"""cleanup/reloader.py — Config validation and service reloading."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def _strip_jsonc_comments(text: str) -> str:
    """Remove // line comments from JSONC text, skipping // inside string literals."""
    result: list[str] = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\":
                result.append(ch)
                i += 1
                if i < len(text):
                    result.append(text[i])
            elif ch == '"':
                in_string = False
                result.append(ch)
            else:
                result.append(ch)
        else:
            if ch == '"':
                in_string = True
                result.append(ch)
            elif ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            else:
                result.append(ch)
        i += 1
    return "".join(result)


def validate_file(path: Path) -> tuple[bool, str]:
    """Return (True, '') if the file is syntactically valid, else (False, reason)."""
    try:
        text = path.read_text(errors="replace")
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

    elif path.suffix in (".conf", ".ini", ".cfg"):
        # Heuristic: check for unclosed braces/brackets which indicate truncation
        opens  = text.count("{") + text.count("[")
        closes = text.count("}") + text.count("]")
        if opens != closes:
            return False, f"{path.name}: unbalanced braces/brackets ({opens} open, {closes} close)"

    elif path.suffix == ".css":
        opens  = text.count("{")
        closes = text.count("}")
        if opens != closes:
            return False, f"{path.name}: unbalanced braces ({opens} open, {closes} close)"

    return True, ""


def reload_waybar(reloaded: list[str], errors: list[str]) -> None:
    r = subprocess.run(["pkill", "-SIGUSR2", "waybar"], capture_output=True)
    if r.returncode == 0:
        reloaded.append("waybar")
    else:
        subprocess.run(["pkill", "waybar"], capture_output=True)
        try:
            subprocess.Popen(["waybar"])
            reloaded.append("waybar(restart)")
        except FileNotFoundError:
            errors.append("waybar not found in PATH — skipping restart")


def reload_dunst(reloaded: list[str], errors: list[str]) -> None:
    subprocess.run(["pkill", "dunst"], capture_output=True)
    try:
        subprocess.Popen(["dunst"])
        reloaded.append("dunst")
    except FileNotFoundError:
        errors.append("dunst not found in PATH — skipping restart")


def reload_mako(reloaded: list[str], errors: list[str]) -> None:
    r = subprocess.run(["makoctl", "reload"], capture_output=True)
    if r.returncode == 0:
        reloaded.append("mako")
    else:
        subprocess.run(["pkill", "mako"], capture_output=True)
        try:
            subprocess.Popen(["mako"])
            reloaded.append("mako(restart)")
        except FileNotFoundError:
            errors.append("mako not found in PATH — skipping restart")


def reload_swaync(reloaded: list[str], errors: list[str]) -> None:
    r = subprocess.run(["swaync-client", "--reload-config"], capture_output=True)
    if r.returncode == 0:
        reloaded.append("swaync")
    else:
        subprocess.run(["pkill", "swaync"], capture_output=True)
        try:
            subprocess.Popen(["swaync"])
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
