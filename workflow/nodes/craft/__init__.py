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

try:
    from langgraph.types import interrupt
except ImportError:
    interrupt = None  # type: ignore[assignment]

from ...config import SCORE_PASS_THRESHOLD, MAX_IMPLEMENT_RETRIES
from ...logging import get_logger
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


def _score(written: list[str], design: dict) -> int:
    """Simple 0–10 quality score: files exist + contain palette colors."""
    if not written:
        return 0

    palette_colors = list((design.get("palette") or {}).values())
    color_hits = 0

    for path_str in written:
        try:
            content = Path(path_str).read_text(encoding="utf-8", errors="replace").lower()
            for color in palette_colors:
                if isinstance(color, str) and color.lstrip("#").lower() in content:
                    color_hits += 1
                    break
        except OSError:
            pass

    # 5 pts for writing files, up to 5 pts for palette coverage
    file_score    = min(5, len(written) * 2)
    palette_score = min(5, color_hits * 2)
    return file_score + palette_score


def craft_node(state: RiceSessionState) -> dict:
    """Process one craft element per invocation (agentic codegen path)."""
    queue        = state.get("element_queue", [])
    if not queue:
        return {}

    element      = queue[0]
    remaining    = queue[1:]
    design       = state.get("design", {})
    session_dir  = state.get("session_dir", "")
    retry_counts = dict(state.get("impl_retry_counts") or {})
    framework    = element.split(":", 1)[1] if ":" in element else element
    log = get_logger("craft", state)

    log.info("crafting %s via %s", element, framework)

    # ── 1 Research ───────────────────────────────────────────────────────────
    log.info("research phase (parallel subagents)")
    research = gather_research(element, design)
    log.info("found %d existing files", len(research.get("system", {}).get("existing_files", {})))

    # ── 2 Codegen ────────────────────────────────────────────────────────────
    log.info("codegen phase (LLM)")
    files = generate_files(element, design, research)
    log.info("LLM produced %d file(s)", len(files))

    if not files:
        record = {"element": element, "verdict": "SKIP", "reason": "codegen produced no files",
                  "written": [], "score": 0}
        append_item(session_dir, f"{element}: SKIP — codegen failed")
        return {"element_queue": remaining, "craft_log": [record],
                "errors": [f"{element}: codegen produced no files"]}

    # ── 3 Write ──────────────────────────────────────────────────────────────
    written, failed = _write_files(files, framework)
    log.info("wrote %d file(s), %d failed", len(written), len(failed))

    # ── 4 Score ──────────────────────────────────────────────────────────────
    total = _score(written, design)
    log.info("score: %d/10", total)

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
            "  or describe specific changes"
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
