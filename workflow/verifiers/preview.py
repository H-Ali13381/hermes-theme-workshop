"""Verify plan.html was written and has real content after plan_node."""
from __future__ import annotations

from pathlib import Path

from ..state import RiceSessionState

MIN_HTML_BYTES = 500


def route_after_plan(state: RiceSessionState) -> str:
    """Return 'baseline' if preview is ready, else 'plan' to retry."""
    path_str = state.get("plan_html_path", "")

    if not path_str:
        return "plan"

    p = Path(path_str)
    if not p.exists():
        print(f"  [Verifier] plan.html not found at {p} → retrying plan")
        return "plan"

    if p.stat().st_size < MIN_HTML_BYTES:
        print(f"  [Verifier] plan.html too small ({p.stat().st_size}B) → retrying plan")
        return "plan"

    return "baseline"
