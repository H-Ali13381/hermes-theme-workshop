"""core/audit_utils.py — Low-level shell and INI utilities for desktop_state_audit.

Extracted from scripts/desktop_state_audit.py to keep that file within the
300-line budget.  Subprocess and KDE config helpers are re-exported from
core.process so there is a single implementation.
"""
import re
import shutil
from pathlib import Path

from core.process import run_cmd, cmd_exists, _kread


def kread(group: str, key: str, file: str = "kdeglobals") -> str | None:
    """Read a KDE config value.  Thin wrapper around _kread with legacy arg order."""
    return _kread(file, group, key)


def read_ini_key(filepath: Path, section: str, key: str) -> str | None:
    """Parse a simple INI file for a specific section key."""
    if not filepath.exists():
        return None
    text = filepath.read_text(encoding="utf-8", errors="replace")
    section_pattern = re.compile(
        rf"^\[{re.escape(section)}\]\s*$",
        re.MULTILINE
    )
    m = section_pattern.search(text)
    if not m:
        return None
    start = m.end()
    next_section = re.search(r"^\[", text[start:], re.MULTILINE)
    if next_section:
        section_text = text[start:start + next_section.start()]
    else:
        section_text = text[start:]
    key_match = re.search(
        rf"^{re.escape(key)}\s*=\s*(.*)$",
        section_text,
        re.MULTILINE
    )
    if key_match:
        return key_match.group(1).strip()
    return None


def copy_to_baseline(src: Path, dest_dir: Path, label: str) -> str | None:
    """Copy a file or directory into the baseline backup dir."""
    if not src.exists():
        return None
    dest = dest_dir / label
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    return str(dest)
