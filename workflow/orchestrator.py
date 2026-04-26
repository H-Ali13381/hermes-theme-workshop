"""workflow/orchestrator.py — The actual workflow logic.

Simple procedural code: call each step in order, with if statements for loops.
This is where the business logic lives — easy to read and change.
"""
from __future__ import annotations

from .state import RiceSessionState
from .validators import validator
from .nodes import (
    audit_node, explore_node, refine_node, plan_node,
    baseline_node, install_node, implement_node, cleanup_node, handoff_node,
)


def run_workflow(state: RiceSessionState) -> RiceSessionState:
    """Execute the 8-step rice workflow.

    The pipeline:
    1. audit — scan the machine
    2. explore — loop until direction confirmed
    3. refine — loop until design complete
    4. plan — loop until HTML ready
    4.5. baseline — snapshot current state
    5. install — install packages
    6. implement — loop through elements
    7. cleanup — validate & reload services
    8. handoff — write documentation
    """

    # Step 1 — Audit
    state = audit_node(state)

    # Step 2 — Explore (loop until direction confirmed)
    while True:
        state = explore_node(state)
        if validator.direction_confirmed(state.get("design", {})):
            break

    # Step 3 — Refine (loop until design is complete)
    while True:
        state = refine_node(state)
        ok, reason = validator.design_complete(state.get("design", {}))
        if ok:
            break
        print(f"  design not ready: {reason}")

    # Step 4 — Plan (loop until HTML is ready)
    while True:
        state = plan_node(state)
        ok, reason = validator.plan_ready(state.get("plan_html_path", ""))
        if ok:
            break
        print(f"  plan not ready: {reason}")

    # Step 4.5 — Baseline
    state = baseline_node(state)

    # Step 5 — Install
    state = install_node(state)

    # Step 6 — Implement (loop through element queue)
    while not validator.implement_done(state.get("element_queue", [])):
        state = implement_node(state)

    # Step 7 — Cleanup
    state = cleanup_node(state)

    # Step 8 — Handoff
    state = handoff_node(state)

    return state
