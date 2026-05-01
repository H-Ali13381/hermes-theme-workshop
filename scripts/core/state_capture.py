"""core/state_capture.py — KDE/GTK desktop state capture functions.

Extracted from scripts/desktop_state_audit.py to keep that file within the
300-line budget.  All functions are read-only with respect to the live desktop.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from core.audit_utils import run_cmd, cmd_exists, kread, read_ini_key, copy_to_baseline

HOME = Path.home()


# =============================================================================
# KDE STATE CAPTURE
# =============================================================================

def capture_kde_colorscheme() -> dict[str, Any]:
    """Capture the active KDE colorscheme."""
    scheme = kread("General", "ColorScheme", "kdeglobals")
    colors_file = None
    if scheme:
        for d in [
            HOME / ".local" / "share" / "color-schemes",
            Path("/usr/share/color-schemes"),
        ]:
            candidate = d / f"{scheme}.colors"
            if candidate.exists():
                colors_file = str(candidate)
                break
    return {
        "active_scheme": scheme,
        "colors_file_path": colors_file,
        "colors_file_exists": Path(colors_file).exists() if colors_file else False,
    }


def capture_kde_wallpaper() -> dict[str, Any]:
    """Capture the current wallpaper settings from plasma-org.kde.plasma.desktop-appletsrc."""
    appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
    if not appletsrc.exists():
        return {"error": "appletsrc not found"}

    text = appletsrc.read_text(encoding="utf-8", errors="replace")
    plugin = image = fill_mode = blur = None

    for m in re.finditer(r"^\[Containments\]\[(\d+)\]\[Wallpaper\]\[(.+?)\]\[General\]\s*$", text, re.MULTILINE):
        start = m.end()
        next_section = re.search(r"^\[", text[start:], re.MULTILINE)
        section_text = text[start:start + next_section.start()] if next_section else text[start:]

        img_match = re.search(r"^Image\s*=\s*(.+)$", section_text, re.MULTILINE)
        if img_match:
            image = img_match.group(1).strip()
            plugin = m.group(2)
        fill_match = re.search(r"^FillMode\s*=\s*(.+)$", section_text, re.MULTILINE)
        if fill_match:
            fill_mode = fill_match.group(1).strip()
        blur_match = re.search(r"^Blur\s*=\s*(.+)$", section_text, re.MULTILINE)
        if blur_match:
            blur = blur_match.group(1).strip()

    return {"plugin": plugin, "image_path": image, "fill_mode": fill_mode,
            "blur": blur, "appletsrc_path": str(appletsrc)}


def capture_kde_plasma_theme() -> dict[str, Any]:
    """Capture the active Plasma theme (panel, tasks, dialogs)."""
    theme = kread("Theme", "name", "plasmarc")
    theme_dir = None
    if theme:
        for d in [
            HOME / ".local" / "share" / "plasma" / "desktoptheme" / theme,
            Path("/usr/share/plasma/desktoptheme") / theme,
        ]:
            if d.exists():
                theme_dir = str(d)
                break
    return {"active_theme": theme, "theme_dir": theme_dir,
            "theme_dir_exists": Path(theme_dir).exists() if theme_dir else False}


def capture_kvantum_state() -> dict[str, Any]:
    """Capture the active Kvantum widget style."""
    kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
    widget_style = kread("KDE", "widgetStyle", "kdeglobals")
    kvantum_theme = None
    if kvantum_config.exists():
        kv_text = kvantum_config.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^theme\s*=\s*(.+)$", kv_text, re.MULTILINE | re.IGNORECASE)
        if m:
            kvantum_theme = m.group(1).strip()
    return {"widget_style": widget_style, "kvantum_config_path": str(kvantum_config),
            "kvantum_theme": kvantum_theme, "kvantum_config_exists": kvantum_config.exists()}


def capture_cursor_theme() -> dict[str, Any]:
    """Capture the active cursor theme."""
    return {"active_cursor": kread("Mouse", "cursorTheme", "kcminputrc")}


def capture_icon_theme() -> dict[str, Any]:
    """Capture the active icon theme."""
    return {"active_icon_theme": kread("General", "Theme", "kdeglobals")}



def capture_gtk_theme() -> dict[str, Any]:
    """Capture GTK theme if gtkrc or gsettings available."""
    gtk2_rc = HOME / ".gtkrc-2.0"
    gtk3_settings = HOME / ".config" / "gtk-3.0" / "settings.ini"
    gtk_theme = None

    if gtk3_settings.exists():
        gtk_theme = read_ini_key(gtk3_settings, "Settings", "gtk-theme-name")
    if not gtk_theme and gtk2_rc.exists():
        text = gtk2_rc.read_text(encoding="utf-8", errors="replace")
        m = re.search(r'gtk-theme-name\s*=\s*"?(.+?)"?\s*$', text, re.MULTILINE)
        if m:
            gtk_theme = m.group(1).strip()
    if not gtk_theme and cmd_exists("gsettings"):
        rc, out, _ = run_cmd(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"])
        if rc == 0:
            gtk_theme = out.strip().strip("'")

    return {"gtk_theme": gtk_theme, "gtk2_rc_exists": gtk2_rc.exists(),
            "gtk3_settings_exists": gtk3_settings.exists()}


def capture_splash_screen() -> dict[str, Any]:
    """Capture the active splash screen theme."""
    return {"active_splash": kread("KSplash", "Theme", "ksplashrc"),
            "engine": kread("KSplash", "Engine", "ksplashrc")}


def capture_konsole_state() -> dict[str, Any]:
    """Capture the active Konsole default profile."""
    profile = None
    konsolerc = HOME / ".config" / "konsolerc"
    if konsolerc.exists():
        profile = read_ini_key(konsolerc, "Desktop Entry", "DefaultProfile")
        if not profile:
            text = konsolerc.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"DefaultProfile\s*=\s*(.+)", text)
            if m:
                profile = m.group(1).strip()

    profiles_dir = HOME / ".local" / "share" / "konsole"
    profiles = []
    if profiles_dir.exists():
        profiles = [f.name for f in profiles_dir.iterdir() if f.suffix == ".profile"]

    return {"default_profile": profile, "all_profiles": profiles,
            "profiles_dir": str(profiles_dir)}


def capture_panel_config() -> dict[str, Any]:
    """Capture the panel/widget configuration from appletsrc."""
    appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
    if not appletsrc.exists():
        return {"error": "appletsrc not found"}

    text = appletsrc.read_text(encoding="utf-8", errors="replace")
    panels = []
    for m in re.finditer(r"^\[Containments\]\[(\d+)\]\s*$", text, re.MULTILINE):
        cid = m.group(1)
        start = m.end()
        next_section = re.search(r"^\[", text[start:], re.MULTILINE)
        section_text = text[start:start + next_section.start()] if next_section else text[start:]

        plugin_match = re.search(r"^plugin\s*=\s*(.+)$", section_text, re.MULTILINE)
        if plugin_match:
            plugin = plugin_match.group(1).strip()
            if "panel" in plugin.lower():
                applets = []
                applet_pattern = re.compile(
                    rf"^\[Containments\]\[{re.escape(cid)}\]\[Applets\]\[(\d+)\]\s*$",
                    re.MULTILINE
                )
                for am in applet_pattern.finditer(text):
                    aid = am.group(1)
                    astart = am.end()
                    anext = re.search(r"^\[", text[astart:], re.MULTILINE)
                    asection = text[astart:astart + anext.start()] if anext else text[astart:]
                    aplugin_match = re.search(r"^plugin\s*=\s*(.+)$", asection, re.MULTILINE)
                    if aplugin_match:
                        applets.append({"applet_id": aid, "plugin": aplugin_match.group(1).strip()})
                panels.append({"containment_id": cid, "plugin": plugin, "applets": applets})

    return {"panels": panels, "appletsrc_path": str(appletsrc),
            "appletsrc_size_bytes": appletsrc.stat().st_size if appletsrc.exists() else 0}


# =============================================================================
# CONFIG FILE BACKUP
# =============================================================================

def backup_all_config_files(baseline_dir: Path) -> dict[str, str | None]:
    """Back up all relevant config files and dirs to the baseline."""
    files_to_backup = {
        "kdeglobals": HOME / ".config" / "kdeglobals",
        "kcmfonts": HOME / ".config" / "kcmfonts",
        "kcminputrc": HOME / ".config" / "kcminputrc",
        "konsolerc": HOME / ".config" / "konsolerc",
        "ksplashrc": HOME / ".config" / "ksplashrc",
        "plasmarc": HOME / ".config" / "plasmarc",
        "plasma-org.kde.plasma.desktop-appletsrc": HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc",
        "kvantum.kvconfig": HOME / ".config" / "Kvantum" / "kvantum.kvconfig",
        "gtkrc-2.0": HOME / ".gtkrc-2.0",
        "gtk-3.0-settings": HOME / ".config" / "gtk-3.0" / "settings.ini",
        "gtk-4.0-settings": HOME / ".config" / "gtk-4.0" / "settings.ini",
        "kitty.conf": HOME / ".config" / "kitty" / "kitty.conf",
        "fastfetch.config.json": HOME / ".config" / "fastfetch" / "config.json",
        "fastfetch.config.jsonc": HOME / ".config" / "fastfetch" / "config.jsonc",
        "fastfetch.logo.txt": HOME / ".config" / "fastfetch" / "logo.txt",
        "dunstrc": HOME / ".config" / "dunst" / "dunstrc",
        "rofi.config.rasi": HOME / ".config" / "rofi" / "config.rasi",
        "waybar.style.css": HOME / ".config" / "waybar" / "style.css",
        "starship.toml": HOME / ".config" / "starship.toml",
        "bashrc": HOME / ".bashrc",
        "zshrc": HOME / ".zshrc",
        "fish.config.fish": HOME / ".config" / "fish" / "config.fish",
        "konsole_profiles": HOME / ".local" / "share" / "konsole",
        "color-schemes": HOME / ".local" / "share" / "color-schemes",
    }
    backed = {}
    for label, path in files_to_backup.items():
        backed[label] = copy_to_baseline(path, baseline_dir, label)
    return backed
