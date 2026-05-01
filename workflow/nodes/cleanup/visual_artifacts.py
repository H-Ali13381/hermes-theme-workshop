"""Screenshot artifact capture for post-implementation verification."""
from __future__ import annotations

import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def capture_visual_artifacts(state: dict) -> list[dict]:
    """Capture deterministic visual artifacts into the session directory."""
    session_dir = state.get("session_dir")
    if not session_dir:
        return []
    profile = state.get("device_profile", {})
    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "").lower()
    artifacts_dir = Path(session_dir) / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    screenshot = artifacts_dir / f"desktop-{stamp}.png"

    command = _screenshot_command(wm, screenshot)
    if command is None:
        return [{
            "type": "screenshot",
            "status": "skipped",
            "reason": "no supported screenshot tool found (spectacle/grim)",
        }]

    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return [{"type": "screenshot", "status": "error", "path": str(screenshot), "error": str(exc)}]

    if result.returncode == 0 and screenshot.exists():
        return [{"type": "screenshot", "status": "ok", "path": str(screenshot), "command": command[0]}]
    return [{
        "type": "screenshot",
        "status": "error",
        "path": str(screenshot),
        "command": command[0],
        "stderr": (result.stderr or "")[:300],
    }]


def _screenshot_command(wm: str, output: Path) -> list[str] | None:
    """Return the preferred screenshot command for this desktop."""
    if ("kde" in wm or "plasma" in wm) and shutil.which("spectacle"):
        return ["spectacle", "--background", "--fullscreen", "-o", str(output)]
    if shutil.which("grim"):
        return ["grim", str(output)]
    if shutil.which("spectacle"):
        return ["spectacle", "--background", "--fullscreen", "-o", str(output)]
    return None