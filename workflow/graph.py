"""workflow/graph.py — Workflow definition: steps, sequence, and routing.

Read this file to understand the full pipeline at a glance.
Node implementations live in workflow/nodes/.
Routing (conditional edge) functions live in workflow/routing.py.
Gate logic (validators) lives in workflow/validators.py.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import RiceSessionState
from .nodes import (
    audit_node, explore_node, visualize_node, refine_node, plan_node,
    baseline_node, install_node, implement_node, cleanup_node, handoff_node,
    craft_node,
)
from .routing import (
    after_audit, after_explore, after_visualize, after_refine, after_plan,
    after_install, after_implement, after_craft,
)


def build_graph(checkpointer: SqliteSaver):
    """Compile and return the LangGraph StateGraph with checkpointing enabled."""
    builder = StateGraph(RiceSessionState)

    # ── Step 1 — Silent machine audit (no LLM) ──────────────────────────────
    builder.add_node("audit",     audit_node)

    # ── Step 2 — Creative direction (loop until stance confirmed) ────────────
    builder.add_node("explore",    explore_node)

    # ── Step 2.5 — AI full-desktop concept preview (FAL + multimodal) ────────
    builder.add_node("visualize",  visualize_node)

    # ── Step 3 — Design JSON (loop until schema valid) ───────────────────────
    builder.add_node("refine",     refine_node)

    # ── Step 4 — HTML mockup (loop until file ready) ─────────────────────────
    builder.add_node("plan",      plan_node)

    # ── Step 4.5 — Immutable rollback baseline ───────────────────────────────
    builder.add_node("baseline",  baseline_node)

    # ── Step 5 — Package installation ────────────────────────────────────────
    builder.add_node("install",   install_node)

    # ── Step 6 — Per-element implementation (one element per invocation) ─────
    builder.add_node("implement", implement_node)

    # ── Step 6/craft — Agentic implementation for advanced elements ──────────
    builder.add_node("craft",     craft_node)

    # ── Step 7 — Validate & reload desktop services ──────────────────────────
    builder.add_node("cleanup",   cleanup_node)

    # ── Step 8 — Write session documentation ─────────────────────────────────
    builder.add_node("handoff",   handoff_node)

    # ── Edges & conditional routing (logic lives in routing.py) ─────────────
    builder.add_edge(START, "audit")
    builder.add_conditional_edges("audit",      after_audit)
    builder.add_conditional_edges("explore",    after_explore)
    builder.add_conditional_edges("visualize",  after_visualize)
    builder.add_conditional_edges("refine",     after_refine)
    builder.add_conditional_edges("plan",      after_plan)
    builder.add_edge("baseline", "install")
    builder.add_conditional_edges("install",   after_install)
    builder.add_conditional_edges("implement", after_implement)
    builder.add_conditional_edges("craft",     after_craft)
    builder.add_edge("cleanup",  "handoff")
    builder.add_edge("handoff",  END)

    return builder.compile(checkpointer=checkpointer)
