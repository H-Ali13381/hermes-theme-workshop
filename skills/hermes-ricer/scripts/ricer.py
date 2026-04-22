#!/usr/bin/env python3
"""
Hermes Ricer — AI-Native Desktop Theming Engine
Python driver for config discovery, materialization, and rollback.
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

# Optional Jinja2 import with fallback
jinja2 = None
try:
    import jinja2
except ImportError:
    pass

HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "hermes-ricer"
BACKUP_DIR = CACHE_DIR / "backups"
CURRENT_DIR = CACHE_DIR / "current"
SKILL_DIR = HOME / ".hermes" / "skills" / "creative" / "hermes-ricer"
TEMPLATES_DIR = SKILL_DIR / "templates"

# ---------------------------------------------------------------------------
# DESIGN SYSTEM
# ---------------------------------------------------------------------------

REQUIRED_PALETTE_KEYS = [
    "background", "foreground", "primary", "secondary", "accent",
    "surface", "muted", "danger", "success", "warning",
]

DEFAULT_DESIGN_SYSTEM = {
    "name": "default",
    "description": "A subtle dark theme with blue accents.",
    "palette": {
        "background": "#1e1e2e",
        "foreground": "#cdd6f4",
        "primary": "#89b4fa",
        "secondary": "#f5c2e7",
        "accent": "#fab387",
        "surface": "#313244",
        "muted": "#6c7086",
        "danger": "#f38ba8",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
    },
    "mood_tags": ["dark", "blue", "subtle"],
    "typography": {"monospace": "JetBrainsMono Nerd Font", "ui_font": "Inter"},
}


# ---------------------------------------------------------------------------
# DISCOVERY LAYER
# ---------------------------------------------------------------------------

def run_cmd(cmd: list[str], timeout: int = 5) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def discover_desktop() -> dict[str, Any]:
    """Detect what DE/WM/compositor is running."""
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    display = os.environ.get("DISPLAY", "")

    wm = "unknown"
    session_type = "x11" if display else "unknown"
    if wayland_display:
        session_type = "wayland"

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
    elif "bspwm" in proc_lower:
        wm = "bspwm"
    elif "awesome" in proc_lower:
        wm = "awesome"
    elif "qtile" in proc_lower:
        wm = "qtile"

    if wm == "unknown":
        if "kde" in desktop or "plasma" in desktop:
            wm = "kde"

    return {
        "wm": wm,
        "session_type": session_type,
        "desktop_env": desktop,
    }


def discover_apps() -> dict[str, Any]:
    """Detect installed themable applications and their config paths."""
    apps = {}

    if cmd_exists("plasmashell") or cmd_exists("kwriteconfig6") or cmd_exists("kwriteconfig5"):
        apps["kde"] = {
            "installed": True,
            "config_dir": str(HOME / ".config"),
            "tools": {
                "apply_colorscheme": cmd_exists("plasma-apply-colorscheme"),
                "apply_wallpaper": cmd_exists("plasma-apply-wallpaperimage"),
                "kwriteconfig": "kwriteconfig6" if cmd_exists("kwriteconfig6") else (
                    "kwriteconfig5" if cmd_exists("kwriteconfig5") else None
                ),
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

    for wp in ["swww", "hyprpaper", "feh", "nitrogen", "azote"]:
        if cmd_exists(wp):
            apps[wp] = {"installed": True, "binary": wp}

    if cmd_exists("picom"):
        apps["picom"] = {"installed": True, "config_dir": str(HOME / ".config" / "picom")}

    # KDE sub-systems — always present when KDE is detected.
    # These are tracked as separate materializers but share the KDE prerequisite.
    # CRITICAL: without this block, kvantum/plasma_theme/cursor materializers are
    # never called because the APP_MATERIALIZERS loop checks `if app_name in apps`.
    if "kde" in apps:
        apps["kvantum"] = {"installed": True}
        apps["plasma_theme"] = {"installed": True}
        apps["cursor"] = {"installed": True}

    return apps


def discover() -> dict[str, Any]:
    """Full system discovery."""
    return {
        "desktop": discover_desktop(),
        "apps": discover_apps(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# PRE-FLIGHT SNAPSHOTS — read current state BEFORE touching anything
# ---------------------------------------------------------------------------

def snapshot_kde_state() -> dict[str, str | None]:
    """Read the currently active KDE colorscheme so we can restore it on undo."""
    scheme = None
    lookandfeel = None

    # Try kreadconfig6/5 first (most reliable)
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([
                tool, "--file", "kdeglobals",
                "--group", "General",
                "--key", "ColorScheme"
            ])
            if rc == 0 and out:
                scheme = out
            rc2, out2, _ = run_cmd([
                tool, "--file", "kdeglobals",
                "--group", "KDE",
                "--key", "LookAndFeelPackage"
            ])
            if rc2 == 0 and out2:
                lookandfeel = out2
            if scheme:
                break

    # Fallback: read kdeglobals directly
    if not scheme or not lookandfeel:
        kdeglobals = HOME / ".config" / "kdeglobals"
        if kdeglobals.exists():
            text = kdeglobals.read_text(errors="replace")
            if not scheme:
                m = re.search(r"^\[General\].*?^ColorScheme=(.+)$", text, re.MULTILINE | re.DOTALL)
                if m:
                    scheme = m.group(1).strip()
            if not lookandfeel:
                m = re.search(r"^\[KDE\].*?^LookAndFeelPackage=(.+)$", text, re.MULTILINE | re.DOTALL)
                if m:
                    lookandfeel = m.group(1).strip()

    # Snapshot Kvantum state
    kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
    kvantum_theme = None
    widget_style = None
    if kvantum_config.exists():
        kv_text = kvantum_config.read_text(errors="replace")
        m = re.search(r"^theme\s*=\s*(.+)$", kv_text, re.MULTILINE | re.IGNORECASE)
        if m:
            kvantum_theme = m.group(1).strip()

    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle"])
            if rc == 0 and out:
                widget_style = out
                break

    # Snapshot Plasma theme
    plasma_theme = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "plasmarc", "--group", "Theme", "--key", "name"])
            if rc == 0 and out:
                plasma_theme = out
                break

    # Snapshot cursor
    cursor = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme"])
            if rc == 0 and out:
                cursor = out
                break

    # Snapshot wallpaper
    wallpaper = None
    wallpaper_plugin = None
    appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
    if appletsrc.exists():
        text = appletsrc.read_text(errors="replace")
        m = re.search(r"^Image\s*=\s*(.+)$", text, re.MULTILINE)
        if m:
            wallpaper = m.group(1).strip()
        m = re.search(r"^Wallpaperplugin\s*=\s*(.+)$", text, re.MULTILINE)
        if m:
            wallpaper_plugin = m.group(1).strip()

    return {
        "active_colorscheme": scheme,
        "look_and_feel": lookandfeel,
        "kvantum_theme": kvantum_theme,
        "widget_style": widget_style,
        "plasma_theme": plasma_theme,
        "cursor_theme": cursor,
        "wallpaper": wallpaper,
        "wallpaper_plugin": wallpaper_plugin,
    }


def snapshot_konsole_state() -> dict[str, str | None]:
    """Read the currently active Konsole default profile."""
    profile = None
    konsolerc = HOME / ".config" / "konsolerc"
    if konsolerc.exists():
        text = konsolerc.read_text(errors="replace")
        m = re.search(r"DefaultProfile=(.+)", text)
        if m:
            profile = m.group(1).strip()
    return {"default_profile": profile}


# ---------------------------------------------------------------------------
# BACKUP HELPERS
# ---------------------------------------------------------------------------

def backup_file(src: Path, backup_ts: str, label: str) -> str | None:
    """Copy src to BACKUP_DIR/<backup_ts>/<label>. Returns backup path or None."""
    if not src.exists():
        return None
    dest = BACKUP_DIR / backup_ts / label
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return str(dest)


def backup_dir_tree(src: Path, backup_ts: str, label: str) -> str | None:
    """Copy an entire directory to backup. Returns backup path or None."""
    if not src.exists():
        return None
    dest = BACKUP_DIR / backup_ts / label
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    return str(dest)


# ---------------------------------------------------------------------------
# COLOR UTILITIES
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> str:
    """Convert '#rrggbb' to 'r,g,b' decimal string as KDE .colors expects."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


