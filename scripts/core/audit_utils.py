"""core/audit_utils.py — Low-level shell and INI utilities for desktop_state_audit.

Extracted from scripts/desktop_state_audit.py to keep that file within the
300-line budget.  These helpers are intentionally self-contained (no imports
from other core modules) so desktop_state_audit.py can remain standalone.
"""
import re
import shutil
import subprocess
from pathlib import Path


def run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str, str]:
    """Run a shell command, return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (OSError, subprocess.SubprocessError, TimeoutError) as e:
        return -1, "", str(e)


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def kread(group: str, key: str, file: str = "kdeglobals") -> str | None:
    """Read a KDE config value using kreadconfig6 or kreadconfig5."""
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([
                tool, "--file", file,
                "--group", group,
                "--key", key
            ])
            if rc == 0 and out:
                return out
    return None


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
