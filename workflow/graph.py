"""workflow/graph.py — Workflow definition: steps, sequence, and routing.

Read this file to understand the full pipeline.
Node implementations live in workflow/nodes/; gate logic lives in validators.py.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import RiceSessionState
from .validators import validator
from .nodes import (
    audit_node, explore_node, refine_node, plan_node,
    baseline_node, install_node, implement_node, cleanup_node, handoff_node,
)


def build_graph(checkpointer: SqliteSaver):
    builder = StateGraph(RiceSessionState)

    # ── Step 1 — Silent machine audit (no LLM) ──────────────────────────────
    builder.add_node("audit", audit_node)

    # ── Step 2 — Creative direction (loop until stance confirmed) ────────────
    builder.add_node("explore", explore_node)

    # ── Step 3 — Design JSON (loop until schema valid) ───────────────────────
    builder.add_node("refine", refine_node)

    # ── Step 4 — HTML mockup (loop until file ready) ─────────────────────────
    builder.add_node("plan", plan_node)

    # ── Step 4.5 — Immutable rollback baseline ───────────────────────────────
    builder.add_node("baseline", baseline_node)

    # ── Step 5 — Package installation ────────────────────────────────────────
    builder.add_node("install", install_node)

    # ── Step 6 — Per-element implementation (one element per invocation) ─────
    builder.add_node("implement", implement_node)

    # ── Step 7 — Validate & reload desktop services ──────────────────────────
    builder.add_node("cleanup", cleanup_node)

    # ── Step 8 — Write session documentation ─────────────────────────────────
    builder.add_node("handoff", handoff_node)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    builder.add_edge(START, "audit")

    def _after_audit(state):
        # Stop immediately for unsupported desktops (i3, xfce, etc.)
        return END if state.get("device_profile", {}).get("desktop_recipe") == "other" else "explore"

    def _after_explore(state):
        return "refine" if validator.direction_confirmed(state.get("design", {})) else "explore"

    def _after_refine(state):
        ok, _ = validator.design_complete(state.get("design", {}), state.get("device_profile", {}))
        return "plan" if ok else "refine"

    def _after_plan(state):
        ok, _ = validator.plan_ready(state.get("plan_html_path", ""))
        return "baseline" if ok else "plan"

    def _after_implement(state):
        return "cleanup" if validator.implement_done(state.get("element_queue", [])) else "implement"

    builder.add_conditional_edges("audit",     _after_audit)
    builder.add_conditional_edges("explore",   _after_explore)
    builder.add_conditional_edges("refine",    _after_refine)
    builder.add_conditional_edges("plan",      _after_plan)
    builder.add_edge("baseline", "install")
    builder.add_edge("install",  "implement")
    builder.add_conditional_edges("implement", _after_implement)
    builder.add_edge("cleanup",  "handoff")
    builder.add_edge("handoff",  END)

    return builder.compile(checkpointer=checkpointer)
