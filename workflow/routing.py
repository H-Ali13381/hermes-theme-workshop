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
from .validators import validator


def after_audit(state: dict) -> str:
    """Route after the audit node.

    If the desktop is unsupported (e.g. i3, xfce) return END immediately so
    the workflow exits cleanly without attempting to apply any themes.
    """
    recipe = state.get("device_profile", {}).get("desktop_recipe")
    return END if recipe == "other" else "explore"


def after_explore(state: dict) -> str:
    """Route after the explore node.

    Loop back to explore until the creative direction has been confirmed;
    proceed to refine once it is.

    Safety guard: if the node has been invoked more than MAX_LOOP_ITERATIONS
    times without confirming a direction (e.g. the LLM emits the sentinel
    repeatedly but JSON parsing fails every time), abort to END rather than
    spinning forever.
    """
    count = state.get("loop_counts", {}).get("explore", 0)
    if count >= MAX_LOOP_ITERATIONS:
        print(
            f"[Explore] ABORT — reached {count}/{MAX_LOOP_ITERATIONS} iterations "
            "without confirming a direction. Check LLM response format.",
            file=sys.stderr,
        )
        return END
    return "refine" if validator.direction_confirmed(state.get("design", {})) else "explore"


def after_refine(state: dict) -> str:
    """Route after the refine node.

    Loop back to refine until the design JSON is schema-valid and complete;
    proceed to plan once it passes validation.

    Safety guard: abort to END after MAX_LOOP_ITERATIONS invocations.
    """
    count = state.get("loop_counts", {}).get("refine", 0)
    if count >= MAX_LOOP_ITERATIONS:
        print(
            f"[Refine] ABORT — reached {count}/{MAX_LOOP_ITERATIONS} iterations "
            "without producing a valid design. Check LLM response format.",
            file=sys.stderr,
        )
        return END
    ok, _ = validator.design_complete(state.get("design", {}), state.get("device_profile", {}))
    return "plan" if ok else "refine"


def after_plan(state: dict) -> str:
    """Route after the plan node.

    Loop back to plan until the HTML mockup file is present and valid;
    proceed to baseline once it is ready.

    Safety guard: abort to END after MAX_LOOP_ITERATIONS invocations.
    """
    count = state.get("loop_counts", {}).get("plan", 0)
    if count >= MAX_LOOP_ITERATIONS:
        print(
            f"[Plan] ABORT — reached {count}/{MAX_LOOP_ITERATIONS} iterations "
            "without an approved HTML preview. Check LLM response format.",
            file=sys.stderr,
        )
        return END
    ok, _ = validator.plan_ready(state.get("plan_html_path", ""))
    return "baseline" if ok else "plan"


def after_implement(state: dict) -> str:
    """Route after the implement node.

    Loop back to implement while there are still pending elements in the
    queue; proceed to cleanup when the queue is empty.
    """
    return "cleanup" if validator.implement_done(state.get("element_queue", [])) else "implement"
