"""audit/detectors.py — Machine detection helpers.

Pure functions. Each detects one aspect of the system. No LLM, no state.

WM detection is delegated to scripts/desktop_utils.py:discover_desktop() — the
single source of truth shared with ricer.py and desktop_state_audit.py.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Allow importing from scripts/ regardless of cwd — mirrors the bootstrap in ricer.py.
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[3] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from desktop_utils import discover_desktop  # noqa: E402


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return -1, ""


def detect_wm() -> str:
    """Detect the running WM/DE string.

    Delegates entirely to scripts/desktop_utils.discover_desktop() so that
    the workflow and the scripts layer share one canonical implementation.
    """
    return discover_desktop()["wm"]


def desktop_recipe_for_wm(wm: str) -> str:
    """Map detected WM/DE strings to supported recipe names."""
    w = (wm or "").lower()
    if "hypr" in w:
        return "hyprland"
    if "kde" in w or "plasma" in w:
        return "kde"
    if "gnome" in w:
        return "gnome"
    return "other"


def detect_chassis() -> str:
    try:
        out = Path("/sys/class/dmi/id/chassis_type").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        out = ""
    return "laptop" if out in {"8", "9", "10", "11", "14"} else "desktop"


def detect_screens() -> int:
    _, out = run(["xrandr", "--listmonitors"])
    lines = [line for line in out.splitlines() if line.strip().startswith("+")]
    if lines:
        return len(lines)
    _, out2 = run(["hyprctl", "monitors", "-j"])
    if out2:
        try:
            return len(json.loads(out2))
        except (json.JSONDecodeError, ValueError):
            pass
    return 1


def detect_gpu() -> dict:
    _, out = run(["lspci"])
    gpu_line = next((line for line in out.splitlines() if "VGA" in line or "3D" in line), "")
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
        "feh", "swww", "swaybg", "wbg",
    ]
    return {app: shutil.which(app) is not None for app in apps}


def detect_touchpad() -> bool:
    _, out = run(["xinput", "list"])
    return "touchpad" in out.lower() or "synaptics" in out.lower()


def get_current_wallpaper() -> str:  # noqa: PLR0911
    """Return the path to the current wallpaper, or '' if not found.

    Tries detection methods in order of specificity:
    1. KDE Plasma  — kreadconfig6 on appletsrc
    2. hyprpaper   — parse ~/.config/hypr/hyprpaper.conf for 'wallpaper ='
    3. feh         — read ~/.fehbg (first --bg-* path)
    4. nitrogen     — read ~/.config/nitrogen/bg-saved.cfg (file= key)
    5. swww        — swww query (one line per monitor; first match)
    6. awww        — awww query (same format as swww)
    7. swaybg      — /proc scan for swaybg -i argument
    """
    # 1. KDE Plasma
    rc, out = run([
        "kreadconfig6", "--file", "plasma-org.kde.plasma.desktop-appletsrc",
        "--group", "Containments", "--group", "1", "--group", "Wallpaper",
        "--group", "org.kde.image", "--group", "General", "--key", "Image",
    ])
    if rc == 0 and out:
        return out

    # 2. hyprpaper — 'wallpaper = <monitor>,<path>'
    hyprpaper_conf = Path.home() / ".config" / "hypr" / "hyprpaper.conf"
    if hyprpaper_conf.exists():
        try:
            for line in hyprpaper_conf.read_text(encoding="utf-8", errors="replace").splitlines():
                stripped = line.strip()
                if stripped.startswith("wallpaper") and "=" in stripped:
                    val = stripped.split("=", 1)[1].strip()
                    # val may be "monitor,/path" or just "/path"
                    path = val.split(",")[-1].strip()
                    if path:
                        return path
        except OSError:
            pass

    # 3. feh — ~/.fehbg: feh --bg-scale '/path/to/image.jpg'
    fehbg = Path.home() / ".fehbg"
    if fehbg.exists():
        try:
            for line in fehbg.read_text(encoding="utf-8", errors="replace").splitlines():
                # skip the feh invocation line; path is the last single-quoted token
                m = re.search(r"'([^']+)'", line)
                if m:
                    return m.group(1)
        except OSError:
            pass

    # 4. nitrogen — ~/.config/nitrogen/bg-saved.cfg
    nitrogen_cfg = Path.home() / ".config" / "nitrogen" / "bg-saved.cfg"
    if nitrogen_cfg.exists():
        try:
            for line in nitrogen_cfg.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip().startswith("file="):
                    return line.split("=", 1)[1].strip()
        except OSError:
            pass

    # 5. swww — one line per monitor: "<monitor>: image: /path"
    rc_swww, out_swww = run(["swww", "query"])
    if rc_swww == 0 and out_swww:
        for line in out_swww.splitlines():
            m = re.search(r"image:\s*(\S.*)$", line)
            if m:
                return m.group(1).strip()

    # 6. awww — same output format as swww
    rc_awww, out_awww = run(["awww", "query"])
    if rc_awww == 0 and out_awww:
        for line in out_awww.splitlines():
            m = re.search(r"image:\s*(\S.*)$", line)
            if m:
                return m.group(1).strip()

    # 7. swaybg — inspect running process arguments
    try:
        proc_dirs = Path("/proc").iterdir()
        for p in proc_dirs:
            cmdline = p / "cmdline"
            if not cmdline.exists():
                continue
            try:
                parts = cmdline.read_bytes().split(b"\x00")
                decoded = [x.decode(errors="replace") for x in parts]
                if decoded and "swaybg" in decoded[0]:
                    for idx, tok in enumerate(decoded):
                        if tok in ("-i", "--image") and idx + 1 < len(decoded):
                            return decoded[idx + 1]
            except OSError:
                continue
    except OSError:
        pass

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

    for launcher in ["rofi", "wofi"]:
        if apps.get(launcher):
            queue.append(f"launcher:{launcher}")
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
        queue.extend([
            "look_and_feel:kde",
            "plasma_theme",
            "cursor_theme",
            "icon_theme",
            "kvantum_theme",
        ])
        queue.append("window_decorations:kde")
        queue.append("lock_screen:kde")
    elif "gnome" in wm:
        # GNOME Shell theme (gnome-shell.css + gsettings color-scheme)
        queue.append("window_decorations:gnome")
        # GNOME lock screen (gsettings org.gnome.desktop.screensaver palette colors)
        queue.append("lock_screen:gnome")

    queue.append("gtk_theme")

    if apps.get("fastfetch") or apps.get("neofetch"):
        queue.append("fastfetch")

    if apps.get("starship"):
        queue.append("shell_prompt:starship")

    return queue
