"""LangGraph StateGraph definition for the linux-ricing workflow."""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import RiceSessionState
from .config import DESIGN_REQUIRED_KEYS, PALETTE_SLOTS
from .nodes import (
    audit_node, explore_node, refine_node, plan_node,
    baseline_node, install_node, implement_node, cleanup_node, handoff_node,
)


def _route_explore(state: RiceSessionState) -> str:
    """Advance to refine if direction is confirmed, else loop explore."""
    d = state.get("design", {})
    if d.get("stance") or d.get("name_hypothesis"):
        return "refine"
    return "explore"


def _route_after_refine(state: RiceSessionState) -> str:
    """Advance to plan only when design is structurally complete and all hex values valid."""
    d = state.get("design", {})
    if not d:
        return "refine"
    if not all(k in d for k in DESIGN_REQUIRED_KEYS):
        missing = [k for k in DESIGN_REQUIRED_KEYS if k not in d]
        print(f"  [Verifier] design missing keys: {missing} → retrying refine")
        return "refine"
    palette = d.get("palette", {})
    if not all(k in palette for k in PALETTE_SLOTS):
        missing = [k for k in PALETTE_SLOTS if k not in palette]
        print(f"  [Verifier] palette missing slots: {missing} → retrying refine")
        return "refine"
    for slot, val in palette.items():
        if not (isinstance(val, str) and val.startswith("#") and len(val) == 7):
            print(f"  [Verifier] invalid hex for {slot}: {val!r} → retrying refine")
            return "refine"
    return "plan"


def _route_after_plan(state: RiceSessionState) -> str:
    """Advance to baseline only when plan.html exists and has real content (≥ 500 B)."""
    path_str = state.get("plan_html_path", "")
    if not path_str:
        return "plan"
    from pathlib import Path
    p = Path(path_str)
    if not p.exists():
        print(f"  [Verifier] plan.html not found at {p} → retrying plan")
        return "plan"
    if p.stat().st_size < 500:
        print(f"  [Verifier] plan.html too small ({p.stat().st_size}B) → retrying plan")
        return "plan"
    return "baseline"


def _route_implement(state: RiceSessionState) -> str:
    """Loop implement while element_queue is non-empty, then move to cleanup."""
    return "more" if state.get("element_queue") else "cleanup"


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
        _route_after_refine,
        {"plan": "plan", "refine": "refine"},
    )

    # Step 4 → 4.5 (verify HTML exists before capturing baseline)
    builder.add_conditional_edges(
        "plan",
        _route_after_plan,
        {"baseline": "baseline", "plan": "plan"},
    )

    # Step 4.5 → 5 → 6
    builder.add_edge("baseline",  "install")
    builder.add_edge("install",   "implement")

    # Step 6 loops until element_queue is empty
    builder.add_conditional_edges(
        "implement",
        _route_implement,
        {"more": "implement", "cleanup": "cleanup"},
    )

    # Step 7 → 8 → END
    builder.add_edge("cleanup",  "handoff")
    builder.add_edge("handoff",  END)

    return builder.compile(checkpointer=checkpointer)