# ---------------------------------------------------------------------------
# TEMPLATE ENGINE
# ---------------------------------------------------------------------------

def simple_render(template_str: str, context: dict) -> str:
    """Minimal template renderer when Jinja2 is unavailable."""
    result = template_str
    for key, value in context.items():
        result = result.replace(f"{{{key}}}", str(value))
    return result


def render_template(template_path: Path, context: dict) -> str:
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    if jinja2:
        env = jinja2.Environment()
        tmpl = env.from_string(template_str)
        return tmpl.render(**context)
    return simple_render(template_str, context)


# ---------------------------------------------------------------------------
# APP HANDLERS — KDE Plasma
# ---------------------------------------------------------------------------

def materialize_kde(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Materialize a KDE Plasma color scheme. Full pre-flight + undo support."""
    palette = design["palette"]
    changes = []
    colorscheme_name = f"hermes-{design.get('name', 'ricer')}"

    kde_colors_dir = HOME / ".local" / "share" / "color-schemes"
    colorscheme_path = kde_colors_dir / f"{colorscheme_name}.colors"

    # KDE .colors format uses decimal RGB (r,g,b) NOT hex
    p = {k: hex_to_rgb(v) for k, v in palette.items()}

    colorscheme_content = f"""[ColorEffects:Disabled]
Color={p['surface']}
ColorAmount=0.55
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color={p['muted']}
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={p['surface']}
BackgroundNormal={p['surface']}
ForegroundNormal={p['foreground']}
ForegroundInactive={p['muted']}
DecorationFocus={p['primary']}
DecorationHover={p['secondary']}
ForegroundNegative={p['danger']}
ForegroundPositive={p['success']}
ForegroundNeutral={p['warning']}

[Colors:Selection]
BackgroundNormal={p['primary']}
ForegroundNormal={p['background']}
DecorationFocus={p['accent']}
DecorationHover={p['accent']}

[Colors:Tooltip]
BackgroundNormal={p['surface']}
ForegroundNormal={p['foreground']}

[Colors:View]
BackgroundAlternate={p['surface']}
BackgroundNormal={p['background']}
ForegroundNormal={p['foreground']}
ForegroundInactive={p['muted']}
ForegroundNegative={p['danger']}
ForegroundPositive={p['success']}
ForegroundNeutral={p['warning']}
DecorationFocus={p['primary']}
DecorationHover={p['secondary']}

[Colors:Window]
BackgroundNormal={p['background']}
BackgroundAlternate={p['surface']}
ForegroundNormal={p['foreground']}
ForegroundInactive={p['muted']}
ForegroundNegative={p['danger']}
ForegroundPositive={p['success']}
ForegroundNeutral={p['warning']}
DecorationFocus={p['primary']}
DecorationHover={p['secondary']}

[Colors:Complementary]
BackgroundNormal={p['surface']}
ForegroundNormal={p['foreground']}
DecorationFocus={p['accent']}

[Colors:Header]
BackgroundNormal={p['background']}
ForegroundNormal={p['foreground']}
DecorationFocus={p['primary']}

[General]
ColorScheme={colorscheme_name}
Name={colorscheme_name}
shadeSortColumn=true

[WM]
activeBackground={p['background']}
activeForeground={p['foreground']}
inactiveBackground={p['surface']}
inactiveForeground={p['muted']}
activeBlend={p['primary']}
inactiveBlend={p['surface']}
"""

    if dry_run:
        state = snapshot_kde_state()
        changes.append({
            "app": "kde",
            "action": "dry-run",
            "path": str(colorscheme_path),
            "previous_colorscheme": state["active_colorscheme"],
            "description": f"Would write KDE colorscheme {colorscheme_name} and apply it",
        })
        return changes

    # --- Pre-flight: snapshot current state ---
    state = snapshot_kde_state()
    prev_scheme = state["active_colorscheme"]

    # Backup existing .colors file if present (overwrite protection)
    existing_backup = backup_file(colorscheme_path, backup_ts, f"kde/{colorscheme_name}.colors")

    # Write new colorscheme file
    kde_colors_dir.mkdir(parents=True, exist_ok=True)
    colorscheme_path.write_text(colorscheme_content, encoding="utf-8")
    changes.append({
        "app": "kde",
        "action": "write",
        "path": str(colorscheme_path),
        "backup": existing_backup,
        "previous_colorscheme": prev_scheme,
    })

    # Apply via plasma-apply-colorscheme
    if cmd_exists("plasma-apply-colorscheme"):
        rc, out, err = run_cmd(["plasma-apply-colorscheme", colorscheme_name], timeout=10)
        changes.append({
            "app": "kde",
            "action": "reload",
            "command": f"plasma-apply-colorscheme {colorscheme_name}",
            "exit_code": rc,
            "previous_colorscheme": prev_scheme,
        })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — kitty
# ---------------------------------------------------------------------------

def materialize_kitty(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    palette = design["palette"]
    kitty_dir = HOME / ".config" / "kitty"
    theme_path = kitty_dir / "theme.conf"
    main_config = kitty_dir / "kitty.conf"
    changes = []

    content = f"""# Generated by hermes-ricer — {design.get('name', 'theme')}
background {palette['background']}
foreground {palette['foreground']}
cursor {palette['accent']}
cursor_text_color {palette['background']}
selection_background {palette['primary']}
selection_foreground {palette['background']}
color0 {palette['surface']}
color1 {palette['danger']}
color2 {palette['success']}
color3 {palette['warning']}
color4 {palette['primary']}
color5 {palette['secondary']}
color6 {palette['accent']}
color7 {palette['foreground']}
color8 {palette['muted']}
"""

    if dry_run:
        changes.append({"app": "kitty", "action": "dry-run", "path": str(theme_path)})
        return changes

    kitty_dir.mkdir(parents=True, exist_ok=True)

    # Backup BOTH the theme file and the main config (we may append to it)
    theme_backup = backup_file(theme_path, backup_ts, "kitty/theme.conf")
    main_backup = backup_file(main_config, backup_ts, "kitty/kitty.conf")

    theme_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "kitty",
        "action": "write",
        "path": str(theme_path),
        "backup": theme_backup,
    })

    # Inject include line into kitty.conf if not already present
    include_line = "include theme.conf"
    hermes_marker = "# hermes-ricer"
    include_injected = False

    if main_config.exists():
        conf_text = main_config.read_text(encoding="utf-8")
        if include_line not in conf_text:
            main_config.write_text(
                conf_text + f"\n{hermes_marker}\n{include_line}\n",
                encoding="utf-8"
            )
            include_injected = True
    else:
        main_config.write_text(f"{hermes_marker}\n{include_line}\n", encoding="utf-8")
        include_injected = True

    changes.append({
        "app": "kitty",
        "action": "inject_include",
        "path": str(main_config),
        "backup": main_backup,
        "injected": include_injected,
        "include_line": include_line,
        "marker": hermes_marker,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — Konsole (KDE terminal)
# ---------------------------------------------------------------------------

def materialize_konsole(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    palette = design["palette"]
    konsole_dir = HOME / ".local" / "share" / "konsole"
    colors_dir = HOME / ".local" / "share" / "konsole"
    profile_name = "hermes-ricer"
    profile_path = konsole_dir / f"{profile_name}.profile"
    color_scheme_name = f"hermes-{design.get('name', 'ricer')}"
    color_scheme_path = colors_dir / f"{color_scheme_name}.colorscheme"
    konsolerc = HOME / ".config" / "konsolerc"
    changes = []

    # Konsole .colorscheme also uses decimal RGB
    p = {k: hex_to_rgb(v) for k, v in palette.items()}

    color_scheme_content = f"""[Background]
Color={p['background']}

[BackgroundIntense]
Color={p['surface']}

[Foreground]
Color={p['foreground']}

[ForegroundIntense]
Color={p['foreground']}
Bold=true

[General]
Anchor=0.5,0.5
Blur=false
ColorRandomization=false
Description={color_scheme_name}
FillStyle=Tile
Opacity=1
Wallpaper=
WallpaperFlipType=NoFlip
WallpaperOpacity=1

[Color0]
Color={p['surface']}

[Color0Intense]
Color={p['muted']}

[Color1]
Color={p['danger']}

[Color1Intense]
Color={p['danger']}

[Color2]
Color={p['success']}

[Color2Intense]
Color={p['success']}

[Color3]
Color={p['warning']}

[Color3Intense]
Color={p['warning']}

[Color4]
Color={p['primary']}

[Color4Intense]
Color={p['primary']}

[Color5]
Color={p['secondary']}

[Color5Intense]
Color={p['secondary']}

[Color6]
Color={p['accent']}

[Color6Intense]
Color={p['accent']}

[Color7]
Color={p['foreground']}

[Color7Intense]
Color={p['foreground']}
"""

    profile_content = f"""[Appearance]
ColorScheme={color_scheme_name}
Font=JetBrains Mono,11,-1,5,50,0,0,0,0,0

[General]
Name={profile_name}
Parent=FALLBACK/
"""

    if dry_run:
        state = snapshot_konsole_state()
        changes.append({
            "app": "konsole",
            "action": "dry-run",
            "profile_path": str(profile_path),
            "previous_profile": state["default_profile"],
        })
        return changes

    # Pre-flight snapshot
    state = snapshot_konsole_state()
    prev_profile = state["default_profile"]

    # Backup existing files
    profile_backup = backup_file(profile_path, backup_ts, f"konsole/{profile_name}.profile")
    colors_backup = backup_file(color_scheme_path, backup_ts, f"konsole/{color_scheme_name}.colorscheme")
    konsolerc_backup = backup_file(konsolerc, backup_ts, "konsole/konsolerc")

    konsole_dir.mkdir(parents=True, exist_ok=True)
    color_scheme_path.write_text(color_scheme_content, encoding="utf-8")
    profile_path.write_text(profile_content, encoding="utf-8")

    # Activate as default profile in konsolerc.
    # The key is DefaultProfile under [Desktop Entry] — verified against konsolerc format.
    kwrite = "kwriteconfig6" if cmd_exists("kwriteconfig6") else ("kwriteconfig5" if cmd_exists("kwriteconfig5") else None)
    if kwrite:
        run_cmd([kwrite, "--file", "konsolerc", "--group", "Desktop Entry",
                 "--key", "DefaultProfile", f"{profile_name}.profile"])

    changes.append({
        "app": "konsole",
        "action": "write",
        "profile_path": str(profile_path),
        "color_scheme_path": str(color_scheme_path),
        "backup_profile": profile_backup,
        "backup_colors": colors_backup,
        "backup_konsolerc": konsolerc_backup,
        "previous_profile": prev_profile,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — waybar
# ---------------------------------------------------------------------------

def materialize_waybar(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    palette = design["palette"]
    waybar_dir = HOME / ".config" / "waybar"
    style_path = waybar_dir / "style-hermes.css"
    config_path = waybar_dir / "config"
    changes = []

    content = f"""/* Generated by hermes-ricer — {design.get('name', 'theme')} */
* {{
    font-family: "{design.get('typography', {}).get('ui_font', 'Inter')}", sans-serif;
    font-size: 14px;
}}

window#waybar {{
    background-color: {palette['background']};
    color: {palette['foreground']};
    border-bottom: 2px solid {palette['primary']};
}}

