"""System discovery: detect installed apps and desktop environment."""
import os
from datetime import datetime, timezone
from typing import Any

from core.constants import HOME
from core.process import run_cmd, cmd_exists, _get_kwrite
from desktop_utils import discover_desktop


def discover_apps() -> dict[str, Any]:
    """Detect installed themable applications and their config paths."""
    apps = {}

    _xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    # KDE sub-systems — plasmashell is KDE-exclusive (unlike kwriteconfig, which
    # ships with any KDE Frameworks app such as Kdenlive on a GNOME system).
    # XDG_CURRENT_DESKTOP covers edge cases where plasmashell isn't in PATH
    # (e.g. Flatpak-only KDE setups or headless test environments).
    if cmd_exists("plasmashell") or "kde" in _xdg or "plasma" in _xdg:
        apps["kde"] = {
            "installed": True,
            "config_dir": str(HOME / ".config"),
            "tools": {
                "apply_colorscheme": cmd_exists("plasma-apply-colorscheme"),
                "apply_wallpaper": cmd_exists("plasma-apply-wallpaperimage"),
                "kwriteconfig": _get_kwrite(),
                "kreadconfig": "kreadconfig6" if cmd_exists("kreadconfig6") else (
                    "kreadconfig5" if cmd_exists("kreadconfig5") else None
                ),
            },
        }

    for term in ["kitty", "alacritty", "konsole", "foot", "wezterm"]:
        if cmd_exists(term):
            apps[term] = {"installed": True, "config_dir": str(HOME / ".config" / term)}

    for bar in ["waybar", "polybar", "eww"]:
        if cmd_exists(bar):
            apps[bar] = {"installed": True, "config_dir": str(HOME / ".config" / bar)}

    for launcher in ["rofi", "wofi", "fuzzel"]:
        if cmd_exists(launcher):
            apps[launcher] = {"installed": True, "config_dir": str(HOME / ".config" / launcher)}

    for notif in ["dunst", "mako", "swaync"]:
        if cmd_exists(notif):
            apps[notif] = {"installed": True, "config_dir": str(HOME / ".config" / notif)}

    for wp in ["awww", "swww", "hyprpaper", "feh", "nitrogen", "azote"]:
        if cmd_exists(wp):
            apps[wp] = {"installed": True, "binary": wp}

    if cmd_exists("picom"):
        apps["picom"] = {"installed": True, "config_dir": str(HOME / ".config" / "picom")}

    if cmd_exists("fastfetch"):
        apps["fastfetch"] = {"installed": True, "config_dir": str(HOME / ".config" / "fastfetch")}

    if cmd_exists("starship"):
        apps["starship"] = {"installed": True, "config": str(HOME / ".config" / "starship.toml")}

    # GTK is always themeable — gsettings or direct settings.ini write
    apps["gtk"] = {"installed": True}

    # KDE sub-systems — always present when KDE is detected.
    if "kde" in apps:
        apps["kvantum"]        = {"installed": True}
        apps["plasma_theme"]   = {"installed": True}
        apps["cursor"]         = {"installed": True}
        apps["icon_theme"]     = {"installed": True}
        apps["kde_lockscreen"] = {"installed": True}
        apps["lnf"]            = {"installed": True}

    # Hyprland sub-system — register when hyprctl is present.
    if cmd_exists("hyprctl"):
        apps["hyprland"] = {"installed": True}
        apps["hyprlock"] = {"installed": True, "config_dir": str(HOME / ".config" / "hypr")}

    # GNOME sub-systems — only register when gnome-shell is actually installed OR
    # XDG_CURRENT_DESKTOP confirms a GNOME session.  gsettings is intentionally
    # excluded: it ships as a GLib/GIO dependency on many non-GNOME systems
    # (e.g. KDE Plasma on Arch) and would cause GNOME materializers to run
    # spuriously on those machines.
    if cmd_exists("gnome-shell") or "gnome" in _xdg:
        apps["gnome_shell"]      = {"installed": True,
                                    "theme_dir": str(HOME / ".local" / "share" / "themes")}
        apps["gnome_lockscreen"] = {"installed": True}

    return apps


def discover() -> dict[str, Any]:
    """Full system discovery: desktop + apps."""
    return {
        "desktop": discover_desktop(),
        "apps": discover_apps(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
