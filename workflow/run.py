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
import traceback
import uuid
from datetime import datetime
from pathlib import Path

# Ensure SKILL_DIR is importable
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import GraphInterrupt
from langgraph.types import Command
from langchain_core.messages import AIMessage

from workflow.config import DB_PATH, SESSIONS_DIR, SCRIPTS_DIR
from workflow.graph import build_graph
from workflow.state import RiceSessionState

# Ensure scripts/ is importable for session_io helpers.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from core.session_io import SESSION_HEADER_TEMPLATE, set_current  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Linux Ricing Workflow")
    parser.add_argument("--resume", metavar="THREAD_ID", help="Resume a paused session")
    parser.add_argument("--list", action="store_true", help="List all sessions")
    parser.add_argument("--json", action="store_true", help="Output --list results as a JSON array")
    args = parser.parse_args()

    # Ensure DB directory exists
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

    with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
        graph = build_graph(checkpointer)

        if args.list:
            _list_sessions(checkpointer, as_json=args.json)
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
                "current_step": 0,
                "messages": [],
                "element_queue": [],
                "impl_log": [],
                "errors": [],
            }
            print(f"\n{'='*60}")
            print("  Linux Ricing Session")
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
        except GraphInterrupt:
            pass  # Expected — handled below via get_state
        except Exception as e:
            print(f"\n[ERROR] {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            raise

        # Check graph state
        state = graph.get_state(config)

        # No pending nodes → session ended (complete or early exit)
        if not state.next:
            device_profile = state.values.get("device_profile", {})
            if device_profile.get("desktop_recipe") == "other":
                msg = device_profile.get("unsupported_message", "Unsupported desktop environment.")
                print(f"\n{msg}\n")
                return

            session_dir = state.values.get("session_dir", "")
            print("\n" + "="*60)
            print("  Session complete!")
            if session_dir:
                print(f"  Handoff: {session_dir}/handoff.md")
                print("  Rollback: ricer undo")
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
        itype = interrupt_val.get("type", "") if isinstance(interrupt_val, dict) else ""
        _display_interrupt(interrupt_val)

        # Get user response — mask input for password prompts
        try:
            if itype == "sudo_password":
                import getpass
                user_input = getpass.getpass("Password: ")
            else:
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


def _list_sessions(checkpointer, as_json: bool = False) -> None:
    """List all sessions in the checkpoint store.

    When *as_json* is True the output is a JSON array so callers (e.g.
    session_manager.py) can parse it without screen-scraping human text.
    """
    sessions: list[dict] = []
    try:
        # Pass None to list all checkpoints across every thread_id.
        # Passing {"configurable": {}} (no thread_id) may return nothing
        # in some SqliteSaver versions.
        configs = list(checkpointer.list(None))
        seen: set[str] = set()
        for c in configs:
            thread_id = c.config["configurable"].get("thread_id", "?")
            if thread_id in seen:
                continue  # show only the latest checkpoint per thread
            seen.add(thread_id)
            sessions.append({
                "thread_id": thread_id,
                "step": str(c.metadata.get("step", "?")),
                "created_at": c.metadata.get("created_at", "unknown"),
            })
    except Exception as e:
        if as_json:
            print(json.dumps([]))
        else:
            print(f"\n  Could not list sessions: {e}\n")
        return

    if as_json:
        print(json.dumps(sessions))
        return

    print("\nSessions:\n")
    if not sessions:
        print("  No sessions found.\n")
        return
    for s in sessions:
        print(f"  {s['thread_id']}  (step {s['step']}, {s['created_at']})")
    print()


def _new_thread_id() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    return f"rice-{ts}-{uuid.uuid4().hex[:6]}"


def _init_session_dir(thread_id: str) -> Path:
    session_dir = SESSIONS_DIR / thread_id
    session_dir.mkdir(parents=True, exist_ok=True)
    header = SESSION_HEADER_TEMPLATE.format(
        theme_name=thread_id,
        started=datetime.now().isoformat(timespec="seconds"),
        session_dir=str(session_dir),
    )
    (session_dir / "session.md").write_text(header, encoding="utf-8")
    set_current(session_dir)
    return session_dir


if __name__ == "__main__":
    main()
