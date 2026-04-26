"""workflow/graph.py — LangGraph wiring only.

Registers each step as a node and connects them. No business logic here.
The actual workflow sequence lives in orchestrator.py.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import RiceSessionState
from .orchestrator import run_workflow


def build_graph(checkpointer: SqliteSaver):
    """Compile and return the ricing StateGraph."""
    builder = StateGraph(RiceSessionState)
    builder.add_node("workflow", run_workflow)
    builder.add_edge(START, "workflow")
    builder.add_edge("workflow", END)
    return builder.compile(checkpointer=checkpointer)
