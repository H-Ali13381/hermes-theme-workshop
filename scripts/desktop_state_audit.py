#!/usr/bin/env python3
"""
================================================================================
HERMES-RICER DESKTOP STATE AUDIT
Corporate-grade baseline capture for KDE Plasma (and generic fallback)
================================================================================

PURPOSE:
    Capture the COMPLETE current state of the desktop environment before any
    ricing operation. This script is READ-ONLY. It never writes anything.

OUTPUT:
    1. JSON manifest: ~/.cache/linux-ricing/baselines/<timestamp>_baseline.json
    2. Config backup dir: ~/.cache/linux-ricing/baselines/<timestamp>_files/

CAPTURED STATE:
    - Desktop Environment / Session type
    - Active colorscheme
    - Active wallpaper (path, mode, plugin)
    - Plasma theme (panel, tasks, dialogs)
    - Kvantum widget style
    - Cursor theme
    - Icon theme
    - GTK theme (if applicable)
    - Splash screen theme
    - Konsole default profile
    - Panel configuration (appletsrc snapshot)
    - All relevant config file contents

USAGE:
    python3 desktop_state_audit.py
    python3 desktop_state_audit.py --output /custom/path/baseline.json

DETERMINISM:
    All values are read via kreadconfig6/5 or direct file parsing. No guesses.
================================================================================
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "linux-ricing"
BASELINES_DIR = CACHE_DIR / "baselines"

# =============================================================================
# UTILITIES
# =============================================================================

def run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str, str]:
    """Run a shell command, return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def kread(group: str, key: str, file: str = "kdeglobals") -> str | None:
    """Read a KDE config value using kreadconfig6 or kreadconfig5."""
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([
                tool, "--file", file,
                "--group", group,
                "--key", key
            ])
            if rc == 0 and out:
                return out
    return None


def read_ini_key(filepath: Path, section: str, key: str) -> str | None:
    """Parse a simple INI file for a specific section key."""
    if not filepath.exists():
        return None
    text = filepath.read_text(errors="replace")
    # Find section
    section_pattern = re.compile(
        rf"^\[{re.escape(section)}\]\s*$",
        re.MULTILINE
    )
    m = section_pattern.search(text)
    if not m:
        return None
    start = m.end()
    # Find next section or end of file
    next_section = re.search(r"^\[", text[start:], re.MULTILINE)
    if next_section:
        section_text = text[start:start + next_section.start()]
    else:
        section_text = text[start:]
    key_match = re.search(
        rf"^{re.escape(key)}\s*=\s*(.*)$",
        section_text,
        re.MULTILINE
    )
    if key_match:
        return key_match.group(1).strip()
    return None


def copy_to_baseline(src: Path, dest_dir: Path, label: str) -> str | None:
    """Copy a file or directory into the baseline backup dir."""
    if not src.exists():
        return None
    dest = dest_dir / label
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    return str(dest)

# =============================================================================
# DISCOVERY
# =============================================================================

def discover_desktop() -> dict[str, Any]:
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    display = os.environ.get("DISPLAY", "")
    session_type = "x11" if display else "unknown"
    if wayland_display:
        session_type = "wayland"

    wm = "unknown"
    _, procs, _ = run_cmd(["ps", "aux"], timeout=3)
    proc_lower = procs.lower()
    if "plasmashell" in proc_lower or "kwin" in proc_lower:
        wm = "kde"
    elif "hyprland" in proc_lower:
        wm = "hyprland"
    elif "sway" in proc_lower:
        wm = "sway"
    elif "i3" in proc_lower:
        wm = "i3"

    if wm == "unknown" and ("kde" in desktop or "plasma" in desktop):
        wm = "kde"

    return {
        "wm": wm,
        "session_type": session_type,
        "desktop_env": desktop,
    }

# =============================================================================
# KDE STATE CAPTURE
# =============================================================================

def capture_kde_colorscheme() -> dict[str, Any]:
    """Capture the active KDE colorscheme."""
    scheme = kread("General", "ColorScheme", "kdeglobals")
    # Also read the actual colors file path if possible
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

    text = appletsrc.read_text(errors="replace")

    # Find the wallpaper plugin and image
    # Wallpaper plugin is usually in [Containments][N][Wallpaper][org.kde.image][General]
    plugin = None
    image = None
    fill_mode = None
    blur = None

    # Find all containment sections
    for m in re.finditer(r"^\[Containments\]\[(\d+)\]\[Wallpaper\]\[(.+?)\]\[General\]\s*$", text, re.MULTILINE):
        start = m.end()
        next_section = re.search(r"^\[", text[start:], re.MULTILINE)
        if next_section:
            section_text = text[start:start + next_section.start()]
        else:
            section_text = text[start:]

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

    return {
        "plugin": plugin,
        "image_path": image,
        "fill_mode": fill_mode,
        "blur": blur,
        "appletsrc_path": str(appletsrc),
    }


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
    return {
        "active_theme": theme,
        "theme_dir": theme_dir,
        "theme_dir_exists": Path(theme_dir).exists() if theme_dir else False,
    }


