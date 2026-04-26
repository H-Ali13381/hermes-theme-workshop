"""Step 6 — Element-by-element implementation with spec→apply→verify→score→gate cycle."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt

from ..config import MODEL, SCRIPTS_DIR, SCORE_PASS_THRESHOLD
from ..state import RiceSessionState

SPEC_SYSTEM = """\
You are writing an implementation spec for one desktop theming element.
Given the element name and the design_system JSON, produce a concise spec:

targets: list of config file paths that will be written
palette_keys: which design.palette slots are used
font: family and size (if applicable, else "N/A")
radii: border radius in px (if applicable, else "N/A")
notes: any non-obvious detail (e.g. "requires daemon restart")

Output ONLY a JSON object, no explanation.
Example:
{
  "targets": ["~/.config/kitty/theme.conf"],
  "palette_keys": ["background","foreground","primary","accent"],
  "font": "FiraCode Nerd Font 12",
  "radii": "8",
  "notes": "Requires kitty reload (ctrl+shift+F5)"
}
"""

SCORE_CATEGORIES = ["palette", "shape", "diegesis", "usability", "preview_match"]


def implement_node(state: RiceSessionState) -> dict:
    """Process one element from element_queue per invocation."""
    queue = state.get("element_queue", [])

    if not queue:
        print("[Step 6] All elements implemented.\n")
        return {"current_step": 6}

    element = queue[0]
    remaining = queue[1:]
    design = state.get("design", {})
    session_dir = state.get("session_dir", "")

    print(f"[Step 6] Implementing: {element}", flush=True)

    # 1 — Write spec (LLM)
    spec = _write_spec(element, design)
    print(f"  Spec: {json.dumps(spec)}")
    _log_spec(session_dir, element, spec)

    # 2 — Apply via ricer.py
    apply_result = _apply_element(element, design, session_dir)
    print(f"  Apply: {'ok' if apply_result['success'] else 'FAILED — ' + apply_result.get('error','?')}")

    if not apply_result["success"]:
        # Log as SKIP and move on
        record = {
            "element": element,
            "spec": spec,
            "verdict": "SKIP",
            "reason": apply_result.get("error", "apply failed"),
            "scorecard": None,
        }
        _log_item(session_dir, element, record)
        return {
            "element_queue": remaining,
            "current_element": element,
            "impl_log": [record],
            "errors": [f"{element}: {apply_result.get('error', 'apply failed')}"],
        }

    # 3 — Verify (Python checks)
    verify_result = _verify_element(element, spec, design)
    print(f"  Verify: {verify_result}")

    # 4 — Score
    scorecard = _score_element(element, spec, design, verify_result)
    total = scorecard["total"]
    print(f"  Score: {total}/10 ({', '.join(f'{k}={v}' for k,v in scorecard.items() if k != 'total')})")

    # 5 — Gate
    verdict = "verified"
    if total < SCORE_PASS_THRESHOLD:
        decision = interrupt({
            "step": 6,
            "type": "score_gate",
            "element": element,
            "score": total,
            "scorecard": scorecard,
            "message": (
                f"Element '{element}' scored {total}/10 (threshold: {SCORE_PASS_THRESHOLD}).\n"
                f"Breakdown: {_format_scorecard(scorecard)}\n\n"
                "Options:\n"
                "  'accept' — accept this result and continue\n"
                "  'skip'   — skip this element\n"
                "  'retry'  — re-apply with the same spec\n"
                "  or describe specific changes"
            ),
        })

        decision_str = str(decision).lower().strip()
        if decision_str == "skip":
            verdict = f"SKIP (score {total}/10, user skipped)"
        elif decision_str == "retry":
            # Return element to front of queue for re-processing
            return {
                "element_queue": [element] + remaining,
                "current_element": element,
            }
        else:
            verdict = f"accepted-deviation (score {total}/10)"

    record = {
        "element": element,
        "spec": spec,
        "scorecard": scorecard,
        "verdict": verdict,
    }
    _log_item(session_dir, element, record)
    print(f"  → {verdict}\n")

    return {
        "element_queue": remaining,
        "current_element": element,
        "impl_log": [record],
    }


# ── spec ─────────────────────────────────────────────────────────────────────

def _write_spec(element: str, design: dict) -> dict:
    try:
        llm = ChatAnthropic(model=MODEL, temperature=0)
        resp = llm.invoke([
            SystemMessage(content=SPEC_SYSTEM),
            HumanMessage(content=f"Element: {element}\nDesign:\n{json.dumps(design, indent=2)}"),
        ])
        text = resp.content.strip()
        # Strip fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text.strip())
        return json.loads(text)
    except Exception as e:
        return {"targets": [], "palette_keys": [], "font": "N/A", "radii": "N/A", "notes": str(e)}


# ── apply ─────────────────────────────────────────────────────────────────────

def _apply_element(element: str, design: dict, session_dir: str) -> dict:
    """Map element name → ricer.py materializer subcommand."""
    ricer = SCRIPTS_DIR / "ricer.py"
    if not ricer.exists():
        return {"success": False, "error": "ricer.py not found"}

    # Build the ricer apply command for this specific element
    app_name = element.split(":")[0]  # e.g. "terminal" from "terminal:kitty"
    sub_app = element.split(":")[-1] if ":" in element else None

    design_file = Path(session_dir) / "design.json" if session_dir else None
    if not design_file or not design_file.exists():
        # Write a temp design file
        import tempfile, os
        tf = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(design, tf)
        tf.close()
        design_file = Path(tf.name)

    cmd = [sys.executable, str(ricer), "apply", "--design", str(design_file), f"--only={app_name}"]
    if sub_app and sub_app != app_name:
        cmd.append(f"--app={sub_app}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode == 0:
        return {"success": True, "stdout": result.stdout[:500]}
    else:
        return {"success": False, "error": result.stderr[:300] or result.stdout[:300]}


# ── verify ────────────────────────────────────────────────────────────────────

def _verify_element(element: str, spec: dict, design: dict) -> dict:
    """Python checks: did target files change? Are they valid?"""
    result = {"files_written": [], "files_missing": []}
    for target in spec.get("targets", []):
        path = Path(target).expanduser()
        if path.exists():
            result["files_written"].append(str(path))
        else:
            result["files_missing"].append(str(path))

    # Check palette slots are referenced in written files
    palette_match = True
    for written in result["files_written"]:
        try:
            content = Path(written).read_text(errors="ignore")
            for key in spec.get("palette_keys", []):
                color = design.get("palette", {}).get(key, "")
                if color and color.lower() not in content.lower():
                    palette_match = False
                    break
        except Exception:
            pass

    result["palette_match"] = palette_match
    return result


# ── score ─────────────────────────────────────────────────────────────────────

def _score_element(element: str, spec: dict, design: dict, verify: dict) -> dict:
    """Compute 5-category scorecard (0-2 each, max 10)."""
    sc = {}

    # palette (0-2): all target palette slots present in files
    files_written = len(verify.get("files_written", []))
    files_missing = len(verify.get("files_missing", []))
    if files_written == 0:
        sc["palette"] = 0
    elif verify.get("palette_match"):
        sc["palette"] = 2
    else:
        sc["palette"] = 1

    # shape (0-2): files exist and are non-trivially sized
    if files_missing > 0 and files_written == 0:
        sc["shape"] = 0
    elif files_written > 0:
        all_ok = all(
            Path(f).expanduser().stat().st_size > 20
            for f in verify.get("files_written", [])
            if Path(f).expanduser().exists()
        )
        sc["shape"] = 2 if all_ok else 1
    else:
        sc["shape"] = 1

    # diegesis (0-2): does the element fit the design stance? (heuristic)
    sc["diegesis"] = 2 if files_written > 0 else 0

    # usability (0-2): no syntax errors detected
    syntax_ok = _check_syntax(verify.get("files_written", []))
    sc["usability"] = 2 if syntax_ok else 1

    # preview_match (0-2): were the correct palette keys used?
    sc["preview_match"] = 2 if verify.get("palette_match") and files_written > 0 else 1

    sc["total"] = sum(v for k, v in sc.items() if k != "total")
    return sc


def _check_syntax(files: list[str]) -> bool:
    for f in files:
        p = Path(f).expanduser()
        if not p.exists():
            continue
        if p.suffix in (".json", ".jsonc"):
            try:
                content = p.read_text()
                # Remove // comments for jsonc
                content = re.sub(r"//.*", "", content)
                json.loads(content)
            except Exception:
                return False
        # .toml, .ini, .conf: basic non-empty check
    return True


def _format_scorecard(sc: dict) -> str:
    return " ".join(f"{k}={v}" for k, v in sc.items() if k != "total")


# ── session logging ────────────────────────────────────────────────────────────

def _log_spec(session_dir: str, element: str, spec: dict) -> None:
    if not session_dir:
        return
    try:
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "session_manager.py"),
             "append-item", element, json.dumps(spec), "--session-dir", session_dir],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass


def _log_item(session_dir: str, element: str, record: dict) -> None:
    if not session_dir:
        return
    try:
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "session_manager.py"),
             "append-item", element, json.dumps(record), "--session-dir", session_dir],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass
