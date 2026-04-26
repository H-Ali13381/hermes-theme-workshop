"""Route after implement_node: loop if queue has items, else move to cleanup."""
from __future__ import annotations

from ..state import RiceSessionState


def route_implement(state: RiceSessionState) -> str:
    queue = state.get("element_queue", [])
    if queue:
        return "more"
    return "cleanup"
