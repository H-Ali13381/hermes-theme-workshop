"""Step 6 — Element-by-element implementation: spec → apply → verify → score → gate."""
from __future__ import annotations

import json

try:
    from langgraph.types import interrupt
except ImportError:  # LangGraph not installed (e.g. during unit tests)
    interrupt = None  # type: ignore[assignment]

from ...config import SCORE_PASS_THRESHOLD, MAX_IMPLEMENT_RETRIES
from ...logging import get_logger
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
        return {}
    element       = queue[0]
    remaining     = queue[1:]
    design        = state.get("design", {})
    session_dir   = state.get("session_dir", "")
    retry_counts  = dict(state.get("impl_retry_counts") or {})
    log = get_logger("implement", state)

    log.info("implementing element: %s", element)

    # 1 — Spec
    spec = write_spec(element, design)
    log.debug("spec: %s", json.dumps(spec))
    append_item(session_dir, f"{element} spec: {json.dumps(spec)}")

    # 2 — Apply
    apply_result = apply_element(element, design, session_dir)
    if apply_result["success"]:
        log.info("apply ok")
    else:
        log.warning("apply failed: %s", apply_result.get("error", "?"))

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
    log.debug("verify: %s", verify_result)

    # 4 — Score
    scorecard = score_element(element, spec, design, verify_result)
    total = scorecard["total"]
    log.info("score: %d/10 (%s)", total, format_scorecard(scorecard))

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
            attempts = retry_counts.get(element, 0) + 1
            if attempts >= MAX_IMPLEMENT_RETRIES:
                verdict = f"SKIP (score {total}/10, max retries {MAX_IMPLEMENT_RETRIES} reached)"
                log.warning("hard skip after %d retries", attempts)
                record = {"element": element, "spec": spec, "scorecard": scorecard, "verdict": verdict}
                append_item(session_dir, f"{element}: {verdict}")
                retry_counts.pop(element, None)
                return {
                    "element_queue": remaining,
                    "impl_log": [record],
                    "impl_retry_counts": retry_counts,
                    "errors": [f"{element}: {verdict}"],
                }
            retry_counts[element] = attempts
            log.info("retry %d/%d", attempts, MAX_IMPLEMENT_RETRIES)
            return {"element_queue": [element] + remaining, "impl_retry_counts": retry_counts}
        else:
            verdict = f"accepted-deviation (score {total}/10)"

    record = {"element": element, "spec": spec, "scorecard": scorecard, "verdict": verdict}
    append_item(session_dir, f"{element}: {verdict} score={total}/10")
    log.info("verdict: %s", verdict)
    retry_counts.pop(element, None)
    return {"element_queue": remaining, "impl_log": [record], "impl_retry_counts": retry_counts}
