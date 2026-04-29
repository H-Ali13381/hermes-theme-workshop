"""workflow/routing.py — Conditional routing functions for the rice pipeline.

Each function receives the current LangGraph state dict and returns the name
of the next node (or END) that the graph should route to.

Keeping routing logic here means graph.py only describes *structure*, not
decision logic, making both files easier to read in isolation.
"""
from __future__ import annotations

import sys

from langgraph.graph import END

from .config import MAX_LOOP_ITERATIONS
from . import validators


def _loop_limit_reached(state: dict, node: str, label: str) -> bool:
    """Return True (and print a warning) if node has hit MAX_LOOP_ITERATIONS."""
    count = state.get("loop_counts", {}).get(node, 0)
    if count >= MAX_LOOP_ITERATIONS:
        print(
            f"[{label}] ABORT — reached {count}/{MAX_LOOP_ITERATIONS} iterations "
            "without making progress. Check LLM response format.",
            file=sys.stderr,
        )
        return True
    return False


def after_audit(state: dict) -> str:
    """Route after the audit node.

    If the desktop is unsupported (e.g. i3, xfce) return END immediately so
    the workflow exits cleanly without attempting to apply any themes.
    """
    recipe = state.get("device_profile", {}).get("desktop_recipe")
    return END if recipe == "other" else "explore"


def after_explore(state: dict) -> str:
    """Loop until creative direction is confirmed; abort if loop limit is hit."""
    if _loop_limit_reached(state, "explore", "Explore"):
        return END
    return "refine" if validators.direction_confirmed(state.get("design", {})) else "explore"


def after_refine(state: dict) -> str:
    """Loop until design JSON is schema-valid; abort if loop limit is hit."""
    if _loop_limit_reached(state, "refine", "Refine"):
        return END
    ok, _ = validators.design_complete(state.get("design", {}), state.get("device_profile", {}))
    return "plan" if ok else "refine"


def after_plan(state: dict) -> str:
    """Loop until HTML mockup is present and valid; abort if loop limit is hit."""
    if _loop_limit_reached(state, "plan", "Plan"):
        return END
    ok, _ = validators.plan_ready(state.get("plan_html_path", ""))
    return "baseline" if ok else "plan"


def after_implement(state: dict) -> str:
    """Route after the implement node.

    Loop back to implement while there are still pending elements in the
    queue; proceed to cleanup when the queue is empty.
    """
    return "cleanup" if validators.implement_done(state.get("element_queue", [])) else "implement"
