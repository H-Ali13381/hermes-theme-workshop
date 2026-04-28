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
from datetime import datetime
from pathlib import Path

SESSIONS_ROOT = Path.home() / ".config" / "rice-sessions"
CURRENT_LINK = SESSIONS_ROOT / ".current"

# Path to workflow/run.py — used for querying and launching LangGraph sessions.
SKILL_DIR = Path(__file__).parent.parent
WORKFLOW_RUN_PY = SKILL_DIR / "workflow" / "run.py"


def _query_workflow_sessions() -> list[dict]:
    """Return incomplete LangGraph sessions by invoking ``workflow/run.py --list``.

    Output format from run.py --list (one line per session):
        rice-YYYYMMDD-HHMM-xxxxxx  (step N, TS)
    Returns [] silently when workflow/run.py is absent or its deps are not installed.
    """
    if not WORKFLOW_RUN_PY.exists():
        return []
    try:
        result = subprocess.run(
            [sys.executable, str(WORKFLOW_RUN_PY), "--list"],
            capture_output=True, text=True, timeout=15,
        )
    except Exception:
        return []

    sessions: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        # Match: rice-YYYYMMDD-HHMM-xxxxxx  (step N, TIMESTAMP)
        m = re.match(r"(rice-\S+)\s+\(step\s+(\S+),\s*(.*)\)", line)
        if not m:
            continue
        thread_id = m.group(1)
        step = m.group(2).rstrip(",")
        ts = m.group(3).strip()
        sessions.append({
            "source": "workflow",
            "thread_id": thread_id,
            "theme": "In Progress",
            "started": ts,
            "status": f"IN PROGRESS — Step {step}",
            "resume_cmd": f"python3 {WORKFLOW_RUN_PY} --resume {thread_id}",
        })
    return sessions

STEP_NAMES = {
    "1": "Audit",
    "2": "Explore",
    "3": "Refine",
    "4": "Plan",
    "4.5": "Rollback Checkpoint",
    "5": "Install",
    "6": "Implement",
    "7": "Cleanup",
    "8": "Handoff",
}

SESSION_HEADER_TEMPLATE = """\
# Rice Session: {theme_name}
Started: {started}
Status: IN PROGRESS — Step 0 complete
Session dir: {session_dir}

---
"""


def ensure_sessions_root():
    SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)


def get_current_session() -> Path:
    if not CURRENT_LINK.is_symlink():
        print("ERROR: No active session. Run `init` first.", file=sys.stderr)
        sys.exit(1)
    target = CURRENT_LINK.resolve()
    if not target.is_dir():
        print(f"ERROR: Active session dir missing: {target}", file=sys.stderr)
        sys.exit(1)
    return target


def session_md(session_dir: Path) -> Path:
    return session_dir / "session.md"


def set_current(session_dir: Path):
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()
    CURRENT_LINK.symlink_to(session_dir)


def update_status_line(session_dir: Path, new_status: str):
    md = session_md(session_dir)
    text = md.read_text()
    updated = re.sub(r"^Status: .*$", f"Status: {new_status}", text, flags=re.MULTILINE)
    md.write_text(updated)


def update_header_theme(session_dir: Path, theme_name: str):
    md = session_md(session_dir)
    text = md.read_text()
    updated = re.sub(r"^# Rice Session: .*$", f"# Rice Session: {theme_name}", text, flags=re.MULTILINE)
    md.write_text(updated)


def update_header_session_dir(session_dir: Path):
    md = session_md(session_dir)
    text = md.read_text()
    updated = re.sub(
        r"^Session dir: .*$",
        f"Session dir: {session_dir}",
        text,
        flags=re.MULTILINE,
    )
    md.write_text(updated)


def cmd_init():
    ensure_sessions_root()
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    slug = f"session-{ts}"
    session_dir = SESSIONS_ROOT / slug
    session_dir.mkdir(parents=True, exist_ok=False)
    header = SESSION_HEADER_TEMPLATE.format(
        theme_name="In Progress",
        started=datetime.now().isoformat(timespec="seconds"),
        session_dir=str(session_dir),
    )
    session_md(session_dir).write_text(header)
    set_current(session_dir)
    print(str(session_dir))


def cmd_resume_check():
    """Print a unified JSON list of all incomplete sessions.

    Each entry has a ``"source"`` field:
      ``"agent"``    — agent-guided session tracked by session.md
      ``"workflow"`` — LangGraph automated session (SQLite checkpoint)

    Agent sessions include a ``"dir"`` key; workflow sessions include
    ``"thread_id"`` and ``"resume_cmd"``.
    """
    ensure_sessions_root()
    results = []

    # --- agent-guided sessions (session.md files) ---
    for d in sorted(SESSIONS_ROOT.iterdir(), reverse=True):
        if not d.is_dir() or d.name.startswith("."):
            continue
        md = session_md(d)
        if not md.exists():
            continue
        text = md.read_text()
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

    # --- LangGraph workflow sessions (SQLite checkpoint) ---
    results.extend(_query_workflow_sessions())

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