#workspaces button {{
    color: {palette['muted']};
    padding: 0 5px;
}}

#workspaces button.focused {{
    background-color: {palette['primary']};
    color: {palette['background']};
}}

#clock, #battery, #network, #pulseaudio {{
    padding: 0 10px;
    color: {palette['foreground']};
}}

#battery.warning {{
    color: {palette['warning']};
}}

#battery.critical {{
    color: {palette['danger']};
}}
"""

    if dry_run:
        changes.append({"app": "waybar", "action": "dry-run", "path": str(style_path)})
        return changes

    waybar_dir.mkdir(parents=True, exist_ok=True)

    style_backup = backup_file(style_path, backup_ts, "waybar/style-hermes.css")
    config_backup = backup_file(config_path, backup_ts, "waybar/config")

    style_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "waybar",
        "action": "write",
        "path": str(style_path),
        "backup": style_backup,
        "config_backup": config_backup,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — rofi
# ---------------------------------------------------------------------------

def materialize_rofi(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    palette = design["palette"]
    rofi_dir = HOME / ".config" / "rofi"
    theme_path = rofi_dir / "hermes-theme.rasi"
    config_path = rofi_dir / "config.rasi"
    changes = []

    content = f"""/* Generated by hermes-ricer — {design.get('name', 'theme')} */
