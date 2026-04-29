"""core/session_io.py — Low-level I/O helpers for rice session state.

Extracted from scripts/session_manager.py to keep that file within the
300-line budget.  Provides the shared constants, path helpers, and header-
mutation functions used by both session_manager.py and session_md_utils.py.
"""
from __future__ import annotations

import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

SESSIONS_ROOT = Path.home() / ".config" / "rice-sessions"
CURRENT_LINK  = SESSIONS_ROOT / ".current"

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

SESSION_HEADER_TEMPLATE = """\
# Rice Session: {theme_name}
Started: {started}
Status: IN PROGRESS — Step 0 complete
Session dir: {session_dir}

---
"""


def ensure_sessions_root() -> None:
    SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)


def session_md(session_dir: Path) -> Path:
    return session_dir / "session.md"


def set_current(session_dir: Path) -> None:
    if CURRENT_LINK.is_symlink() or CURRENT_LINK.exists():
        CURRENT_LINK.unlink()
    CURRENT_LINK.symlink_to(session_dir)


def get_current_session() -> Path:
    if not CURRENT_LINK.is_symlink():
        print("ERROR: No active session. Run `init` first.", file=sys.stderr)
        sys.exit(1)
    target = CURRENT_LINK.resolve()
    if not target.is_dir():
        print(f"ERROR: Active session dir missing: {target}", file=sys.stderr)
        sys.exit(1)
    return target


def update_status_line(session_dir: Path, new_status: str) -> None:
    md = session_md(session_dir)
    text = md.read_text(encoding="utf-8")
    updated = re.sub(r"^Status: .*$", f"Status: {new_status}", text, flags=re.MULTILINE)
    md.write_text(updated, encoding="utf-8")


def update_header_theme(session_dir: Path, theme_name: str) -> None:
    md = session_md(session_dir)
    text = md.read_text(encoding="utf-8")
    updated = re.sub(r"^# Rice Session: .*$", f"# Rice Session: {theme_name}", text, flags=re.MULTILINE)
    md.write_text(updated, encoding="utf-8")


def update_header_session_dir(session_dir: Path) -> None:
    md = session_md(session_dir)
    text = md.read_text(encoding="utf-8")
    updated = re.sub(
        r"^Session dir: .*$", f"Session dir: {session_dir}", text, flags=re.MULTILINE
    )
    md.write_text(updated, encoding="utf-8")


def cmd_init() -> None:
    ensure_sessions_root()
    ts   = datetime.now().strftime("%Y%m%d-%H%M")
    slug = f"rice-{ts}-{uuid.uuid4().hex[:6]}"
    session_dir = SESSIONS_ROOT / slug
    session_dir.mkdir(parents=True, exist_ok=False)
    header = SESSION_HEADER_TEMPLATE.format(
        theme_name="In Progress",
        started=datetime.now().isoformat(timespec="seconds"),
        session_dir=str(session_dir),
    )
    session_md(session_dir).write_text(header, encoding="utf-8")
    set_current(session_dir)
    print(str(session_dir))


def load_design_file(path: str | Path) -> dict:
    """Load a design file from *path*, supporting both JSON and YAML.

    Tries JSON first (no extra dependency) and falls back to ``yaml.safe_load``
    when the file is not valid JSON.  Raises a clear error if neither parser
    succeeds or if *pyyaml* is missing for a YAML file.
    """
    import json

    p = Path(path)
    text = p.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        try:
            import yaml
        except ImportError as imp_exc:
            raise RuntimeError(
                f"{p.name}: not valid JSON and pyyaml is not installed "
                f"(pip install pyyaml)"
            ) from imp_exc
        try:
            return yaml.safe_load(text)
        except Exception as yaml_exc:
            raise RuntimeError(
                f"{p.name}: failed to parse as JSON ({exc}) and as YAML ({yaml_exc})"
            ) from yaml_exc