def cmd_append_step(step_id: str, kvpairs: list[str]):
    step_name = STEP_NAMES.get(step_id)
    if not step_name:
        print(f"ERROR: Unknown step_id '{step_id}'. Valid: {list(STEP_NAMES.keys())}", file=sys.stderr)
        sys.exit(1)
    session_dir = get_current_session()
    md = session_md(session_dir)

    # Build bullet content (shared for new section and step-6 addendum)
    bullets = ""
    for pair in kvpairs:
        if "=" in pair:
            key, _, val = pair.partition("=")
            bullets += f"- {key.replace('_', ' ').capitalize()}: {val}\n"
        else:
            bullets += f"- {pair}\n"

    # Step 6 is append-only — mark existing header ✓ rather than creating a new section
    if step_id == "6":
        content = md.read_text()
        if "## Step 6 — Implement" in content:
            updated = re.sub(
                r"## Step 6 — Implement\b[^\n]*",
                f"## Step 6 — Implement ✓",
                content,
            )
            if bullets:
                # Match content up to the next section header (lookahead) or end of string.
                # Group 3 is a zero-width lookahead — m.group(3) is always "".
                updated = re.sub(
                    r"(## Step 6 — Implement ✓\n)(.*?)((?=\n## )|\Z)",
                    lambda m: m.group(1) + m.group(2) + bullets + m.group(3),
                    updated,
                    flags=re.DOTALL,
                )
            md.write_text(updated)
        else:
            # No items yet — create section with ✓
            with md.open("a") as f:
                f.write(f"\n## Step 6 — Implement ✓\n{bullets}")
    else:
        content = md.read_text()
        header_pattern = f"## Step {step_id} — {step_name}"
        if header_pattern in content:
            # Section already exists — mark ✓ and append any new bullets in-place
            # rather than creating a duplicate header.
            updated = re.sub(
                rf"## Step {re.escape(step_id)} — {re.escape(step_name)}\b[^\n]*",
                f"## Step {step_id} — {step_name} ✓",
                content,
            )
            if bullets:
                updated = re.sub(
                    rf"(## Step {re.escape(step_id)} — {re.escape(step_name)} ✓\n)(.*?)((?=\n## )|\Z)",
                    lambda m: m.group(1) + m.group(2) + bullets + m.group(3),
                    updated,
                    flags=re.DOTALL,
                )
            md.write_text(updated)
        else:
            section = f"\n## Step {step_id} — {step_name} ✓\n{bullets}"
            with md.open("a") as f:
                f.write(section)

    # Update status header
    update_status_line(session_dir, f"IN PROGRESS — Step {step_id} complete")
    print(f"Appended Step {step_id} — {step_name} ✓  →  {md}")


def cmd_append_item(text: str):
    """Append a single implement item to the Step 6 section (or create it)."""
    session_dir = get_current_session()
    md = session_md(session_dir)
    content = md.read_text()
    item_line = f"- {text}\n"

    if "## Step 6 — Implement" in content:
        # Append item at the end of the Step 6 block, before the next ## header (if any)
        # or at end-of-string. Group 3 is a zero-width lookahead — m.group(3) is always "".
        updated = re.sub(
            r"(## Step 6 — Implement[^\n]*\n)(.*?)((?=\n## )|\Z)",
            lambda m: m.group(1) + m.group(2) + item_line + m.group(3),
            content,
            flags=re.DOTALL,
        )
        md.write_text(updated)
    else:
        # Create the section (no trailing blank line — items are dense)
        with md.open("a") as f:
            f.write(f"\n## Step 6 — Implement\n{item_line}")

    print(f"Appended implement item to Step 6: {text}")


def cmd_rename(theme_slug: str):
    session_dir = get_current_session()
    # Extract original timestamp from dir name (session-YYYYMMDD-HHMM or old-slug-YYYYMMDD-HHMM)
    name = session_dir.name
    ts_m = re.search(r"(\d{8}-\d{4})$", name)
    if ts_m:
        ts = ts_m.group(1)
    else:
        ts = datetime.now().strftime("%Y%m%d-%H%M")

    new_name = f"{theme_slug}-{ts}"
    new_dir = SESSIONS_ROOT / new_name
    session_dir.rename(new_dir)
    set_current(new_dir)

    update_header_theme(new_dir, theme_slug.replace("-", " ").title())
    update_header_session_dir(new_dir)

    print(f"Renamed: {session_dir.name} → {new_name}")
    print(f"Active session: {new_dir}")


def cmd_status():
    session_dir = get_current_session()
    text = session_md(session_dir).read_text()
    m = re.search(r"^Status: (.*)$", text, re.MULTILINE)
    print(m.group(1).strip() if m else "Status: unknown")


def cmd_read():
    session_dir = get_current_session()
    print(session_md(session_dir).read_text())


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
