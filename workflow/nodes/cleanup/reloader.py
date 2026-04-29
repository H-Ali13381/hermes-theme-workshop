"""cleanup/reloader.py — Config validation and service reloading."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ...utils import strip_jsonc_comments as _strip_jsonc_comments
from ...utils import css_braces_balanced as _css_braces_balanced


def validate_file(path: Path) -> tuple[bool, str]:
    """Return (True, '') if the file is syntactically valid, else (False, reason)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return False, f"{path.name}: cannot read: {e}"

    if path.suffix in (".json", ".jsonc"):
        try:
            json.loads(_strip_jsonc_comments(text))
        except Exception as e:
            return False, f"{path.name}: {e}"

    elif path.suffix == ".toml":
        try:
            import tomllib  # Python 3.11+
            tomllib.loads(text)
        except ImportError:
            pass  # tomllib unavailable — skip deep check
        except Exception as e:
            return False, f"{path.name}: {e}"

    elif path.suffix == ".css":
        if not _css_braces_balanced(text):
            return False, f"{path.name}: unbalanced braces (outside strings/comments)"

    return True, ""


def reload_waybar(reloaded: list[str], errors: list[str]) -> None:
    r = subprocess.run(["pkill", "-SIGUSR2", "waybar"], capture_output=True, timeout=5)
    if r.returncode == 0:
        reloaded.append("waybar")
    else:
        subprocess.run(["pkill", "waybar"], capture_output=True, timeout=5)
        try:
            subprocess.Popen(["waybar"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            reloaded.append("waybar(restart)")
        except FileNotFoundError:
            errors.append("waybar not found in PATH — skipping restart")


def reload_polybar(reloaded: list[str], errors: list[str]) -> None:
    subprocess.run(["pkill", "polybar"], capture_output=True, timeout=5)
    try:
        subprocess.Popen(["polybar"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        reloaded.append("polybar(restart)")
    except FileNotFoundError:
        errors.append("polybar not found in PATH — skipping restart")


def reload_dunst(reloaded: list[str], errors: list[str]) -> None:
    subprocess.run(["pkill", "dunst"], capture_output=True, timeout=5)
    try:
        subprocess.Popen(["dunst"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        reloaded.append("dunst")
    except FileNotFoundError:
        errors.append("dunst not found in PATH — skipping restart")


def reload_mako(reloaded: list[str], errors: list[str]) -> None:
    r = subprocess.run(["makoctl", "reload"], capture_output=True, timeout=5)
    if r.returncode == 0:
        reloaded.append("mako")
    else:
        subprocess.run(["pkill", "mako"], capture_output=True, timeout=5)
        try:
            subprocess.Popen(["mako"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            reloaded.append("mako(restart)")
        except FileNotFoundError:
            errors.append("mako not found in PATH — skipping restart")


def reload_swaync(reloaded: list[str], errors: list[str]) -> None:
    r = subprocess.run(["swaync-client", "--reload-config"], capture_output=True, timeout=5)
    if r.returncode == 0:
        reloaded.append("swaync")
    else:
        subprocess.run(["pkill", "swaync"], capture_output=True, timeout=5)
        try:
            subprocess.Popen(["swaync"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            reloaded.append("swaync(restart)")
        except FileNotFoundError:
            errors.append("swaync not found in PATH — skipping restart")


def reload_hyprland(reloaded: list[str], errors: list[str]) -> None:
    try:
        r = subprocess.run(["hyprctl", "reload"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            reloaded.append("hyprland")
        else:
            errors.append(f"hyprctl reload failed: {r.stderr[:100]}")
    except subprocess.TimeoutExpired:
        errors.append("hyprctl reload timed out after 10 seconds")
