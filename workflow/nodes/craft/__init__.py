"""Step 6/craft — Agentic implementation for advanced desktop elements.

Unlike implement_node (which calls fixed materializers), craft_node runs an
open loop:
  1. Research  — parallel subagents gather framework syntax + system state
  2. Codegen   — LLM writes complete, original config files from scratch
  3. Write     — files are placed in the framework's config directory
  4. Score     — heuristic quality gate (files written, palette present)
  5. Gate      — user interrupt when score is below threshold

One element is processed per invocation; routing loops craft_node or hands
off to implement/cleanup depending on what's next in the queue.
"""
from __future__ import annotations

from pathlib import Path
import shutil

try:
    from langgraph.types import interrupt
except ImportError:
    interrupt = None  # type: ignore[assignment]

from ...config import SCORE_PASS_THRESHOLD, MAX_IMPLEMENT_RETRIES
from ...log_setup import get_logger
from ...session import append_item
from ...state import RiceSessionState
from .frameworks import get_reference, config_dir
from .research import gather_research
from .codegen import generate_files


def _write_files(files: list[dict], framework: str) -> tuple[list[str], list[str]]:
    """Write generated files into the framework's config dir.

    Returns (written_paths, failed_paths).
    """
    cd = config_dir(framework)
    if cd is None:
        ref = get_reference(framework)
        raw = ref.get("config_dir", "")
        cd = Path(raw).expanduser() if raw else Path.home() / ".config" / framework

    cd.mkdir(parents=True, exist_ok=True)
    written, failed = [], []

    for obj in files:
        rel  = obj.get("path", "")
        text = obj.get("content", "")
        if not rel or not text:
            continue
        target = (cd / rel).resolve()
        # Safety: never escape the config dir
        try:
            target.relative_to(cd.resolve())
        except ValueError:
            get_logger("craft").warning("SKIP unsafe path: %s", target)
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            written.append(str(target))
        except OSError as exc:
            get_logger("craft").warning("write error %s: %s", target, exc)
            failed.append(str(target))

    return written, failed


def _copy_texture_assets(research: dict, dest_dir: Path) -> list[str]:
    """Copy generated texture assets into a framework config dir."""

    texture_assets = research.get("texture_assets") if isinstance(research, dict) else None
    if not isinstance(texture_assets, dict):
        return []
    root = Path(str(texture_assets.get("root") or ""))
    if not root:
        return []
    copied: list[str] = []
    for asset in texture_assets.get("assets", []):
        if not isinstance(asset, dict):
            continue
        rel = Path(str(asset.get("path", "")))
        if not str(rel) or rel.is_absolute() or ".." in rel.parts:
            get_logger("craft").warning("SKIP unsafe texture asset path: %s", rel)
            continue
        src = root / rel
        if not src.exists():
            # Metadata may point root at assets/<theme>; tolerate that shape too.
            src = root / rel.name
        if not src.exists():
            get_logger("craft").warning("SKIP missing texture asset: %s", rel)
            continue
        target = (dest_dir / rel).resolve()
        try:
            target.relative_to(dest_dir.resolve())
        except ValueError:
            get_logger("craft").warning("SKIP unsafe texture target: %s", target)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        copied.append(str(target))
    return copied


