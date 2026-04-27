"""implement/apply.py — Applies one element by calling ricer.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from ...config import SCRIPTS_DIR


def apply_element(element: str, design: dict, session_dir: str) -> dict:
    """Map element name → ricer.py materializer subcommand and run it."""
    ricer = SCRIPTS_DIR / "ricer.py"
    if not ricer.exists():
        return {"success": False, "error": "ricer.py not found"}

    materializer = _element_to_materializer(element)
    if materializer is None:
        return {"success": False, "error": f"unsupported element: {element}"}

    design_file = Path(session_dir) / "design.json" if session_dir else None
    tmpfile: Path | None = None
    if not design_file or not design_file.exists():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(design, tf)
            tf.flush()
            design_file = Path(tf.name)
        tmpfile = design_file  # remember to clean up

    cmd = [sys.executable, str(ricer), "apply", "--design", str(design_file), f"--only={materializer}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "apply timed out after 60s"}
    finally:
        if tmpfile is not None:
            tmpfile.unlink(missing_ok=True)

    if result.returncode == 0:
        return {"success": True, "stdout": result.stdout[:500]}
    return {"success": False, "error": result.stderr[:300] or result.stdout[:300]}


# Elements where category:provider doesn't map directly to the materializer key.
_PROVIDER_REMAPS: dict[str, str] = {
    "lock_screen:kde": "kde_lockscreen",
}


def _element_to_materializer(element: str) -> str | None:
    """Translate workflow element names to ricer.py APP_MATERIALIZERS keys."""
    if element in _PROVIDER_REMAPS:
        return _PROVIDER_REMAPS[element]

    if ":" in element:
        category, provider = element.split(":", 1)
        if category in {"terminal", "bar", "launcher", "notifications", "shell_prompt",
                        "window_decorations", "lock_screen"}:
            return provider
        return None

    aliases = {
        "gtk_theme": "gtk",
        "fastfetch": "fastfetch",
    }
    return aliases.get(element)
