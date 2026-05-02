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


def _remove_injected_block(
    file_path: Path,
    marker: str,
    marker_end: str | None = None,
) -> bool:
    """Remove a hermes-injected block from a text config file.

    Two protocols are supported:

    **New (preferred)** — start/end marker pair:
        Pass ``marker_end`` in addition to ``marker``.  Every line from the
        start marker (inclusive) up to and including the matching end-marker
        line is removed, plus one optional trailing blank line.  This handles
        multi-line injected blocks safely regardless of how many lines were
        inserted between the markers.

    **Legacy (backward compat)** — single marker only:
        When ``marker_end`` is *None* the old behaviour is preserved:
        the marker line *and* the immediately following line are removed,
        plus one optional trailing blank line.  This keeps old manifests
        (written before start/end markers were adopted) working correctly.

    Returns True if anything was removed.
    """
    if not file_path.exists():
        return False

    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines: list[str] = []
    i = 0
    removed = False

    while i < len(lines):
        if marker in lines[i]:
            if marker_end is not None:
                # New protocol: skip until we find the end marker (inclusive).
                i += 1  # skip the start-marker line
                while i < len(lines) and marker_end not in lines[i]:
                    i += 1
                if i < len(lines):
                    i += 1  # skip the end-marker line itself
            else:
                # Legacy protocol: skip marker line + the one following line.
                i += 1
                if i < len(lines):
                    i += 1
            # Consume a single trailing blank line left by either injection style.
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            removed = True
        else:
            new_lines.append(lines[i])
            i += 1

    if removed:
        file_path.write_text("".join(new_lines), encoding="utf-8")

    return removed
