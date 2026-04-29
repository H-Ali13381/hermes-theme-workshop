#!/usr/bin/env python3
"""
session_manager.py — Linux ricing session state manager.

Manages ~/.config/rice-sessions/ directories for crash-safe ricing sessions.
Every rice session writes a running session.md log that grows step-by-step,
enabling crash recovery, resume, and a human-readable audit trail.

Usage:
  python3 session_manager.py init
      Create a new session dir + session.md. Prints the session dir path.

  python3 session_manager.py resume-check
      Scan for incomplete sessions (both agent-guided and LangGraph workflow).
      Prints a unified JSON list; each entry has a "source" field:
        "agent"    — agent-guided session (session.md in ~/.config/rice-sessions/)
        "workflow" — LangGraph automated session (SQLite checkpoint)
      Resume an agent session:   session_manager.py load <dir>
      Resume a workflow session:  session_manager.py workflow-run <thread-id>
                               OR python3 workflow/run.py --resume <thread-id>

  python3 session_manager.py load <session-dir>
      Point .current symlink at an existing session dir (for resume).

  python3 session_manager.py append-step <step_id> [key=value ...]
      Append a ## Step N — Name ✓ section. step_id: 1 2 3 4 4.5 5 6 7 8
      Data passed as key=value pairs → rendered as bullet list.

  python3 session_manager.py append-item <text>
      Append a single implement item to the Step 6 section (for mid-step progress).

  python3 session_manager.py rename <theme-slug>
      Rename the active session dir to <theme-slug>-<original-timestamp>.
      Updates session.md header and .current symlink.

  python3 session_manager.py status
      Print the current session's Status line.

  python3 session_manager.py read
      Print the full session.md contents.

  python3 session_manager.py complete
      Mark session COMPLETE (update header status). Step 8 should already be appended.

  python3 session_manager.py workflow-run [<thread-id>]
      Launch the LangGraph automated workflow (workflow/run.py).
      If <thread-id> is given, resumes that session; otherwise starts a new one.

Session tracking: ~/.config/rice-sessions/.current → symlink to active session dir.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

from core.session_io import (                             # noqa: E402
    SESSIONS_ROOT, CURRENT_LINK,
    ensure_sessions_root, session_md, set_current, get_current_session,
    update_status_line, update_header_theme, update_header_session_dir,
    cmd_init,
)
from core.session_md_utils import (                       # noqa: E402
    cmd_append_step, cmd_append_item, cmd_rename,
)

# Path to workflow/run.py — used for querying and launching LangGraph sessions.
SKILL_DIR = Path(__file__).parent.parent
WORKFLOW_RUN_PY = SKILL_DIR / "workflow" / "run.py"


def _query_workflow_sessions() -> list[dict]:
    """Return incomplete LangGraph sessions by invoking ``workflow/run.py --list --json``.

    Uses JSON output so the result is not tied to the human-readable text format
    of ``--list``.  Returns [] silently when workflow/run.py is absent or its
    deps are not installed.
    """
    if not WORKFLOW_RUN_PY.exists():
        return []
    try:
        result = subprocess.run(
            [sys.executable, str(WORKFLOW_RUN_PY), "--list", "--json"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception as e:
        print(f"[session_manager] Warning: could not query workflow sessions: {e}", file=sys.stderr)
        return []

    try:
        records = json.loads(result.stdout)
    except Exception as e:
        print(f"[session_manager] Warning: could not parse workflow sessions JSON: {e}", file=sys.stderr)
        return []

    sessions: list[dict] = []
    for rec in records:
        thread_id = rec.get("thread_id", "")
        if not thread_id:
            continue
        step = rec.get("step", "?")
        ts = rec.get("created_at", "")
        sessions.append({
            "source": "workflow",
            "thread_id": thread_id,
            "theme": "In Progress",
            "started": ts,
            "status": f"IN PROGRESS — Step {step}",
            "resume_cmd": f"python3 {WORKFLOW_RUN_PY} --resume {thread_id}",
        })
    return sessions

# STEP_NAMES, SESSION_HEADER_TEMPLATE, ensure_sessions_root, session_md,
# set_current, get_current_session, update_status_line, update_header_*,
# and cmd_init are all imported from core.session_io above.
# cmd_append_step, cmd_append_item, cmd_rename imported from core.session_md_utils.


def cmd_resume_check():
    """Print a unified JSON list of all incomplete sessions.

    Each entry has a ``"source"`` field:
      ``"agent"``    — agent-guided session tracked by session.md
      ``"workflow"`` — LangGraph automated session (SQLite checkpoint)

    Agent sessions include a ``"dir"`` key; workflow sessions include
    ``"thread_id"`` and ``"resume_cmd"``.

    Workflow session dirs also live in SESSIONS_ROOT and contain session.md,
    so we query SQLite first and skip any filesystem dir whose name matches a
    known workflow thread_id — preventing duplicate entries.
    """
    ensure_sessions_root()
    results = []

    # --- LangGraph workflow sessions (SQLite checkpoint) — query first ---
    workflow_sessions = _query_workflow_sessions()
    workflow_thread_ids = {s["thread_id"] for s in workflow_sessions}

    # --- agent-guided sessions (session.md files) ---
    for d in sorted(SESSIONS_ROOT.iterdir(), reverse=True):
        if not d.is_dir() or d.name.startswith("."):
            continue
        if d.name in workflow_thread_ids:
            continue  # already represented by SQLite entry — skip to avoid duplicate
        md = session_md(d)
        if not md.exists():
            continue
        text = md.read_text(encoding="utf-8")
        status_m = re.search(r"^Status: (.*)$", text, re.MULTILINE)
        theme_m = re.search(r"^# Rice Session: (.*)$", text, re.MULTILINE)
        started_m = re.search(r"^Started: (.*)$", text, re.MULTILINE)
        status = status_m.group(1).strip() if status_m else "unknown"
        if "IN PROGRESS" in status:
            results.append({
                "source": "agent",
                "dir": str(d),
                "theme": theme_m.group(1).strip() if theme_m else "unknown",
                "started": started_m.group(1).strip() if started_m else "unknown",
                "status": status,
            })

    results.extend(workflow_sessions)
    print(json.dumps(results, indent=2))


def cmd_load(session_dir_str: str):
    target = Path(session_dir_str).expanduser().resolve()
    if not target.is_dir():
        print(f"ERROR: Not a directory: {target}", file=sys.stderr)
        sys.exit(1)
    if not session_md(target).exists():
        print(f"ERROR: No session.md in {target}", file=sys.stderr)
        sys.exit(1)
    set_current(target)
    print(f"Loaded session: {target}")


# cmd_append_step, cmd_append_item, cmd_rename imported from core.session_md_utils above.


def cmd_status():
    session_dir = get_current_session()
    text = session_md(session_dir).read_text(encoding="utf-8")
    m = re.search(r"^Status: (.*)$", text, re.MULTILINE)
    print(m.group(1).strip() if m else "Status: unknown")


def cmd_read():
    session_dir = get_current_session()
    print(session_md(session_dir).read_text(encoding="utf-8"))


def cmd_complete():
    session_dir = get_current_session()
    update_status_line(session_dir, "COMPLETE")
    print(f"Session marked COMPLETE: {session_dir}")


def cmd_workflow_run(thread_id: str | None = None) -> None:
    """Launch or resume the LangGraph automated workflow.

    Delegates to ``workflow/run.py``, passing ``--resume <thread_id>`` when a
    thread ID is supplied.  Exits with the subprocess return code.
    """
    if not WORKFLOW_RUN_PY.exists():
        print(
            f"ERROR: workflow/run.py not found at {WORKFLOW_RUN_PY}\n"
            "Make sure the skill directory is intact.",
            file=sys.stderr,
        )
        sys.exit(1)
    cmd = [sys.executable, str(WORKFLOW_RUN_PY)]
    if thread_id:
        cmd += ["--resume", thread_id]
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "resume-check":
        cmd_resume_check()
    elif cmd == "load":
        if len(sys.argv) < 3:
            print("ERROR: load requires <session-dir>", file=sys.stderr)
            sys.exit(1)
        cmd_load(sys.argv[2])
    elif cmd == "append-step":
        if len(sys.argv) < 3:
            print("ERROR: append-step requires <step_id>", file=sys.stderr)
            sys.exit(1)
        cmd_append_step(sys.argv[2], sys.argv[3:])
    elif cmd == "append-item":
        if len(sys.argv) < 3:
            print("ERROR: append-item requires <text>", file=sys.stderr)
            sys.exit(1)
        cmd_append_item(" ".join(sys.argv[2:]))
    elif cmd == "rename":
        if len(sys.argv) < 3:
            print("ERROR: rename requires <theme-slug>", file=sys.stderr)
            sys.exit(1)
        cmd_rename(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    elif cmd == "read":
        cmd_read()
    elif cmd == "complete":
        cmd_complete()
    elif cmd == "workflow-run":
        cmd_workflow_run(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print(f"ERROR: Unknown command '{cmd}'", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