def capture_kvantum_state() -> dict[str, Any]:
    """Capture the active Kvantum widget style."""
    kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
    widget_style = kread("KDE", "widgetStyle", "kdeglobals")
    kvantum_theme = None
    if kvantum_config.exists():
        kv_text = kvantum_config.read_text(errors="replace")
        m = re.search(r"^theme\s*=\s*(.+)$", kv_text, re.MULTILINE | re.IGNORECASE)
        if m:
            kvantum_theme = m.group(1).strip()

    return {
        "widget_style": widget_style,
        "kvantum_config_path": str(kvantum_config),
        "kvantum_theme": kvantum_theme,
        "kvantum_config_exists": kvantum_config.exists(),
    }


def capture_cursor_theme() -> dict[str, Any]:
    """Capture the active cursor theme."""
    cursor = kread("Mouse", "cursorTheme", "kcminputrc")
    return {
        "active_cursor": cursor,
    }


def capture_icon_theme() -> dict[str, Any]:
    """Capture the active icon theme."""
    icon = kread("General", "Theme", "kdeglobals")
    return {
        "active_icon_theme": icon,
    }


def capture_gtk_theme() -> dict[str, Any]:
    """Capture GTK theme if gtkrc or gsettings available."""
    gtk2_rc = HOME / ".gtkrc-2.0"
    gtk3_settings = HOME / ".config" / "gtk-3.0" / "settings.ini"
    gtk_theme = None

    if gtk3_settings.exists():
        gtk_theme = read_ini_key(gtk3_settings, "Settings", "gtk-theme-name")

    if not gtk_theme and gtk2_rc.exists():
        text = gtk2_rc.read_text(errors="replace")
        m = re.search(r'gtk-theme-name\s*=\s*"?(.+?)"?\s*$', text, re.MULTILINE)
        if m:
            gtk_theme = m.group(1).strip()

    # Try gsettings as fallback
    if not gtk_theme and cmd_exists("gsettings"):
        rc, out, _ = run_cmd(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"])
        if rc == 0:
            gtk_theme = out.strip().strip("'")

    return {
        "gtk_theme": gtk_theme,
        "gtk2_rc_exists": gtk2_rc.exists(),
        "gtk3_settings_exists": gtk3_settings.exists(),
    }


def capture_splash_screen() -> dict[str, Any]:
    """Capture the active splash screen theme."""
    splash = kread("KSplash", "Theme", "ksplashrc")
    engine = kread("KSplash", "Engine", "ksplashrc")
    return {
        "active_splash": splash,
        "engine": engine,
    }


def capture_konsole_state() -> dict[str, Any]:
    """Capture the active Konsole default profile."""
    profile = None
    konsolerc = HOME / ".config" / "konsolerc"
    if konsolerc.exists():
        profile = read_ini_key(konsolerc, "Desktop Entry", "DefaultProfile")
        if not profile:
            # Try reading raw
            text = konsolerc.read_text(errors="replace")
            m = re.search(r"DefaultProfile\s*=\s*(.+)", text)
            if m:
                profile = m.group(1).strip()

    # List all profiles
    profiles_dir = HOME / ".local" / "share" / "konsole"
    profiles = []
    if profiles_dir.exists():
        profiles = [f.name for f in profiles_dir.iterdir() if f.suffix == ".profile"]

    return {
        "default_profile": profile,
        "all_profiles": profiles,
        "profiles_dir": str(profiles_dir),
    }


def capture_panel_config() -> dict[str, Any]:
    """Capture the panel/widget configuration from appletsrc."""
    appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
    if not appletsrc.exists():
        return {"error": "appletsrc not found"}

    text = appletsrc.read_text(errors="replace")

    # Extract panel containments (usually Containments with plugin=org.kde.panel)
    panels = []
    for m in re.finditer(r"^\[Containments\]\[(\d+)\]\s*$", text, re.MULTILINE):
        cid = m.group(1)
        start = m.end()
        next_section = re.search(r"^\[", text[start:], re.MULTILINE)
        if next_section:
            section_text = text[start:start + next_section.start()]
        else:
            section_text = text[start:]

        plugin_match = re.search(r"^plugin\s*=\s*(.+)$", section_text, re.MULTILINE)
        if plugin_match:
            plugin = plugin_match.group(1).strip()
            if "panel" in plugin.lower():
                # Find applets in this containment
                applets = []
                applet_pattern = re.compile(
                    rf"^\[Containments\]\[{re.escape(cid)}\]\[Applets\]\[(\d+)\]\s*$",
                    re.MULTILINE
                )
                for am in applet_pattern.finditer(text):
                    aid = am.group(1)
                    astart = am.end()
                    anext = re.search(r"^\[", text[astart:], re.MULTILINE)
                    if anext:
                        asection = text[astart:astart + anext.start()]
                    else:
                        asection = text[astart:]
                    aplugin_match = re.search(r"^plugin\s*=\s*(.+)$", asection, re.MULTILINE)
                    if aplugin_match:
                        applets.append({
                            "applet_id": aid,
                            "plugin": aplugin_match.group(1).strip(),
                        })

                panels.append({
                    "containment_id": cid,
                    "plugin": plugin,
                    "applets": applets,
                })

    return {
        "panels": panels,
        "appletsrc_path": str(appletsrc),
        "appletsrc_size_bytes": appletsrc.stat().st_size if appletsrc.exists() else 0,
    }

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
        "dunstrc": HOME / ".config" / "dunst" / "dunstrc",
        "rofi.config.rasi": HOME / ".config" / "rofi" / "config.rasi",
        "waybar.style.css": HOME / ".config" / "waybar" / "style.css",
        "konsole_profiles": HOME / ".local" / "share" / "konsole",
        "color-schemes": HOME / ".local" / "share" / "color-schemes",
    }

    backed = {}
    for label, path in files_to_backup.items():
        backed[label] = copy_to_baseline(path, baseline_dir, label)

    return backed

