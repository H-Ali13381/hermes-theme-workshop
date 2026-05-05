"""workflow/routing.py — Conditional routing functions for the rice pipeline.

Each function receives the current LangGraph state dict and returns the name
of the next node (or END) that the graph should route to.

Keeping routing logic here means graph.py only describes *structure*, not
decision logic, making both files easier to read in isolation.
"""
from __future__ import annotations

from langgraph.graph import END

from .config import MAX_LOOP_ITERATIONS
from .log_setup import get_logger
from . import validators


def _loop_limit_reached(state: dict, node: str, label: str) -> bool:
    """Return True (and log a warning) if node has hit MAX_LOOP_ITERATIONS."""
    count = state.get("loop_counts", {}).get(node, 0)
    if count >= MAX_LOOP_ITERATIONS:
        get_logger("routing", state).warning(
            "%s ABORT — reached %d/%d iterations without making progress. "
            "Check LLM response format.",
            label, count, MAX_LOOP_ITERATIONS,
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
    """Loop until creative direction is confirmed; then hand off to visualize."""
    if _loop_limit_reached(state, "explore", "Explore"):
        return END
    return "visualize" if validators.direction_confirmed(state.get("design", {})) else "explore"


def after_visualize(state: dict) -> str:
    """Dispatch on the visualize-feedback signal set by visualize_node.

    Routes:
      - "approve"    → refine (visual locked in; carry visual_context forward)
      - "skip"       → refine (FAL unavailable or generation failed; proceed without)
      - "regenerate" → visualize (loop: generate a new style image)
      - "explore"    → explore (user wants to revise the creative direction)
      - unset        → refine if visual_context is populated, else visualize
    """
    if _loop_limit_reached(state, "visualize", "Visualize"):
        return END

    route = (state.get("visualize_route") or "").strip().lower()
    if route in ("approve", "skip"):
        return "refine"
    if route == "regenerate":
        return "visualize"
    if route == "explore":
        return "explore"

    # Fallback: visual_context populated means we can proceed
    return "refine" if state.get("visual_context") else "visualize"


def after_refine(state: dict) -> str:
    """Loop until design JSON is schema-valid; abort if loop limit is hit."""
    if _loop_limit_reached(state, "refine", "Refine"):
        return END
    ok, _ = validators.design_complete(state.get("design", {}), state.get("device_profile", {}))
    return "plan" if ok else "refine"


def after_plan(state: dict) -> str:
    """Dispatch on the plan-feedback classifier signal set by plan_node.

    Routes:
      - "approve"  → baseline (forward through pipeline)
      - "refine"   → refine (design.json needs changes)
      - "explore"  → explore (creative direction needs revision)
      - "render"   → plan (re-render with same design.json)
      - unset      → fall back to validator-based check (back-compat for first
                     pass before plan_node has run, and for older state shapes)
    Loop limit is checked last so the destination node still gets a fair shot
    even when the signal asks for a backward jump.
    """
    if _loop_limit_reached(state, "plan", "Plan"):
        return END

    route = (state.get("plan_feedback_route") or "").strip().lower()
    if route == "approve":
        return "baseline"
    if route == "refine":
        return "refine"
    if route == "explore":
        return "explore"
    if route == "render":
        return "plan"

    # No explicit route yet — defer to validator (e.g. state was just primed
    # without a feedback turn).
    ok, _ = validators.plan_ready(state.get("plan_html_path", ""))
    return "baseline" if ok else "plan"


def _next_node_for_queue(state: dict) -> str:
    """Given a non-empty element queue, return the right processing node."""
    queue = state.get("element_queue", [])
    if not queue:
        return "cleanup"
    return "craft" if validators.is_craft_element(queue[0]) else "implement"


def after_install(state: dict) -> str:
    """Route after the install node.

    The first queued element may be a craft element (eww/quickshell/conky
    widgets, waybar) — in that case we must enter craft_node directly,
    bypassing implement_node which has no codegen path. An unconditional
    install→implement edge would hand the craft element to the materializer
    and skip the agentic build entirely.
    """
    if validators.implement_done(state.get("element_queue", [])):
        return "cleanup"
    return _next_node_for_queue(state)


def after_implement(state: dict) -> str:
    """Route after the implement node.

    Loop back to implement (or craft) while there are still pending elements;
    proceed to cleanup when the queue is empty.
    """
    if validators.implement_done(state.get("element_queue", [])):
        return "cleanup"
    return _next_node_for_queue(state)


def after_craft(state: dict) -> str:
    """Route after the craft node — mirrors after_implement."""
    if validators.implement_done(state.get("element_queue", [])):
        return "cleanup"
    return _next_node_for_queue(state)
