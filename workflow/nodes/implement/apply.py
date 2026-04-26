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

    app_name = element.split(":")[0]
    sub_app  = element.split(":")[-1] if ":" in element else None

    design_file = Path(session_dir) / "design.json" if session_dir else None
    if not design_file or not design_file.exists():
        tf = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(design, tf)
        tf.close()
        design_file = Path(tf.name)

    cmd = [sys.executable, str(ricer), "apply", "--design", str(design_file), f"--only={app_name}"]
    if sub_app and sub_app != app_name:
        cmd.append(f"--app={sub_app}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode == 0:
        return {"success": True, "stdout": result.stdout[:500]}
    return {"success": False, "error": result.stderr[:300] or result.stdout[:300]}