def _score_details(written: list[str], design: dict, required_files: list[str] | None = None) -> dict:
    """Return craft score details for a generated file set.

    Score the file set as a unit.  Frameworks such as EWW intentionally split
    structure (``eww.yuck``) from palette styling (``eww.scss``), so requiring
    every individual file to contain literal palette values creates false low
    scores for correct output.
    """
    if not written:
        return {"total": 0, "file_score": 0, "palette_score": 0,
                "required_present": 0, "required_total": len(required_files or []),
                "palette_hits": 0, "palette_total": 0}

    written_names = {Path(path_str).name for path_str in written}
    required = [str(name).strip() for name in (required_files or []) if str(name).strip()]
    if required:
        present = sum(1 for name in required if name in written_names)
        file_score = round((present / len(required)) * 5)
    else:
        present = len(written)
        file_score = 5

    blob_parts = []
    for path_str in written:
        try:
            blob_parts.append(Path(path_str).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    blob = "\n".join(blob_parts).lower()

    palette_colors = [
        str(color).lower()
        for color in (design.get("palette") or {}).values()
        if isinstance(color, str) and color.startswith("#")
    ]
    palette_hits = sum(
        1 for color in palette_colors
        if color.lower() in blob or color.lstrip("#").lower() in blob
    )
    if palette_colors:
        palette_score = round((palette_hits / len(palette_colors)) * 5)
    else:
        palette_score = 5

    total = max(0, min(10, file_score + palette_score))
    return {"total": total, "file_score": file_score, "palette_score": palette_score,
            "required_present": present, "required_total": len(required),
            "palette_hits": palette_hits, "palette_total": len(palette_colors)}


def _score(written: list[str], design: dict, required_files: list[str] | None = None) -> int:
    """0–10 quality score: required files written + palette coverage across file set."""
    return int(_score_details(written, design, required_files)["total"])


def _design_requires_eww(design: dict) -> bool:
    """Return True only when EWW is explicitly required, not merely a fallback."""
    if not isinstance(design, dict):
        return False
    chrome = design.get("chrome_strategy", {})
    return bool(
        design.get("eww_required")
        or (isinstance(chrome, dict) and chrome.get("eww_required"))
    )


def _crafted_successfully(state: RiceSessionState, element: str) -> bool:
    """Whether a prior craft log entry already produced a passing element."""
    for record in state.get("craft_log", []) or []:
        if not isinstance(record, dict) or record.get("element") != element:
            continue
        verdict = str(record.get("verdict", "")).lower()
        if "skip" not in verdict and int(record.get("score") or 0) >= SCORE_PASS_THRESHOLD:
            return True
    return False


def _skip_redundant_eww_fallback(state: RiceSessionState, element: str, remaining: list[str]) -> dict | None:
    """Skip EWW fallback when Quickshell has already satisfied KDE Wayland widgets."""
    if element != "widgets:eww":
        return None
    design = state.get("design", {})
    if _design_requires_eww(design):
        return None
    profile = state.get("device_profile", {}) or {}
    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "").lower()
    session = str(profile.get("session_type") or "").lower()
    kde_wayland = ("kde" in wm or "plasma" in wm) and session == "wayland"
    targets = ""
    chrome = design.get("chrome_strategy", {}) if isinstance(design, dict) else {}
    if isinstance(chrome, dict):
        targets = " ".join(str(t).lower() for t in chrome.get("implementation_targets", []))
    if not kde_wayland and "widgets:quickshell" not in targets:
        return None
    if not _crafted_successfully(state, "widgets:quickshell"):
        return None
    record = {
        "element": element,
        "verdict": "SKIP (redundant fallback; widgets:quickshell already crafted)",
        "reason": "EWW is only a fallback for this design; Quickshell is the approved KDE Wayland widget framework.",
        "written": [],
        "score": SCORE_PASS_THRESHOLD,
    }
    retry_counts = dict(state.get("impl_retry_counts") or {})
    retry_counts.pop(element, None)
    append_item(state.get("session_dir", ""), f"{element}: {record['verdict']}")
    return {"element_queue": remaining, "craft_log": [record], "impl_retry_counts": retry_counts}


