#!/usr/bin/env python3
"""
Entry point for the linux-ricing LangGraph workflow.

Usage:
  python3 workflow/run.py                        # start new session
  python3 workflow/run.py --resume <thread-id>   # resume existing session
  python3 workflow/run.py --list                 # list all sessions
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure SKILL_DIR is importable
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR.parent.parent.parent))  # up to .hermes if needed

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from langchain_core.messages import AIMessage

from workflow.config import DB_PATH, SESSIONS_DIR
from workflow.graph import build_graph
from workflow.state import RiceSessionState


def main() -> None:
    parser = argparse.ArgumentParser(description="Linux Ricing Workflow")
    parser.add_argument("--resume", metavar="THREAD_ID", help="Resume a paused session")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    args = parser.parse_args()

    # Ensure DB directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)

        if args.list:
            _list_sessions(checkpointer)
            return

        if args.resume:
            thread_id = args.resume
            config = {"configurable": {"thread_id": thread_id}}
            print(f"\nResuming session: {thread_id}\n")
            _run_loop(graph, config, initial_input=None)
        else:
            thread_id = _new_thread_id()
            session_dir = _init_session_dir(thread_id)
            config = {"configurable": {"thread_id": thread_id}}
            initial: RiceSessionState = {
                "session_dir": str(session_dir),
                "thread_id": thread_id,
                "current_step": 0,
                "messages": [],
                "element_queue": [],
                "impl_log": [],
                "errors": [],
            }
            print(f"\n{'='*60}")
            print(f"  Linux Ricing Session")
            print(f"  Thread ID: {thread_id}")
            print(f"  Session dir: {session_dir}")
            print(f"  Resume later: python3 workflow/run.py --resume {thread_id}")
            print(f"{'='*60}\n")
            _run_loop(graph, config, initial_input=initial)


def _run_loop(graph, config: dict, initial_input) -> None:
    """Main interactive loop: stream → interrupt → user input → resume."""
    current_input = initial_input

    while True:
        # Stream graph execution
        try:
            for chunk in graph.stream(current_input, config, stream_mode="updates"):
                _print_chunk(chunk)
        except Exception as e:
            if "GraphInterrupt" in type(e).__name__:
                pass  # Expected — handled below via get_state
            elif "StopIteration" in type(e).__name__:
                pass
            else:
                print(f"\n[ERROR] {e}")
                raise

        # Check graph state
        state = graph.get_state(config)

        # No pending nodes → session complete
        if not state.next:
            session_dir = state.values.get("session_dir", "")
            print("\n" + "="*60)
            print("  Session complete!")
            if session_dir:
                print(f"  Handoff: {session_dir}/handoff.md")
                print(f"  Rollback: ricer undo")
            print("="*60 + "\n")
            break

        # Collect pending interrupts
        pending = []
        for task in state.tasks:
            pending.extend(getattr(task, "interrupts", []))

        if not pending:
            # Graph is waiting but no interrupt — pass None to continue
            current_input = None
            continue

        # Display interrupt to user
        interrupt_val = pending[0].value
        _display_interrupt(interrupt_val)

        # Get user response
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession paused. Resume with:")
            thread_id = config["configurable"]["thread_id"]
            print(f"  python3 workflow/run.py --resume {thread_id}\n")
            sys.exit(0)

        current_input = Command(resume=user_input)


def _print_chunk(chunk: dict) -> None:
    """Print relevant output from a graph update chunk."""
    for node_name, node_update in chunk.items():
        if not isinstance(node_update, dict):
            continue

        messages = node_update.get("messages", [])
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.content:
                content = msg.content.strip()
                if content:
                    print(f"\n{content}\n")


def _display_interrupt(val) -> None:
    """Pretty-print an interrupt value."""
    if isinstance(val, dict):
        step = val.get("step", "")
        itype = val.get("type", "")
        message = val.get("message", str(val))

        prefix = f"[Step {step}]" if step else ""
        if itype == "score_gate":
            element = val.get("element", "")
            score = val.get("score", 0)
            print(f"\n{prefix} Score gate — {element}: {score}/10")
        elif itype == "approval":
            print(f"\n{prefix} Approval needed")
        else:
            print(f"\n{prefix}")

        print(message)
    else:
        print(f"\n{val}")

    print()


def _list_sessions(checkpointer) -> None:
    """List all sessions in the checkpoint store."""
    print("\nSessions:\n")
    try:
        configs = list(checkpointer.list({"configurable": {}}))
        if not configs:
            print("  No sessions found.\n")
            return
        for c in configs:
            thread_id = c.config["configurable"].get("thread_id", "?")
            ts = c.metadata.get("created_at", "unknown")
            step = c.metadata.get("step", "?")
            print(f"  {thread_id}  (step {step}, {ts})")
    except Exception as e:
        print(f"  Could not list sessions: {e}\n")
    print()


def _new_thread_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    return f"rice-{ts}-{uuid.uuid4().hex[:6]}"


def _init_session_dir(thread_id: str) -> Path:
    session_dir = SESSIONS_DIR / thread_id
    session_dir.mkdir(parents=True, exist_ok=True)
    # Write session header
    header = f"# Rice Session: {thread_id}\nStarted: {datetime.now().isoformat()}\nStatus: IN PROGRESS — Step 0\n"
    (session_dir / "session.md").write_text(header)
    return session_dir


if __name__ == "__main__":
    main()
