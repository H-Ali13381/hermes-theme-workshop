"""workflow/nodes — lazy re-exports.

Importing a specific sub-module (e.g. ``workflow.nodes.cleanup.reloader``)
must not trigger the full LangGraph/typing_extensions dependency chain.
All node symbols are still accessible as ``workflow.nodes.<name>``
via the module-level ``__getattr__`` hook; they are only loaded on first
access rather than eagerly at import time.
"""
from __future__ import annotations

_NODE_MAP: dict[str, tuple[str, str]] = {
    "audit_node":     ("workflow.nodes.audit",     "audit_node"),
    "explore_node":   ("workflow.nodes.explore",   "explore_node"),
    "refine_node":    ("workflow.nodes.refine",    "refine_node"),
    "plan_node":      ("workflow.nodes.plan",      "plan_node"),
    "baseline_node":  ("workflow.nodes.baseline",  "baseline_node"),
    "install_node":   ("workflow.nodes.install",   "install_node"),
    "implement_node": ("workflow.nodes.implement", "implement_node"),
    "craft_node":     ("workflow.nodes.craft",     "craft_node"),
    "cleanup_node":   ("workflow.nodes.cleanup",   "cleanup_node"),
    "handoff_node":   ("workflow.nodes.handoff",   "handoff_node"),
}

__all__ = list(_NODE_MAP)


def __getattr__(name: str):  # noqa: ANN001, ANN202
    if name in _NODE_MAP:
        import importlib
        module_path, attr = _NODE_MAP[name]
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