* {{
    background: {palette['background']};
    foreground: {palette['foreground']};
    primary: {palette['primary']};
    accent: {palette['accent']};
    surface: {palette['surface']};
    muted: {palette['muted']};
}}

window {{
    background-color: @background;
    border: 2px;
    border-color: @primary;
    padding: 20px;
    border-radius: 8px;
}}

inputbar {{
    background-color: @surface;
    children: [prompt, entry];
    border-radius: 4px;
    padding: 4px;
}}

listview {{
    background-color: @background;
}}

element selected {{
    background-color: @primary;
    text-color: @background;
}}
"""

    if dry_run:
        changes.append({"app": "rofi", "action": "dry-run", "path": str(theme_path)})
        return changes

    rofi_dir.mkdir(parents=True, exist_ok=True)

    theme_backup = backup_file(theme_path, backup_ts, "rofi/hermes-theme.rasi")
    config_backup = backup_file(config_path, backup_ts, "rofi/config.rasi")

    theme_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "rofi",
        "action": "write",
        "path": str(theme_path),
        "backup": theme_backup,
    })

    # Inject @theme reference into config.rasi
    theme_ref = f'@theme "{theme_path}"'
    hermes_marker = "/* hermes-ricer */"
    injected = False

    if config_path.exists():
        conf_text = config_path.read_text(encoding="utf-8")
        if str(theme_path) not in conf_text:
            config_path.write_text(
                conf_text + f"\n{hermes_marker}\n{theme_ref}\n",
                encoding="utf-8"
            )
            injected = True
    else:
        config_path.write_text(f"{hermes_marker}\n{theme_ref}\n", encoding="utf-8")
        injected = True

    changes.append({
        "app": "rofi",
        "action": "inject_theme",
        "path": str(config_path),
        "backup": config_backup,
        "injected": injected,
        "theme_ref": theme_ref,
        "marker": hermes_marker,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — dunst
# ---------------------------------------------------------------------------

def materialize_dunst(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    palette = design["palette"]
    dunst_dir = HOME / ".config" / "dunst"
    dunstrc = dunst_dir / "dunstrc"
    fragment_path = dunst_dir / "hermes-dunstrc"
    changes = []

    fragment_content = f"""# Generated by hermes-ricer — {design.get('name', 'theme')}
# Include this in dunstrc with: include = ~/.config/dunst/hermes-dunstrc
# (dunst >= 1.7.0 supports include directives)

[global]
    frame_color = "{palette['primary']}"
    separator_color = "{palette['surface']}"

[urgency_low]
    background = "{palette['background']}"
    foreground = "{palette['muted']}"
    frame_color = "{palette['surface']}"

[urgency_normal]
    background = "{palette['background']}"
    foreground = "{palette['foreground']}"
    frame_color = "{palette['primary']}"

[urgency_critical]
    background = "{palette['danger']}"
    foreground = "{palette['background']}"
    frame_color = "{palette['danger']}"
