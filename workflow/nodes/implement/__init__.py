"""Step 6 — Element-by-element implementation: spec → apply → verify → score → gate."""
from __future__ import annotations

import json

from langgraph.types import interrupt

from ...config import SCORE_PASS_THRESHOLD
from ...session import append_item
from ...state import RiceSessionState
from .spec   import write_spec
from .apply  import apply_element
from .verify import verify_element
from .score  import score_element, format_scorecard


def implement_node(state: RiceSessionState) -> dict:
    """Process one element from element_queue per invocation."""
    queue = state.get("element_queue", [])
    if not queue:
        print("[Step 6] All elements implemented.\n")
        return {"element_queue": [], "current_step": 6}

    element     = queue[0]
    remaining   = queue[1:]
    design      = state.get("design", {})
    session_dir = state.get("session_dir", "")

    print(f"[Step 6] Implementing: {element}", flush=True)

    # 1 — Spec
    spec = write_spec(element, design)
    print(f"  Spec: {json.dumps(spec)}")
    append_item(session_dir, f"{element} spec: {json.dumps(spec)}")

    # 2 — Apply
    apply_result = apply_element(element, design, session_dir)
    print(f"  Apply: {'ok' if apply_result['success'] else 'FAILED — ' + apply_result.get('error', '?')}")

    if not apply_result["success"]:
        record = {"element": element, "spec": spec, "verdict": "SKIP",
                  "reason": apply_result.get("error", "apply failed"), "scorecard": None}
        append_item(session_dir, f"{element}: SKIP — {record['reason']}")
        return {
            "element_queue": remaining,
            "impl_log": [record],
            "errors": [f"{element}: {record['reason']}"],
        }

    # 3 — Verify
    verify_result = verify_element(element, spec, design)
    print(f"  Verify: {verify_result}")

    # 4 — Score
    scorecard = score_element(element, spec, design, verify_result)
    total = scorecard["total"]
    print(f"  Score: {total}/10 ({format_scorecard(scorecard)})")

    # 5 — Gate
    verdict = "verified"
    if total < SCORE_PASS_THRESHOLD:
        decision = interrupt({
            "step": 6, "type": "score_gate", "element": element,
            "score": total, "scorecard": scorecard,
            "message": (
                f"Element '{element}' scored {total}/10 (threshold: {SCORE_PASS_THRESHOLD}).\n"
                f"Breakdown: {format_scorecard(scorecard)}\n\n"
                "Options:\n"
                "  'accept' — accept and continue\n"
                "  'skip'   — skip this element\n"
                "  'retry'  — re-apply with same spec\n"
                "  or describe specific changes"
            ),
        })
        decision_str = str(decision).lower().strip()
        if decision_str == "skip":
            verdict = f"SKIP (score {total}/10, user skipped)"
        elif decision_str == "retry":
            return {"element_queue": [element] + remaining}
        else:
            verdict = f"accepted-deviation (score {total}/10)"

    record = {"element": element, "spec": spec, "scorecard": scorecard, "verdict": verdict}
    append_item(session_dir, f"{element}: {verdict} score={total}/10")
    print(f"  → {verdict}\n")

    return {"element_queue": remaining, "impl_log": [record]}
