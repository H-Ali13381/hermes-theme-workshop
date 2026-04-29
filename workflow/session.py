"""workflow/session.py — Session log writer.

Direct Python API for updating session.md.  Every function accepts
``session_dir`` explicitly — no subprocess, no .current symlink dependency.
"""
from __future__ import annotations

import re
import sys
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
        print(f"[session] append_step({step}): session_dir is empty — skipping", file=sys.stderr)
        return
    step_id = str(step)
    step_name = STEP_NAMES.get(step_id, f"Step {step_id}")
    md = _md(session_dir)
    if not md.exists():
        print(f"[session] append_step({step}): {md} not found — skipping", file=sys.stderr)
        return

    content = md.read_text(encoding="utf-8")
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
    md.write_text(content, encoding="utf-8")


def append_item(session_dir: str, text: str) -> None:
    """Append one bullet line to the Step 6 — Implement section.

    Creates the section header if it does not yet exist.

    Uses string indexing rather than a regex substitution so that sections
    separated by either a single newline or a blank line are handled correctly.
    The previous regex used a lookahead for ``\\n## `` which failed to match
    when the next section was preceded by a blank line (``\\n\\n## ``).
    """
    if not session_dir:
        print("[session] append_item: session_dir is empty — skipping", file=sys.stderr)
        return
    md = _md(session_dir)
    if not md.exists():
        print(f"[session] append_item: {md} not found — skipping", file=sys.stderr)
        return

    content = md.read_text(encoding="utf-8")
    item = f"- {text}\n"
    header = "## Step 6 — Implement"

    if header not in content:
        with md.open("a", encoding="utf-8") as f:
            f.write(f"\n{header}\n{item}")
        return

    # Find the end of the Step-6 header line, then locate where the next
    # section begins (any "## " that follows).  Works regardless of whether
    # sections are separated by one or two newlines.
    idx = content.index(header)
    eol = content.find("\n", idx)           # end of the header line
    if eol == -1:
        eol = len(content)
    next_sec = re.search(r"\n## ", content[eol:])
    if next_sec:
        insert_at = eol + next_sec.start()  # position of the \n before next ##
    else:
        insert_at = len(content)            # Step 6 is the last section

    prefix = content[:insert_at]
    if not prefix.endswith("\n"):
        prefix += "\n"
    md.write_text(prefix + item + content[insert_at:], encoding="utf-8")


def mark_complete(session_dir: str) -> None:
    """Set Status to COMPLETE in session.md."""
    if not session_dir:
        print("[session] mark_complete: session_dir is empty — skipping", file=sys.stderr)
        return
    md = _md(session_dir)
    if not md.exists():
        print(f"[session] mark_complete: {md} not found — skipping", file=sys.stderr)
        return
    content = md.read_text(encoding="utf-8")
    content = re.sub(r"^Status: .*$", "Status: COMPLETE", content, flags=re.MULTILINE)
    md.write_text(content, encoding="utf-8")