"""

    if dry_run:
        changes.append({"app": "dunst", "action": "dry-run", "path": str(fragment_path)})
        return changes

    dunst_dir.mkdir(parents=True, exist_ok=True)

    # Backup the fragment and the main dunstrc before touching either
    fragment_backup = backup_file(fragment_path, backup_ts, "dunst/hermes-dunstrc")
    dunstrc_backup = backup_file(dunstrc, backup_ts, "dunst/dunstrc")

    fragment_path.write_text(fragment_content, encoding="utf-8")
    changes.append({
        "app": "dunst",
        "action": "write",
        "path": str(fragment_path),
        "backup": fragment_backup,
    })

    # Inject include directive into dunstrc if it supports it (dunst >= 1.7)
    include_line = f"include = {fragment_path}"
    hermes_marker = "# hermes-ricer"
    injected = False

    if dunstrc.exists():
        dunstrc_text = dunstrc.read_text(encoding="utf-8")
        if str(fragment_path) not in dunstrc_text:
            # Find [global] section and inject after it
            if "[global]" in dunstrc_text:
                dunstrc_text = dunstrc_text.replace(
                    "[global]",
                    f"[global]\n    {hermes_marker}\n    {include_line}",
                    1
                )
            else:
                dunstrc_text += f"\n{hermes_marker}\n{include_line}\n"
            dunstrc.write_text(dunstrc_text, encoding="utf-8")
            injected = True

    changes.append({
        "app": "dunst",
        "action": "inject_include",
        "path": str(dunstrc),
        "backup": dunstrc_backup,
        "injected": injected,
        "include_line": include_line,
        "marker": hermes_marker,
    })

    # Signal dunst to reload
    run_cmd(["pkill", "-USR1", "dunst"], timeout=3)

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — Kvantum (Qt widget style)
# ---------------------------------------------------------------------------

def materialize_kvantum(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set Kvantum widget style and theme."""
    changes = []
    kvantum_dir = HOME / ".config" / "Kvantum"
    kvantum_config = kvantum_dir / "kvantum.kvconfig"
    kdeglobals = HOME / ".config" / "kdeglobals"

    # Determine Kvantum theme from design or fallback
    kvantum_theme = design.get("kvantum_theme")
    if not kvantum_theme:
        # Default to a sensible fallback based on the palette mood
        kvantum_theme = "kvantum-dark"

    if dry_run:
        changes.append({
            "app": "kvantum",
            "action": "dry-run",
            "theme": kvantum_theme,
            "config_path": str(kvantum_config),
        })
        return changes

    # Snapshot current state before touching anything
    prev_kvantum_theme = None
    prev_widget_style = None
    if kvantum_config.exists():
        kv_text = kvantum_config.read_text(errors="replace")
        m = re.search(r"^theme\s*=\s*(.+)$", kv_text, re.MULTILINE | re.IGNORECASE)
        if m:
            prev_kvantum_theme = m.group(1).strip()

    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle"])
            if rc == 0 and out:
                prev_widget_style = out
                break

    # Backup
    kvantum_backup = backup_file(kvantum_config, backup_ts, "kvantum/kvantum.kvconfig")
    kdeglobals_backup = backup_file(kdeglobals, backup_ts, "kvantum/kdeglobals")

    # Write Kvantum config
    kvantum_dir.mkdir(parents=True, exist_ok=True)
    kvantum_config.write_text(f"[General]\ntheme={kvantum_theme}\n", encoding="utf-8")

    # Set widgetStyle in kdeglobals.
    # CRITICAL: value must be "kvantum" (exact Qt6 plugin name from libkvantum.so).
    # "kvantum-dark" is NOT a valid Qt6 style name and will silently fall back to Breeze.
    kwrite = "kwriteconfig6" if cmd_exists("kwriteconfig6") else ("kwriteconfig5" if cmd_exists("kwriteconfig5") else None)
    if kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", "kvantum"])

    # Reload KWin so the style change takes effect in running apps.
    # SAFE on Wayland: only reconfigures compositor, does not kill plasmashell.
    if cmd_exists("qdbus6"):
        run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)

    changes.append({
        "app": "kvantum",
        "action": "write",
        "theme": kvantum_theme,
        "config_path": str(kvantum_config),
        "backup": kvantum_backup,
        "kdeglobals_backup": kdeglobals_backup,
        "previous_kvantum_theme": prev_kvantum_theme,
        "previous_widget_style": prev_widget_style,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — Plasma Theme (panel, tasks, dialogs)
# ---------------------------------------------------------------------------

def materialize_plasma_theme(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the Plasma desktop theme (panel SVGs, task buttons, etc.)."""
    changes = []
    plasma_theme = design.get("plasma_theme")
    if not plasma_theme:
        return changes

    plasmarc = HOME / ".config" / "plasmarc"

    if dry_run:
        changes.append({
            "app": "plasma_theme",
            "action": "dry-run",
            "theme": plasma_theme,
            "config_path": str(plasmarc),
        })
        return changes

    # Snapshot current theme
    prev_theme = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "plasmarc", "--group", "Theme", "--key", "name"])
            if rc == 0 and out:
                prev_theme = out
                break

    # Backup
    plasmarc_backup = backup_file(plasmarc, backup_ts, "plasma/plasmarc")

    # Apply
    kwrite = "kwriteconfig6" if cmd_exists("kwriteconfig6") else ("kwriteconfig5" if cmd_exists("kwriteconfig5") else None)
    if kwrite:
        run_cmd([kwrite, "--file", "plasmarc", "--group", "Theme", "--key", "name", plasma_theme])

    if cmd_exists("plasma-apply-desktoptheme"):
        run_cmd(["plasma-apply-desktoptheme", plasma_theme])

    changes.append({
        "app": "plasma_theme",
        "action": "write",
        "theme": plasma_theme,
        "config_path": str(plasmarc),
        "backup": plasmarc_backup,
        "previous_theme": prev_theme,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — Cursor Theme
# ---------------------------------------------------------------------------

def materialize_cursor(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the cursor theme."""
    changes = []
    cursor_theme = design.get("cursor_theme")
    if not cursor_theme:
        return changes

    kcminputrc = HOME / ".config" / "kcminputrc"

    if dry_run:
        changes.append({
            "app": "cursor",
            "action": "dry-run",
            "theme": cursor_theme,
            "config_path": str(kcminputrc),
        })
        return changes

    # Snapshot current cursor
    prev_cursor = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme"])
            if rc == 0 and out:
                prev_cursor = out
                break

    # Backup
    cursor_backup = backup_file(kcminputrc, backup_ts, "cursor/kcminputrc")

    # Apply
    kwrite = "kwriteconfig6" if cmd_exists("kwriteconfig6") else ("kwriteconfig5" if cmd_exists("kwriteconfig5") else None)
    if kwrite:
        run_cmd([kwrite, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", cursor_theme])

    if cmd_exists("plasma-apply-cursortheme"):
        run_cmd(["plasma-apply-cursortheme", cursor_theme])

    changes.append({
        "app": "cursor",
        "action": "write",
        "theme": cursor_theme,
        "config_path": str(kcminputrc),
        "backup": cursor_backup,
        "previous_cursor": prev_cursor,
    })

    return changes


# ---------------------------------------------------------------------------
# WALLPAPER
# ---------------------------------------------------------------------------

def materialize_wallpaper(
    design: dict,
    wallpaper_path: str | None = None,
    backup_ts: str = "",
    dry_run: bool = False,
) -> list[dict]:
    if not wallpaper_path:
        return []

    changes = []
    desktop = discover_desktop()

    if desktop["wm"] == "kde" and cmd_exists("plasma-apply-wallpaperimage"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path, "method": "plasma-apply-wallpaperimage"})
        else:
            run_cmd(["plasma-apply-wallpaperimage", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path, "method": "plasma-apply-wallpaperimage"})

    elif cmd_exists("swww"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path, "method": "swww img"})
        else:
            run_cmd(["swww", "img", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path, "method": "swww img"})

    elif cmd_exists("feh"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path, "method": "feh --bg-scale"})
        else:
            run_cmd(["feh", "--bg-scale", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path, "method": "feh --bg-scale"})

    return changes


# ---------------------------------------------------------------------------
# MATERIALIZATION ORCHESTRATOR
# ---------------------------------------------------------------------------

APP_MATERIALIZERS = {
    "kde": materialize_kde,
    "kvantum": materialize_kvantum,
    "plasma_theme": materialize_plasma_theme,
    "cursor": materialize_cursor,
    "kitty": materialize_kitty,
    "konsole": materialize_konsole,
    "waybar": materialize_waybar,
    "rofi": materialize_rofi,
    "dunst": materialize_dunst,
}


def materialize(
    design: dict,
    apps: dict | None = None,
    wallpaper: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Materialize the design system across all detected apps."""
    if apps is None:
        apps = discover_apps()

    # ONE shared timestamp for ALL materializers — no race condition
    backup_ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    all_changes = []

    for app_name, mat_fn in APP_MATERIALIZERS.items():
        if app_name in apps:
            try:
                changes = mat_fn(design, backup_ts=backup_ts, dry_run=dry_run)
                all_changes.extend(changes)
            except Exception as e:
                all_changes.append({"app": app_name, "action": "error", "error": str(e)})

    if wallpaper:
        all_changes.extend(
            materialize_wallpaper(design, wallpaper, backup_ts=backup_ts, dry_run=dry_run)
        )

    manifest = {
        "timestamp": backup_ts,
        "design_system": design,
        "changes": all_changes,
        "dry_run": dry_run,
        "backup_dir": str(BACKUP_DIR / backup_ts),
    }

    if not dry_run:
        CURRENT_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = CURRENT_DIR / "manifest.json"

        # Archive previous manifest to history
        if manifest_path.exists():
            history_dir = CURRENT_DIR / "history"
            history_dir.mkdir(exist_ok=True)
            prev = json.loads(manifest_path.read_text())
            prev_ts = prev.get("timestamp", backup_ts + "_prev")
            shutil.move(str(manifest_path), str(history_dir / f"manifest_{prev_ts}.json"))

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest


# ---------------------------------------------------------------------------
# ROLLBACK — comprehensive undo
# ---------------------------------------------------------------------------

def _remove_injected_block(file_path: Path, marker: str) -> bool:
    """
    Remove a hermes-injected block from a text config file.
    Removes the marker line and the line immediately following it.
    Returns True if anything was removed.
    """
    if not file_path.exists():
        return False

    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines = []
    i = 0
    removed = False
    while i < len(lines):
        if marker in lines[i]:
            # Skip the marker line AND the next line (the injected directive)
            i += 1
            if i < len(lines):
                i += 1
            removed = True
        else:
            new_lines.append(lines[i])
            i += 1

    if removed:
        file_path.write_text("".join(new_lines), encoding="utf-8")

    return removed


def undo() -> dict:
    """
    Undo the most recent materialization.

    Strategy per app:
    - If the change has a 'backup' key: restore the file from backup.
    - If the change was an 'inject_include' or 'inject_theme': remove the
      injected lines using the stored marker (EVEN IF the backup already
      restored the file — belt-and-suspenders).
    - For KDE: re-apply the previous colorscheme via plasma-apply-colorscheme.
    - For Konsole: previous_profile is noted in the manifest (no autoswitch —
      Konsole requires a session restart to change profile).
    """
    manifest_path = CURRENT_DIR / "manifest.json"
    if not manifest_path.exists():
        return {"status": "error", "message": "No active theme to undo. Run 'apply' or 'preset' first."}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if manifest.get("dry_run"):
        return {"status": "error", "message": "Cannot undo a dry-run — no changes were made."}

    restored = []
    failed = []
    skipped = []

    for change in manifest.get("changes", []):
        app = change.get("app", "unknown")
        action = change.get("action", "")

        # ---- Restore backed-up files ----
        for backup_key in ["backup", "backup_profile", "backup_colors", "backup_konsolerc",
                            "config_backup", "theme_backup", "main_backup"]:
            bp = change.get(backup_key)
            dest_key = {
                "backup": "path",
                "backup_profile": "profile_path",
                "backup_colors": "color_scheme_path",
                "config_backup": None,   # waybar config
            }.get(backup_key, None)

            if bp and Path(bp).exists():
                # Determine destination
                if backup_key == "backup" and "path" in change:
                    dest = Path(change["path"])
                elif backup_key == "backup_profile" and "profile_path" in change:
                    dest = Path(change["profile_path"])
                elif backup_key == "backup_colors" and "color_scheme_path" in change:
                    dest = Path(change["color_scheme_path"])
                elif backup_key == "backup_konsolerc":
                    dest = HOME / ".config" / "konsolerc"
                elif backup_key == "config_backup":
                    dest = HOME / ".config" / "waybar" / "config"
                else:
                    continue

                try:
                    shutil.copy2(bp, dest)
                    restored.append({"app": app, "restored": str(dest), "from": bp})
                except Exception as e:
                    failed.append({"app": app, "path": str(dest), "error": str(e)})

            elif bp and not Path(bp).exists():
                # Backup path recorded but file is gone — delete what we created
                dest_path = change.get("path")
                if dest_path and Path(dest_path).exists():
                    try:
                        Path(dest_path).unlink()
                        restored.append({"app": app, "deleted": dest_path, "note": "no backup existed — file was new, deleted"})
                    except Exception as e:
                        failed.append({"app": app, "path": dest_path, "error": str(e)})

        # ---- Remove injected include/theme lines ----
        if action in ("inject_include", "inject_theme") and change.get("injected"):
            path = change.get("path")
            marker = change.get("marker")
            if path and marker:
                removed = _remove_injected_block(Path(path), marker)
                if removed:
                    restored.append({"app": app, "action": "removed_injection", "path": path})
                else:
                    skipped.append({"app": app, "note": "injection marker not found in file (may already be clean)", "path": path})

        # ---- KDE: re-apply previous colorscheme ----
        if app == "kde" and action in ("reload", "write"):
            prev = change.get("previous_colorscheme")
            if prev and cmd_exists("plasma-apply-colorscheme"):
                rc, _, _ = run_cmd(["plasma-apply-colorscheme", prev], timeout=10)
                if rc == 0:
                    restored.append({"app": "kde", "action": "restored_colorscheme", "scheme": prev})
                else:
                    failed.append({"app": "kde", "action": "restore_colorscheme", "scheme": prev, "error": f"exit code {rc}"})
            elif prev:
                skipped.append({"app": "kde", "note": "plasma-apply-colorscheme not found; previous scheme was: " + prev})

        # ---- Kvantum: restore previous theme and widgetStyle ----
        if app == "kvantum" and action == "write":
            prev_kv = change.get("previous_kvantum_theme")
            prev_ws = change.get("previous_widget_style")
            kwrite = "kwriteconfig6" if cmd_exists("kwriteconfig6") else ("kwriteconfig5" if cmd_exists("kwriteconfig5") else None)

            if prev_kv:
                kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
                kvantum_config.parent.mkdir(parents=True, exist_ok=True)
                kvantum_config.write_text(f"[General]\ntheme={prev_kv}\n", encoding="utf-8")
                restored.append({"app": "kvantum", "action": "restored_theme", "theme": prev_kv})
            if prev_ws and kwrite:
                # Restore exact previous widgetStyle (e.g. "Breeze", "kvantum", "Oxygen")
                run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", prev_ws])
                restored.append({"app": "kvantum", "action": "restored_widgetStyle", "style": prev_ws})
            elif not prev_ws and kwrite:
                # No previous widgetStyle recorded — delete the key entirely so KDE uses L&F default.
                # Use --delete rather than setting to empty string (empty string is worse than absent).
                run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", "--delete"])
                restored.append({"app": "kvantum", "action": "cleared_widgetStyle"})
            # Reload KWin after widget style change
            if cmd_exists("qdbus6"):
                run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)

        # ---- Plasma Theme: restore previous ----
        if app == "plasma_theme" and action == "write":
            prev = change.get("previous_theme")
            kwrite = "kwriteconfig6" if cmd_exists("kwriteconfig6") else ("kwriteconfig5" if cmd_exists("kwriteconfig5") else None)
            if prev and kwrite:
                run_cmd([kwrite, "--file", "plasmarc", "--group", "Theme", "--key", "name", prev])
            if prev and cmd_exists("plasma-apply-desktoptheme"):
                rc, _, _ = run_cmd(["plasma-apply-desktoptheme", prev], timeout=10)
                if rc == 0:
                    restored.append({"app": "plasma_theme", "action": "restored", "theme": prev})
                else:
                    failed.append({"app": "plasma_theme", "action": "restore", "theme": prev, "error": f"exit code {rc}"})
            elif not prev:
                skipped.append({"app": "plasma_theme", "note": "no previous theme recorded"})

        # ---- Cursor: restore previous ----
        if app == "cursor" and action == "write":
            prev = change.get("previous_cursor")
            kwrite = "kwriteconfig6" if cmd_exists("kwriteconfig6") else ("kwriteconfig5" if cmd_exists("kwriteconfig5") else None)
            if prev and kwrite:
                run_cmd([kwrite, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", prev])
            if prev and cmd_exists("plasma-apply-cursortheme"):
                rc, _, _ = run_cmd(["plasma-apply-cursortheme", prev], timeout=10)
                if rc == 0:
                    restored.append({"app": "cursor", "action": "restored", "theme": prev})
                else:
                    failed.append({"app": "cursor", "action": "restore", "theme": prev, "error": f"exit code {rc}"})
            elif not prev:
                skipped.append({"app": "cursor", "note": "no previous cursor recorded"})

    # Mark manifest as undone
    manifest["undone"] = True
    manifest["undone_at"] = datetime.utcnow().isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    status = "success" if not failed else "partial"
    return {
        "status": status,
        "restored": restored,
        "failed": failed,
        "skipped": skipped,
    }


# ---------------------------------------------------------------------------
# PRESETS
# ---------------------------------------------------------------------------

PRESETS = {
    "catppuccin-mocha": {
        "name": "catppuccin-mocha",
        "description": "Soothing pastel dark theme.",
        "palette": {
            "background": "#1e1e2e", "foreground": "#cdd6f4", "primary": "#89b4fa",
            "secondary": "#f5c2e7", "accent": "#fab387", "surface": "#313244",
            "muted": "#6c7086", "danger": "#f38ba8", "success": "#a6e3a1", "warning": "#f9e2af",
        },
        "mood_tags": ["pastel", "dark", "cozy"],
    },
    "nord": {
        "name": "nord",
        "description": "Arctic, north-bluish color palette.",
        "palette": {
            "background": "#2e3440", "foreground": "#d8dee9", "primary": "#88c0d0",
            "secondary": "#81a1c1", "accent": "#ebcb8b", "surface": "#3b4252",
            "muted": "#4c566a", "danger": "#bf616a", "success": "#a3be8c", "warning": "#ebcb8b",
        },
        "mood_tags": ["arctic", "blue", "flat"],
    },
    "gruvbox-dark": {
        "name": "gruvbox-dark",
        "description": "Retro groove dark colors.",
        "palette": {
            "background": "#282828", "foreground": "#ebdbb2", "primary": "#458588",
            "secondary": "#b16286", "accent": "#d79921", "surface": "#3c3836",
            "muted": "#928374", "danger": "#cc241d", "success": "#98971a", "warning": "#d79921",
        },
        "mood_tags": ["retro", "warm", "sepia"],
    },
    "dracula": {
        "name": "dracula",
        "description": "Dark theme with vibrant colors.",
        "palette": {
            "background": "#282a36", "foreground": "#f8f8f2", "primary": "#bd93f9",
            "secondary": "#ff79c6", "accent": "#ffb86c", "surface": "#44475a",
            "muted": "#6272a4", "danger": "#ff5555", "success": "#50fa7b", "warning": "#f1fa8c",
        },
        "mood_tags": ["dark", "neon", "purple"],
    },
    "tokyo-night": {
        "name": "tokyo-night",
        "description": "A dark and clean theme inspired by the lights of Tokyo at night.",
        "palette": {
            "background": "#1a1b26", "foreground": "#a9b1d6", "primary": "#7aa2f7",
            "secondary": "#bb9af7", "accent": "#ff9e64", "surface": "#24283b",
            "muted": "#565f89", "danger": "#f7768e", "success": "#9ece6a", "warning": "#e0af68",
        },
        "mood_tags": ["cyberpunk", "blue", "neon"],
    },
    "rose-pine": {
        "name": "rose-pine",
        "description": "All natural pine, faux fur and a bit of soho vibes.",
        "palette": {
            "background": "#191724", "foreground": "#e0def4", "primary": "#9ccfd8",
            "secondary": "#f6c177", "accent": "#ebbcba", "surface": "#1f1d2e",
            "muted": "#6e6a86", "danger": "#eb6f92", "success": "#31748f", "warning": "#f6c177",
        },
        "mood_tags": ["soft", "pastel", "nature"],
    },
    "solarized-dark": {
        "name": "solarized-dark",
        "description": "Precision colors for machines and people.",
        "palette": {
            "background": "#002b36", "foreground": "#839496", "primary": "#268bd2",
            "secondary": "#2aa198", "accent": "#b58900", "surface": "#073642",
            "muted": "#586e75", "danger": "#dc322f", "success": "#859900", "warning": "#b58900",
        },
        "mood_tags": ["low-contrast", "warm", "readable"],
    },
    "doom-knight": {
        "name": "doom-knight",
        "description": "DragonFable DoomKnight — deep purples, battered gold, dark crimson.",
        "palette": {
            "background": "#0d0b14", "foreground": "#d4c5a9", "primary": "#c9a227",
            "secondary": "#7b2d8b", "accent": "#e8d5a3", "surface": "#1a1625",
            "muted": "#4a3f5c", "danger": "#8b1a1a", "success": "#4a7c59", "warning": "#c9a227",
        },
        "mood_tags": ["dark", "gothic", "gold", "dragonfable"],
    },
    "void-dragon": {
        "name": "void-dragon",
        "description": "Hasan's void dragon knight — extracted directly from his DragonFable character. Deep void sky, cyan soul blade, gold filigree, dark teal dragon aura.",
        "palette": {
            "background": "#0c1220",
            "foreground": "#e4f0ff",
            "primary":    "#7ad4f0",
            "secondary":  "#0d2e32",
            "accent":     "#d4a012",
            "surface":    "#1c1e2a",
            "muted":      "#3d2214",
            "danger":     "#cc3090",
            "success":    "#2a8060",
            "warning":    "#c87820",
        },
        # Kvantum: catppuccin-mocha-teal is already installed and matches the
        # cyan primary perfectly. If you want to try others: catppuccin-mocha-sky
        # (brighter), catppuccin-mocha-sapphire (deeper blue).
        "kvantum_theme": "catppuccin-mocha-teal",
        # Cursor: catppuccin-macchiato-teal-cursors is installed.
        # Matches the cyan primary without being too bright.
        "cursor_theme": "catppuccin-macchiato-teal-cursors",
        "mood_tags": ["void", "dragon", "cyan", "gold", "dragonfable"],
    },
}


def load_preset(name: str) -> dict | None:
    return PRESETS.get(name)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hermes Ricer — AI-Native Desktop Theming")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("discover", help="Detect desktop stack")

    apply_parser = subparsers.add_parser("apply", help="Apply a design system JSON")
    apply_parser.add_argument("--design", required=True, help="Path to design_system.json")
    apply_parser.add_argument("--wallpaper", default=None, help="Wallpaper image path")
    apply_parser.add_argument("--dry-run", action="store_true", help="Preview without applying")

    preset_parser = subparsers.add_parser("preset", help="Apply a named preset")
    preset_parser.add_argument("name", choices=list(PRESETS.keys()), help="Preset name")
    preset_parser.add_argument("--dry-run", action="store_true")

    subparsers.add_parser("undo", help="Undo last theme application")
    subparsers.add_parser("status", help="Show detected stack and active theme")
    subparsers.add_parser("presets", help="List available presets")
    subparsers.add_parser("simulate-undo", help="Show exactly what undo would restore, without applying anything")

    args = parser.parse_args()

    if args.command == "discover":
        result = discover()
        print(json.dumps(result, indent=2, default=str))
        return

    if args.command == "presets":
        for name, preset in PRESETS.items():
            print(f"  {name:25s} — {preset['description']}")
        return

    if args.command == "status":
        result = discover()
        print("=== Desktop Stack ===")
        print(f"  WM/DE   : {result['desktop']['wm']}")
        print(f"  Session : {result['desktop']['session_type']}")
        print(f"  Env     : {result['desktop']['desktop_env']}")
        print("\n=== Detected Apps ===")
        for app in sorted(result["apps"]):
            print(f"  {app}")
        manifest_path = CURRENT_DIR / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            ds = manifest.get("design_system", {})
            print("\n=== Active Theme ===")
            print(f"  Name        : {ds.get('name', 'unknown')}")
            print(f"  Description : {ds.get('description', '')}")
            print(f"  Applied at  : {manifest.get('timestamp', '')}")
            if manifest.get("undone"):
                print(f"  Status      : UNDONE at {manifest.get('undone_at')}")
            print(f"  Backup dir  : {manifest.get('backup_dir', '')}")
        else:
            print("\n=== Active Theme ===")
            print("  None (no theme applied yet)")
        return

    if args.command == "preset":
        design = load_preset(args.name)
        if not design:
            print(f"Unknown preset: {args.name}", file=sys.stderr)
            sys.exit(1)
        manifest = materialize(design, dry_run=args.dry_run)
        print(json.dumps(manifest, indent=2, default=str))
        return

    if args.command == "apply":
        with open(args.design, "r", encoding="utf-8") as f:
            design = json.load(f)
        manifest = materialize(design, wallpaper=args.wallpaper, dry_run=args.dry_run)
        print(json.dumps(manifest, indent=2, default=str))
        return

    if args.command == "undo":
        result = undo()
        print(json.dumps(result, indent=2, default=str))
        if result["status"] == "success":
            print("\nUndo complete.", file=sys.stderr)
        elif result["status"] == "partial":
            print(f"\nPartial undo — {len(result['failed'])} failure(s). Check 'failed' in output.", file=sys.stderr)
        return

    if args.command == "simulate-undo":
        manifest_path = CURRENT_DIR / "manifest.json"
        if not manifest_path.exists():
            print("No manifest found — no theme has been applied yet.")
            return
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("dry_run"):
            print("Last run was a dry-run — nothing to undo.")
            return
        print("=== Simulate Undo ===")
        print(f"Theme applied  : {manifest.get('design_system', {}).get('name', 'unknown')}")
        print(f"Applied at     : {manifest.get('timestamp', 'unknown')}")
        print(f"Backup dir     : {manifest.get('backup_dir', 'unknown')}")
        print(f"Undone already : {manifest.get('undone', False)}")
        print()
        for change in manifest.get("changes", []):
            app = change.get("app", "?")
            action = change.get("action", "?")
            if action == "error":
                print(f"  [{app}] SKIPPED (errored during apply): {change.get('error')}")
                continue

            # --- File restores ---
            for bk in ["backup", "backup_profile", "backup_colors", "backup_konsolerc", "config_backup"]:
                val = change.get(bk)
                dest = change.get("path") or change.get("profile_path") or change.get("color_scheme_path")
                if val:
                    exists = Path(val).exists()
                    print(f"  [{app}] RESTORE {dest}")
                    print(f"         from    {val}  ({'EXISTS' if exists else 'MISSING — would delete dest'})")

            # --- Injection removals ---
            if action in ("inject_include", "inject_theme") and change.get("injected"):
                print(f"  [{app}] REMOVE injected block from {change.get('path')}")
                print(f"         marker: {change.get('marker')}")

            # --- KDE: reapply colorscheme ---
            if app == "kde" and action in ("reload", "write"):
                prev = change.get("previous_colorscheme")
                if prev:
                    print(f"  [kde]  REAPPLY colorscheme: {prev}")

            # --- Kvantum: restore theme + widgetStyle ---
            if app == "kvantum" and action == "write":
                prev_kv = change.get("previous_kvantum_theme")
                prev_ws = change.get("previous_widget_style")
                if prev_kv:
                    print(f"  [kvantum] RESTORE theme:       {prev_kv}")
                if prev_ws:
                    print(f"  [kvantum] RESTORE widgetStyle: {prev_ws}")
                else:
                    print(f"  [kvantum] DELETE widgetStyle key (was not set)")

            # --- Plasma theme: restore ---
            if app == "plasma_theme" and action == "write":
                prev = change.get("previous_theme")
                if prev:
                    print(f"  [plasma_theme] RESTORE: {prev}")
                else:
                    print(f"  [plasma_theme] No previous theme recorded — will skip")

            # --- Cursor: restore ---
            if app == "cursor" and action == "write":
                prev = change.get("previous_cursor")
                if prev:
                    print(f"  [cursor] RESTORE: {prev}")
                else:
                    print(f"  [cursor] No previous cursor recorded — will skip")
        print()
        print("Run 'ricer undo' to execute the above.")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
