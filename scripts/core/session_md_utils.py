"""core/session_md_utils.py — Session markdown append/rename commands.

Extracted from scripts/session_manager.py to keep that file within the
300-line budget.  Handles the three write-heavy CLI commands:
  append-step, append-item, rename.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

from core.session_io import (
    SESSIONS_ROOT, STEP_NAMES,
    session_md, get_current_session, set_current,
    update_status_line, update_header_theme, update_header_session_dir,
)


def cmd_append_step(step_id: str, kvpairs: list[str]) -> None:
    step_name = STEP_NAMES.get(step_id)
    if not step_name:
        print(f"ERROR: Unknown step_id '{step_id}'. Valid: {list(STEP_NAMES.keys())}", file=sys.stderr)
        sys.exit(1)
    session_dir = get_current_session()
    md = session_md(session_dir)

    bullets = ""
    for pair in kvpairs:
        if "=" in pair:
            key, _, val = pair.partition("=")
            bullets += f"- {key.replace('_', ' ').capitalize()}: {val}\n"
        else:
            bullets += f"- {pair}\n"

    if step_id == "6":
        content = md.read_text(encoding="utf-8")
        if "## Step 6 — Implement" in content:
            updated = re.sub(
                r"## Step 6 — Implement\b[^\n]*",
                "## Step 6 — Implement ✓",
                content,
            )
            if bullets:
                updated = re.sub(
                    r"(## Step 6 — Implement ✓\n)(.*?)((?=\n## )|\Z)",
                    lambda m: m.group(1) + m.group(2) + bullets + m.group(3),
                    updated,
                    flags=re.DOTALL,
                )
            md.write_text(updated, encoding="utf-8")
        else:
            with md.open("a", encoding="utf-8") as f:
                f.write(f"\n## Step 6 — Implement ✓\n{bullets}")
    else:
        content = md.read_text(encoding="utf-8")
        header_pattern = f"## Step {step_id} — {step_name}"
        if header_pattern in content:
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
            md.write_text(updated, encoding="utf-8")
        else:
            section = f"\n## Step {step_id} — {step_name} ✓\n{bullets}"
            with md.open("a", encoding="utf-8") as f:
                f.write(section)

    update_status_line(session_dir, f"IN PROGRESS — Step {step_id} complete")
    print(f"Appended Step {step_id} — {step_name} ✓  →  {md}")


def cmd_append_item(text: str) -> None:
    """Append a single implement item to the Step 6 section (or create it)."""
    session_dir = get_current_session()
    md = session_md(session_dir)
    content = md.read_text(encoding="utf-8")
    item_line = f"- {text}\n"

    if "## Step 6 — Implement" in content:
        updated = re.sub(
            r"(## Step 6 — Implement[^\n]*\n)(.*?)((?=\n## )|\Z)",
            lambda m: m.group(1) + m.group(2) + item_line + m.group(3),
            content,
            flags=re.DOTALL,
        )
        md.write_text(updated, encoding="utf-8")
    else:
        with md.open("a", encoding="utf-8") as f:
            f.write(f"\n## Step 6 — Implement\n{item_line}")
    print(f"Appended implement item to Step 6: {text}")


def cmd_rename(theme_slug: str) -> None:
    session_dir = get_current_session()
    name = session_dir.name
    ts_m = re.search(r"(\d{8}-\d{4})", name)
    ts   = ts_m.group(1) if ts_m else datetime.now().strftime("%Y%m%d-%H%M")
    new_name = f"{theme_slug}-{ts}"
    new_dir  = SESSIONS_ROOT / new_name
    session_dir.rename(new_dir)
    set_current(new_dir)
    update_header_theme(new_dir, theme_slug.replace("-", " ").title())
    update_header_session_dir(new_dir)
    print(f"Renamed: {session_dir.name} → {new_name}")
    print(f"Active session: {new_dir}")
