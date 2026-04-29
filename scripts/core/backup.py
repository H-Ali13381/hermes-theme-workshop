"""File backup and injection-removal helpers for ricer undo support."""
import shutil
from pathlib import Path

from core.constants import BACKUP_DIR


def backup_file(src: Path, backup_ts: str, label: str) -> str | None:
    """Copy src to BACKUP_DIR/<backup_ts>/<label>.  Returns backup path or None."""
    if not src.exists():
        return None
    dest = BACKUP_DIR / backup_ts / label
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return str(dest)


def _remove_injected_block(file_path: Path, marker: str) -> bool:
    """Remove a hermes-injected block from a text config file.

    Removes the marker line and the line immediately following it.
    Returns True if anything was removed.
    """
    if not file_path.exists():
        return False

    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = []
    i = 0
    removed = False
    while i < len(lines):
        if marker in lines[i]:
            # Skip the marker line AND the next line (the injected directive)
            i += 1
            if i < len(lines):
                i += 1
            # Also consume a single trailing blank line left by the injection
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            removed = True
        else:
            new_lines.append(lines[i])
            i += 1

    if removed:
        file_path.write_text("".join(new_lines), encoding="utf-8")

    return removed
