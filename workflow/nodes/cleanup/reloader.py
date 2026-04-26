"""cleanup/reloader.py — Config validation and service reloading."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def validate_file(path: Path) -> tuple[bool, str]:
    """Return (True, '') if the file is syntactically valid, else (False, reason)."""
    if path.suffix in (".json", ".jsonc"):
        try:
            content = re.sub(r"//.*", "", path.read_text())
            json.loads(content)
        except Exception as e:
            return False, f"{path.name}: {e}"
    return True, ""


def reload_waybar(reloaded: list[str]) -> None:
    r = subprocess.run(["pkill", "-SIGUSR2", "waybar"], capture_output=True)
    if r.returncode == 0:
        reloaded.append("waybar")
    else:
        subprocess.run(["pkill", "waybar"], capture_output=True)
        subprocess.Popen(["waybar"])
        reloaded.append("waybar(restart)")


def reload_dunst(reloaded: list[str]) -> None:
    subprocess.run(["pkill", "dunst"], capture_output=True)
    subprocess.Popen(["dunst"])
    reloaded.append("dunst")


def reload_hyprland(reloaded: list[str], errors: list[str]) -> None:
    r = subprocess.run(["hyprctl", "reload"], capture_output=True, text=True, timeout=10)
    if r.returncode == 0:
        reloaded.append("hyprland")
    else:
        errors.append(f"hyprctl reload failed: {r.stderr[:100]}")
