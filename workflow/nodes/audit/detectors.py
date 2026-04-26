"""audit/detectors.py — Machine detection helpers.

Pure functions. Each detects one aspect of the system. No LLM, no state.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception:
        return -1, ""


def detect_wm() -> str:
    for var in ("XDG_CURRENT_DESKTOP", "DESKTOP_SESSION"):
        v = os.environ.get(var, "")
        if v:
            return v.lower()
    _, out = run(["wmctrl", "-m"])
    if "hypr" in out.lower():
        return "hyprland"
    _, out2 = run(["plasmashell", "--version"])
    if out2:
        return "kde"
    return "unknown"


def detect_chassis() -> str:
    _, out = run(["cat", "/sys/class/dmi/id/chassis_type"])
    return "laptop" if out.strip() in {"8", "9", "10", "11", "14"} else "desktop"


def detect_screens() -> int:
    _, out = run(["xrandr", "--listmonitors"])
    lines = [l for l in out.splitlines() if l.strip().startswith("+")]
    if lines:
        return len(lines)
    _, out2 = run(["hyprctl", "monitors", "-j"])
    if out2:
        try:
            return len(json.loads(out2))
        except Exception:
            pass
    return 1


def detect_gpu() -> dict:
    _, out = run(["lspci"])
    gpu_line = next((l for l in out.splitlines() if "VGA" in l or "3D" in l), "")
    _, vram_out = run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"])
    vram_mb = int(vram_out) if vram_out.isdigit() else 0
    return {"name": gpu_line.split(": ")[-1] if gpu_line else "unknown", "vram_mb": vram_mb}


def detect_apps() -> dict[str, bool]:
    apps = [
        "kitty", "alacritty", "konsole", "foot", "wezterm",
        "waybar", "polybar",
        "rofi", "wofi",
        "dunst", "mako", "swaync",
        "hyprlock", "swaylock",
        "starship", "fastfetch", "neofetch",
        "feh", "swww", "swaybg", "awww",
    ]
    return {app: run(["which", app])[0] == 0 for app in apps}


def detect_touchpad() -> bool:
    _, out = run(["xinput", "list"])
    return "touchpad" in out.lower() or "synaptics" in out.lower()


def get_current_wallpaper() -> str:
    rc, out = run([
        "kreadconfig6", "--file", "plasma-org.kde.plasma.desktop-appletsrc",
        "--group", "Containments", "--group", "1", "--group", "Wallpaper",
        "--group", "org.kde.image", "--group", "General", "--key", "Image",
    ])
    if rc == 0 and out:
        return out
    rc2, out2 = run(["swww", "query"])
    if rc2 == 0 and out2:
        for line in out2.splitlines():
            if "image:" in line.lower():
                return line.split(":", 1)[-1].strip()
    return ""


def build_element_queue(wm: str, apps: dict) -> list[str]:
    queue = []

    for t in ["kitty", "alacritty", "konsole", "foot", "wezterm"]:
        if apps.get(t):
            queue.append(f"terminal:{t}")
            break

    for b in ["waybar", "polybar"]:
        if apps.get(b):
            queue.append(f"bar:{b}")
            break

    for l in ["rofi", "wofi"]:
        if apps.get(l):
            queue.append(f"launcher:{l}")
            break

    for n in ["dunst", "mako", "swaync"]:
        if apps.get(n):
            queue.append(f"notifications:{n}")
            break

    if "hypr" in wm:
        queue.append("window_decorations:hyprland")
        if apps.get("hyprlock") or apps.get("swaylock"):
            queue.append("lock_screen:hyprlock")
    elif "kde" in wm or "plasma" in wm:
        queue.append("window_decorations:kde")
        queue.append("lock_screen:kde")

    queue.append("gtk")

    if apps.get("fastfetch") or apps.get("neofetch"):
        queue.append("fastfetch")

    if apps.get("starship"):
        queue.append("shell_prompt:starship")

    return queue