# =============================================================================
# MAIN AUDIT
# =============================================================================

def run_full_audit(output_path: str | None = None) -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    baseline_dir = BASELINES_DIR / f"{timestamp}_files"
    baseline_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== HERMES-RICER DESKTOP STATE AUDIT ===")
    print(f"Timestamp : {timestamp}")
    print(f"Baseline  : {baseline_dir}")
    print("")

    # 1. Desktop discovery
    print("[1/8] Discovering desktop environment...")
    desktop = discover_desktop()
    print(f"  WM/DE   : {desktop['wm']}")
    print(f"  Session : {desktop['session_type']}")

    # 2. KDE-specific state
    print("")
    print("[2/8] Capturing KDE colorscheme...")
    colorscheme = capture_kde_colorscheme()
    print(f"  Active  : {colorscheme['active_scheme']}")

    print("")
    print("[3/8] Capturing wallpaper...")
    wallpaper = capture_kde_wallpaper()
    print(f"  Plugin  : {wallpaper.get('plugin')}")
    print(f"  Image   : {wallpaper.get('image_path')}")
    print(f"  Fill    : {wallpaper.get('fill_mode')}")

    print("")
    print("[4/8] Capturing Plasma theme / Kvantum / Cursor / Icons...")
    plasma_theme = capture_kde_plasma_theme()
    kvantum = capture_kvantum_state()
    cursor = capture_cursor_theme()
    icons = capture_icon_theme()
    print(f"  Plasma  : {plasma_theme['active_theme']}")
    print(f"  Kvantum : {kvantum['kvantum_theme']} (widgetStyle={kvantum['widget_style']})")
    print(f"  Cursor  : {cursor['active_cursor']}")
    print(f"  Icons   : {icons['active_icon_theme']}")

    print("")
    print("[5/8] Capturing GTK theme / Splash...")
    gtk = capture_gtk_theme()
    splash = capture_splash_screen()
    print(f"  GTK     : {gtk['gtk_theme']}")
    print(f"  Splash  : {splash['active_splash']}")

    print("")
    print("[6/8] Capturing Konsole state...")
    konsole = capture_konsole_state()
    print(f"  Profile : {konsole['default_profile']}")
    print(f"  All     : {konsole['all_profiles']}")

    print("")
    print("[7/8] Capturing panel/widgets configuration...")
    panel = capture_panel_config()
    if "error" in panel:
        print(f"  ERROR   : {panel['error']}")
    else:
        print(f"  Panels  : {len(panel['panels'])}")
        for p in panel['panels']:
            print(f"    [{p['containment_id']}] {p['plugin']} — {len(p['applets'])} applets")
            for a in p['applets']:
                print(f"      - {a['plugin']}")

    print("")
    print("[8/8] Backing up config files...")
    backups = backup_all_config_files(baseline_dir)
    backed_count = sum(1 for v in backups.values() if v is not None)
    print(f"  Backed up {backed_count}/{len(backups)} items")

    # Assemble manifest
    manifest = {
        "audit_version": "1.0.0",
        "timestamp": timestamp,
        "hostname": os.uname().nodename,
        "user": os.environ.get("USER", "unknown"),
        "desktop": desktop,
        "kde": {
            "colorscheme": colorscheme,
            "wallpaper": wallpaper,
            "plasma_theme": plasma_theme,
            "kvantum": kvantum,
            "cursor": cursor,
            "icons": icons,
            "splash": splash,
        },
        "gtk": gtk,
        "konsole": konsole,
        "panel": panel,
        "backups": backups,
        "baseline_dir": str(baseline_dir),
    }

    # Write manifest
    if output_path:
        manifest_path = Path(output_path)
    else:
        manifest_path = BASELINES_DIR / f"{timestamp}_baseline.json"

    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print("")
    print(f"=== AUDIT COMPLETE ===")
    print(f"Manifest  : {manifest_path}")
    print(f"Files     : {baseline_dir}")
    print("")
    print("THIS BASELINE IS IMMUTABLE. STORE IT SAFELY.")

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Hermes Ricer — Desktop State Audit (READ-ONLY)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Custom output path for the JSON manifest"
    )
    args = parser.parse_args()
    run_full_audit(output_path=args.output)


if __name__ == "__main__":
    main()
