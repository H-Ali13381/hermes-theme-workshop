"""Step 1 — Silent machine audit. No LLM. Returns device_profile."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ..config import SCRIPTS_DIR, SESSIONS_DIR
from ..state import RiceSessionState

# ── helpers ──────────────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except Exception:
        return -1, ""


def _detect_wm() -> str:
    for var in ("XDG_CURRENT_DESKTOP", "DESKTOP_SESSION"):
        import os
        v = os.environ.get(var, "")
        if v:
            return v.lower()
    _, out = _run(["wmctrl", "-m"])
    if "hypr" in out.lower():
        return "hyprland"
    _, out2 = _run(["plasmashell", "--version"])
    if out2:
        return "kde"
    return "unknown"


def _detect_chassis() -> str:
    _, out = _run(["cat", "/sys/class/dmi/id/chassis_type"])
    laptop_types = {"8", "9", "10", "11", "14"}
    if out.strip() in laptop_types:
        return "laptop"
    return "desktop"


def _detect_screens() -> int:
    _, out = _run(["xrandr", "--listmonitors"])
    lines = [l for l in out.splitlines() if l.strip().startswith("+")]
    if lines:
        return len(lines)
    _, out2 = _run(["hyprctl", "monitors", "-j"])
    if out2:
        try:
            return len(json.loads(out2))
        except Exception:
            pass
    return 1


def _detect_gpu() -> dict:
    _, out = _run(["lspci"])
    gpu_line = next((l for l in out.splitlines() if "VGA" in l or "3D" in l), "")
    vram_mb = 0
    _, vram_out = _run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"])
    if vram_out.isdigit():
        vram_mb = int(vram_out)
    return {"name": gpu_line.split(": ")[-1] if gpu_line else "unknown", "vram_mb": vram_mb}


def _detect_apps() -> dict[str, bool]:
    apps = [
        "kitty", "alacritty", "konsole", "foot", "wezterm",
        "waybar", "polybar",
        "rofi", "wofi",
        "dunst", "mako", "swaync",
        "hyprlock", "swaylock",
        "starship", "fastfetch", "neofetch",
        "feh", "swww", "swaybg", "awww",
    ]
    result = {}
    for app in apps:
        rc, _ = _run(["which", app])
        result[app] = rc == 0
    return result


def _detect_touchpad() -> bool:
    _, out = _run(["xinput", "list"])
    return "touchpad" in out.lower() or "synaptics" in out.lower()


def _get_current_wallpaper() -> str:
    from pathlib import Path
    # KDE
    rc, out = _run([
        "kreadconfig6", "--file", "plasma-org.kde.plasma.desktop-appletsrc",
        "--group", "Containments", "--group", "1", "--group", "Wallpaper",
        "--group", "org.kde.image", "--group", "General", "--key", "Image"
    ])
    if rc == 0 and out:
        return out
    # Hyprland/swww
    rc2, out2 = _run(["swww", "query"])
    if rc2 == 0 and out2:
        for line in out2.splitlines():
            if "image:" in line.lower():
                return line.split(":", 1)[-1].strip()
    return ""


# ── node ─────────────────────────────────────────────────────────────────────

def audit_node(state: RiceSessionState) -> dict:
    """Gather device profile silently. No user interaction."""
    print("[Step 1] Auditing your machine...", flush=True)

    wm = _detect_wm()
    chassis = _detect_chassis()
    screens = _detect_screens()
    gpu = _detect_gpu()
    apps = _detect_apps()
    has_touchpad = _detect_touchpad()
    current_wallpaper = _get_current_wallpaper()

    # Check for FAL_KEY (animated wallpaper capability)
    import os
    fal_available = bool(os.environ.get("FAL_KEY", "").strip())

    # Run desktop_state_audit to get current theme names
    current_theme = {}
    audit_script = SCRIPTS_DIR / "desktop_state_audit.py"
    if audit_script.exists():
        rc, out = _run([sys.executable, str(audit_script), "--json-summary"], timeout=15)
        if rc == 0 and out:
            try:
                current_theme = json.loads(out)
            except Exception:
                pass

    profile = {
        "wm": wm,
        "chassis": chassis,
        "screens": screens,
        "gpu": gpu,
        "has_touchpad": has_touchpad,
        "apps": apps,
        "fal_available": fal_available,
        "current_wallpaper": current_wallpaper,
        "current_theme": current_theme,
    }

    # Derive recommended element queue based on installed apps + WM
    queue = _build_element_queue(wm, apps)

    print(f"  WM: {wm} | Chassis: {chassis} | Screens: {screens} | GPU: {gpu['name'][:40]}")
    print(f"  Installed: {', '.join(k for k, v in apps.items() if v)}")
    print(f"  Element queue ({len(queue)}): {', '.join(queue)}\n")

    return {
        "device_profile": profile,
        "element_queue": queue,
        "current_step": 1,
    }


def _build_element_queue(wm: str, apps: dict) -> list[str]:
    queue = []

    # Terminal
    for t in ["kitty", "alacritty", "konsole", "foot", "wezterm"]:
        if apps.get(t):
            queue.append(f"terminal:{t}")
            break

    # Bar
    for b in ["waybar", "polybar"]:
        if apps.get(b):
            queue.append(f"bar:{b}")
            break

    # Launcher
    for l in ["rofi", "wofi"]:
        if apps.get(l):
            queue.append(f"launcher:{l}")
            break

    # Notifications
    for n in ["dunst", "mako", "swaync"]:
        if apps.get(n):
            queue.append(f"notifications:{n}")
            break

    # WM-specific
    if "hypr" in wm:
        queue.append("window_decorations:hyprland")
        if apps.get("hyprlock") or apps.get("swaylock"):
            queue.append("lock_screen:hyprlock")
    elif "kde" in wm or "plasma" in wm:
        queue.append("window_decorations:kde")
        queue.append("lock_screen:kde")

    # Universal
    queue.append("gtk_theme")
    queue.append("wallpaper")

    if apps.get("fastfetch") or apps.get("neofetch"):
        queue.append("fastfetch")

    for sp in ["starship"]:
        if apps.get(sp):
            queue.append(f"shell_prompt:{sp}")
            break

    return queue