def craft_node(state: RiceSessionState) -> dict:
    """Process one craft element per invocation (agentic codegen path)."""
    queue        = state.get("element_queue", [])
    if not queue:
        return {}

    element      = queue[0]
    remaining    = queue[1:]
    fallback_skip = _skip_redundant_eww_fallback(state, element, remaining)
    if fallback_skip is not None:
        return fallback_skip
    design       = state.get("design", {})
    session_dir  = state.get("session_dir", "")
    retry_counts = dict(state.get("impl_retry_counts") or {})
    framework    = element.split(":", 1)[1] if ":" in element else element
    log = get_logger("craft", state)

    log.info("crafting %s via %s", element, framework)

    # ── 1 Research ───────────────────────────────────────────────────────────
    log.info("research phase (parallel subagents)")
    research = gather_research(element, design)
    research["device_profile"] = dict(state.get("device_profile") or {})
    research["session_dir"] = session_dir
    log.info("found %d existing files", len(research.get("system", {}).get("existing_files", {})))

    # ── 2 Codegen ────────────────────────────────────────────────────────────
    log.info("codegen phase (LLM)")
    files = generate_files(element, design, research)
    log.info("LLM produced %d file(s)", len(files))

    if not files:
        attempts = retry_counts.get(element, 0) + 1
        log.warning("codegen produced no files (attempt %d/%d)",
                    attempts, MAX_IMPLEMENT_RETRIES)
        if attempts < MAX_IMPLEMENT_RETRIES:
            retry_counts[element] = attempts
            append_item(session_dir,
                        f"{element}: codegen failed (0 files), retry {attempts}/{MAX_IMPLEMENT_RETRIES}")
            return {"element_queue": [element] + remaining,
                    "impl_retry_counts": retry_counts}
        record = {"element": element, "verdict": "SKIP",
                  "reason": f"codegen produced no files after {attempts} attempts",
                  "written": [], "score": 0}
        retry_counts.pop(element, None)
        append_item(session_dir, f"{element}: SKIP — codegen failed after {attempts} attempts")
        return {"element_queue": remaining, "craft_log": [record],
                "impl_retry_counts": retry_counts,
                "errors": [f"{element}: codegen produced no files"]}

    # ── 3 Write ──────────────────────────────────────────────────────────────
    written, failed = _write_files(files, framework)
    cd = config_dir(framework)
    if cd is None:
        ref = get_reference(framework)
        raw = ref.get("config_dir", "")
        cd = Path(raw).expanduser() if raw else Path.home() / ".config" / framework
    copied_assets = _copy_texture_assets(research, cd)
    written.extend(copied_assets)
    log.info("wrote %d file(s), copied %d texture asset(s), %d failed", len(written), len(copied_assets), len(failed))

    # ── 4 Score ──────────────────────────────────────────────────────────────
    required_files = research.get("syntax", {}).get("key_files", []) if isinstance(research, dict) else []
    score = _score_details(written, design, required_files)
    total = int(score["total"])
    log.info("score: %d/10 file_score=%d palette_score=%d required=%d/%d palette_hits=%d/%d",
             total, score["file_score"], score["palette_score"],
             score["required_present"], score["required_total"],
             score["palette_hits"], score["palette_total"])

    # ── 5 Gate ───────────────────────────────────────────────────────────────
    verdict = "crafted"
    if total < SCORE_PASS_THRESHOLD:
        msg = (
            f"Craft element '{element}' scored {total}/10 (threshold: {SCORE_PASS_THRESHOLD}).\n"
            f"Files written: {written}\n"
            f"Files failed:  {failed}\n\n"
            "Options:\n"
            "  'accept' — accept and continue\n"
            "  'skip'   — skip this element\n"
            "  'retry'  — regenerate from scratch\n"
            "Anything else is treated as 'accept'."
        )
        if interrupt is not None:
            decision = interrupt({"step": 6, "type": "craft_gate", "element": element,
                                  "score": total, "message": msg})
            decision_str = str(decision).lower().strip()
        else:
            decision_str = "accept"

        if decision_str == "skip":
            verdict = f"SKIP (score {total}/10, user skipped)"
        elif decision_str == "retry":
            attempts = retry_counts.get(element, 0) + 1
            if attempts >= MAX_IMPLEMENT_RETRIES:
                verdict = f"SKIP (score {total}/10, max retries reached)"
                retry_counts.pop(element, None)
                record = {"element": element, "verdict": verdict, "written": written, "score": total}
                append_item(session_dir, f"{element}: {verdict}")
                return {"element_queue": remaining, "craft_log": [record],
                        "impl_retry_counts": retry_counts,
                        "errors": [f"{element}: {verdict}"]}
            retry_counts[element] = attempts
            log.info("retry %d/%d", attempts, MAX_IMPLEMENT_RETRIES)
            return {"element_queue": [element] + remaining, "impl_retry_counts": retry_counts}
        else:
            verdict = f"accepted-deviation (score {total}/10)"

    record = {"element": element, "verdict": verdict, "written": written,
              "failed": failed, "score": total}
    append_item(session_dir, f"{element}: {verdict} score={total}/10")
    log.info("verdict: %s", verdict)
    retry_counts.pop(element, None)
    return {"element_queue": remaining, "craft_log": [record], "impl_retry_counts": retry_counts}
