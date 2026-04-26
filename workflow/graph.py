"""LangGraph StateGraph definition for the linux-ricing workflow."""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import RiceSessionState
from .nodes import (
    audit_node, explore_node, refine_node, plan_node,
    baseline_node, install_node, implement_node, cleanup_node, handoff_node,
)
from .verifiers import route_after_refine, route_after_plan, route_implement


def build_graph(checkpointer: SqliteSaver):
    """Compile and return the ricing StateGraph."""
    builder = StateGraph(RiceSessionState)

    # Register nodes
    builder.add_node("audit",     audit_node)
    builder.add_node("explore",   explore_node)
    builder.add_node("refine",    refine_node)
    builder.add_node("plan",      plan_node)
    builder.add_node("baseline",  baseline_node)
    builder.add_node("install",   install_node)
    builder.add_node("implement", implement_node)
    builder.add_node("cleanup",   cleanup_node)
    builder.add_node("handoff",   handoff_node)

    # ── Edges ────────────────────────────────────────────────────────────────

    # Step 1 → 2 (no gate needed — audit is pure Python)
    builder.add_edge(START,      "audit")
    builder.add_edge("audit",    "explore")

    # Step 2 → 3 (explore loops back to itself via routing)
    builder.add_conditional_edges(
        "explore",
        _route_explore,
        {"refine": "refine", "explore": "explore"},
    )

    # Step 3 → 4 (verify design completeness before showing preview)
    builder.add_conditional_edges(
        "refine",
        route_after_refine,
        {"plan": "plan", "refine": "refine"},
    )

    # Step 4 → 4.5 (verify HTML exists before capturing baseline)
    builder.add_conditional_edges(
        "plan",
        route_after_plan,
        {"baseline": "baseline", "plan": "plan"},
    )

    # Step 4.5 → 5 → 6
    builder.add_edge("baseline",  "install")
    builder.add_edge("install",   "implement")

    # Step 6 loops until element_queue is empty
    builder.add_conditional_edges(
        "implement",
        route_implement,
        {"more": "implement", "cleanup": "cleanup"},
    )

    # Step 7 → 8 → END
    builder.add_edge("cleanup",  "handoff")
    builder.add_edge("handoff",  END)

    return builder.compile(checkpointer=checkpointer)


def _route_explore(state: RiceSessionState) -> str:
    """Advance to refine if direction is confirmed, else loop explore."""
    d = state.get("design", {})
    # direction is confirmed when design has stance/mood keys (set by explore_node)
    if d.get("stance") or d.get("name_hypothesis"):
        return "refine"
    return "explore"
