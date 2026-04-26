"""workflow/session.py — Session log writer.

Direct Python API for updating session.md.  Every function accepts
``session_dir`` explicitly — no subprocess, no .current symlink dependency.
"""
from __future__ import annotations

import re
from pathlib import Path

STEP_NAMES: dict[str, str] = {
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


def _md(session_dir: str) -> Path:
    return Path(session_dir) / "session.md"


def append_step(session_dir: str, step: str | int, note: str = "") -> None:
    """Mark *step* complete in session.md and update the Status line.

    If the section header already exists it is stamped ✓ in-place;
    otherwise a new section is appended.
    """
    if not session_dir:
        return
    step_id = str(step)
    step_name = STEP_NAMES.get(step_id, f"Step {step_id}")
    md = _md(session_dir)
    if not md.exists():
        return

    content = md.read_text()
    header = f"## Step {step_id} — {step_name}"
    bullet = f"- {note}\n" if note else ""

    if header in content:
        content = re.sub(
            rf"{re.escape(header)}[^\n]*",
            f"{header} ✓",
            content,
        )
    else:
        content = content + f"\n{header} ✓\n{bullet}"

    content = re.sub(
        r"^Status: .*$",
        f"Status: IN PROGRESS — Step {step_id} complete",
        content,
        flags=re.MULTILINE,
    )
    md.write_text(content)


def append_item(session_dir: str, text: str) -> None:
    """Append one bullet line to the Step 6 — Implement section.

    Creates the section header if it does not yet exist.
    """
    if not session_dir:
        return
    md = _md(session_dir)
    if not md.exists():
        return

    content = md.read_text()
    item = f"- {text}\n"

    if "## Step 6 — Implement" in content:
        content = re.sub(
            r"(## Step 6 — Implement[^\n]*\n)(.*?)((?=\n## )|\Z)",
            lambda m: m.group(1) + m.group(2) + item + m.group(3),
            content,
            flags=re.DOTALL,
        )
        md.write_text(content)
    else:
        with md.open("a") as f:
            f.write(f"\n## Step 6 — Implement\n{item}")


def mark_complete(session_dir: str) -> None:
    """Set Status to COMPLETE in session.md."""
    if not session_dir:
        return
    md = _md(session_dir)
    if not md.exists():
        return
    content = md.read_text()
    content = re.sub(r"^Status: .*$", "Status: COMPLETE", content, flags=re.MULTILINE)
    md.write_text(content)
