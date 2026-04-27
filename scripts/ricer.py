#!/usr/bin/env python3
"""
Hermes Ricer — AI-Native Desktop Theming Engine
Python driver for config discovery, materialization, and rollback.
"""

import argparse
import colorsys
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Resolve the real scripts dir even when invoked via a symlink (e.g. ~/.local/bin/ricer)
# so sibling modules like palette_extractor are importable.
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# Optional Jinja2 import with fallback
jinja2 = None
try:
    import jinja2
except ImportError:
    pass

HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "linux-ricing"
BACKUP_DIR = CACHE_DIR / "backups"
CURRENT_DIR = CACHE_DIR / "current"
SKILL_DIR = _SCRIPT_DIR.parent  # scripts/ -> skill root
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
    "kvantum_theme": "catppuccin-mocha-blue",
    "cursor_theme": "catppuccin-macchiato-blue-cursors",
    "icon_theme": "Papirus-Dark",
    "gtk_theme": "Adwaita-dark",
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
    except (OSError, subprocess.SubprocessError, TimeoutError) as e:
        return -1, "", str(e)


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _get_kwrite() -> str | None:
    if cmd_exists("kwriteconfig6"):
        return "kwriteconfig6"
    if cmd_exists("kwriteconfig5"):
        return "kwriteconfig5"
    return None


from desktop_utils import discover_desktop  # noqa: E402


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
    # These are tracked as separate materializers but share the KDE prerequisite.
    # CRITICAL: without this block, kvantum/plasma_theme/cursor materializers are
    # never called because the APP_MATERIALIZERS loop checks `if app_name in apps`.
    if "kde" in apps:
        apps["kvantum"]        = {"installed": True}
        apps["plasma_theme"]   = {"installed": True}
        apps["cursor"]         = {"installed": True}
        apps["kde_lockscreen"] = {"installed": True}

    # Hyprland sub-system — register when hyprland is the active WM.
    # hyprctl is the detection signal; no binary named "hyprland" in PATH.
    if cmd_exists("hyprctl"):
        apps["hyprland"] = {"installed": True}
        apps["hyprlock"] = {"installed": True, "config_dir": str(HOME / ".config" / "hypr")}

    return apps


def discover() -> dict[str, Any]:
    """Full system discovery."""
    return {
        "desktop": discover_desktop(),
        "apps": discover_apps(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
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


# ---------------------------------------------------------------------------
# COLOR UTILITIES
# ---------------------------------------------------------------------------

def hex_to_rgb(hex_color: str) -> str:
    """Convert '#rrggbb' to 'r,g,b' decimal string as KDE .colors expects."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


def hex_to_rgb_tuple(hex_color: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' to (r, g, b) integer tuple."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_tuple_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) integers to '#rrggbb' hex string."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def yiq_text_color(hex_color: str) -> str:
    """Return '#ffffff' or '#000000' for maximum readability over hex_color background.

    Uses the YIQ perceptual luma formula — same technique as ricemood's 'ttc' pipe.
    YIQ accounts for human perception: green contributes most to perceived brightness.
      yiq = (r*299 + g*587 + b*114) / 1000
    Under 200 -> white text. 200+ -> black text.
    """
    r, g, b = hex_to_rgb_tuple(hex_color)
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "#ffffff" if yiq < 200 else "#000000"


def rotate_hue(hex_color: str, degrees: float) -> str:
    """Rotate the hue of hex_color by degrees (0-360). Preserves saturation and value.

    Used to derive harmonious color variants without leaving the wallpaper's palette.
    E.g. rotate_hue(primary, 30) for a related secondary, rotate_hue(accent, 180) for complement.
    """
    r, g, b = hex_to_rgb_tuple(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360.0) % 1.0
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return rgb_tuple_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


def adjust_lightness(hex_color: str, factor: float) -> str:
    """Multiply the HSL lightness of hex_color by factor.

    factor < 1 darkens (0.8 = 20% darker), factor > 1 lightens (1.3 = 30% lighter).
    Clamps to [0.0, 1.0]. Preserves hue and saturation.
    """
    r, g, b = hex_to_rgb_tuple(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = max(0.0, min(1.0, l * factor))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return rgb_tuple_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


# ---------------------------------------------------------------------------
# TEMPLATE ENGINE
# ---------------------------------------------------------------------------

def simple_render(template_str: str, context: dict) -> str:
    """Minimal template renderer when Jinja2 is unavailable.

    Supports the same ``{{key}}`` double-brace syntax used by Jinja2 so that
    templates work identically regardless of whether Jinja2 is installed.
    Using single-brace ``{key}`` would match *inside* ``{{key}}``, leaving
    stray braces in the output (e.g. ``{#1e1e2e}`` instead of ``#1e1e2e``).
    """
    result = template_str
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
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

    # Back up kdeglobals FIRST — before any materializer mutates it. This is
    # the shared file every KDE materializer touches (kde writes [Colors:*],
    # kvantum writes widgetStyle, etc.) so it must be captured pre-apply.
    # Other materializers (e.g. kvantum) rely on their own key-level snapshots
    # and MUST NOT re-backup kdeglobals — their backup would be stale.
    kdeglobals_path = HOME / ".config" / "kdeglobals"
    kdeglobals_backup = backup_file(kdeglobals_path, backup_ts, "kde/kdeglobals")

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
        "kdeglobals_backup": kdeglobals_backup,
        "previous_colorscheme": prev_scheme,
    })

    # Apply via plasma-apply-colorscheme
    if cmd_exists("plasma-apply-colorscheme"):
        # Force-toggle: if already set, Plasma says "already set" and does nothing.
        # Bounce to BreezeClassic first to force a real re-application.
        rc_pre, out_pre, _ = run_cmd(["plasma-apply-colorscheme", colorscheme_name], timeout=10)
        if "already set" in (out_pre or ""):
            run_cmd(["plasma-apply-colorscheme", "BreezeClassic"], timeout=5)
            time.sleep(0.3)
            rc, out, err = run_cmd(["plasma-apply-colorscheme", colorscheme_name], timeout=10)
        else:
            rc = rc_pre
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

    # ANSI color4 is "blue". If primary==warning (both map to the same hex),
    # blue and yellow become indistinguishable. Fall back to secondary for color4
    # to keep the 16-color palette distinct.
    blue_slot = palette['secondary'] if palette['primary'] == palette['warning'] else palette['primary']
    blue_bright = adjust_lightness(rotate_hue(blue_slot, -10), 1.3)

    content = f"""# Generated by linux-ricing — {design.get('name', 'theme')}
background {palette['background']}
foreground {palette['foreground']}
cursor {palette['accent']}
cursor_text_color {yiq_text_color(palette['accent'])}
selection_background {palette['primary']}
selection_foreground {yiq_text_color(palette['primary'])}
# --- ANSI normal (0-7) ---
color0 {palette['surface']}
color1 {palette['danger']}
color2 {palette['success']}
color3 {palette['warning']}
color4 {blue_slot}
color5 {palette['secondary']}
color6 {palette['accent']}
color7 {palette['foreground']}
# --- ANSI bright/intense (8-15): hue-rotated and lightened for variety ---
color8  {adjust_lightness(palette['muted'], 1.4)}
color9  {adjust_lightness(rotate_hue(palette['danger'], 15), 1.3)}
color10 {adjust_lightness(rotate_hue(palette['success'], 10), 1.3)}
color11 {adjust_lightness(palette['warning'], 1.3)}
color12 {blue_bright}
color13 {adjust_lightness(rotate_hue(palette['secondary'], 20), 1.3)}
color14 {adjust_lightness(rotate_hue(palette['accent'], 15), 1.3)}
color15 {adjust_lightness(palette['foreground'], 1.25)}
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
    hermes_marker = "# linux-ricing"
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
    profile_name = "linux-ricing"
    profile_path = konsole_dir / f"{profile_name}.profile"
    color_scheme_name = f"hermes-{design.get('name', 'ricer')}"
    color_scheme_path = colors_dir / f"{color_scheme_name}.colorscheme"
    konsolerc = HOME / ".config" / "konsolerc"
    changes = []

    # Konsole .colorscheme uses decimal RGB — base palette
    p = {k: hex_to_rgb(v) for k, v in palette.items()}
    # ANSI color4 = "blue". If primary==warning, they collide — use secondary instead.
    blue_hex = palette['secondary'] if palette['primary'] == palette['warning'] else palette['primary']
    p['blue'] = hex_to_rgb(blue_hex)
    # Bright/intense variants use hue rotation + lightness boost (same logic as kitty)
    pi = {
        "muted":     hex_to_rgb(adjust_lightness(palette["muted"], 1.4)),
        "danger":    hex_to_rgb(adjust_lightness(rotate_hue(palette["danger"], 15), 1.3)),
        "success":   hex_to_rgb(adjust_lightness(rotate_hue(palette["success"], 10), 1.3)),
        "warning":   hex_to_rgb(adjust_lightness(palette["warning"], 1.3)),
        "blue":      hex_to_rgb(adjust_lightness(rotate_hue(blue_hex, -10), 1.3)),
        "secondary": hex_to_rgb(adjust_lightness(rotate_hue(palette["secondary"], 20), 1.3)),
        "accent":    hex_to_rgb(adjust_lightness(rotate_hue(palette["accent"], 15), 1.3)),
        "foreground":hex_to_rgb(adjust_lightness(palette["foreground"], 1.25)),
    }

    color_scheme_content = f"""[Background]
Color={p['background']}

[BackgroundIntense]
Color={p['surface']}

[Foreground]
Color={p['foreground']}

[ForegroundIntense]
Color={pi['foreground']}
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
Color={pi['muted']}

[Color1]
Color={p['danger']}

[Color1Intense]
Color={pi['danger']}

[Color2]
Color={p['success']}

[Color2Intense]
Color={pi['success']}

[Color3]
Color={p['warning']}

[Color3Intense]
Color={pi['warning']}

[Color4]
Color={p['blue']}

[Color4Intense]
Color={pi['blue']}

[Color5]
Color={p['secondary']}

[Color5Intense]
Color={pi['secondary']}

[Color6]
Color={p['accent']}

[Color6Intense]
Color={pi['accent']}

[Color7]
Color={p['foreground']}

[Color7Intense]
Color={pi['foreground']}
"""

    profile_content = f"""[Appearance]
ColorScheme={color_scheme_name}

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
    kwrite = _get_kwrite()
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

    content = f"""/* Generated by linux-ricing — {design.get('name', 'theme')} */
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
        "config_path": str(config_path),
    })

    # Inject @import into the main style.css so hermes theme is loaded.
    # If style.css has many @define-color lines it's a hardcoded theme — warn but still inject.
    main_style = waybar_dir / "style.css"
    import_line = f'@import "{style_path}";'
    hermes_marker = "/* linux-ricing */"
    injected = False

    if main_style.exists():
        css_text = main_style.read_text(encoding="utf-8")
        if hermes_marker not in css_text:
            # Prepend at top so it loads before any hardcoded definitions
            main_style.write_text(
                f"{hermes_marker}\n{import_line}\n\n" + css_text,
                encoding="utf-8"
            )
            injected = True
    else:
        main_style.write_text(f"{hermes_marker}\n{import_line}\n", encoding="utf-8")
        injected = True

    changes.append({
        "app": "waybar",
        "action": "inject_include",
        "path": str(main_style),
        "injected": injected,
        "import_line": import_line,
        "marker": hermes_marker,
    })

    # Reload waybar
    run_cmd(["pkill", "-SIGUSR2", "waybar"], timeout=3)

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

    content = f"""/* Generated by linux-ricing — {design.get('name', 'theme')} */
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
    hermes_marker = "/* linux-ricing */"
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

    fragment_content = f"""# Generated by linux-ricing — {design.get('name', 'theme')}
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
    hermes_marker = "# linux-ricing"
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
# APP HANDLERS — Hyprland (border colors, gaps)
# ---------------------------------------------------------------------------

def materialize_hyprland(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set Hyprland window border colors from the palette.

    Uses hyprctl keyword for live changes, and patches hyprland.conf for persistence.
    Active border: primary -> accent gradient. Inactive: secondary.
    """
    palette = design["palette"]
    changes = []

    # Guard: only run on Hyprland — skip silently on other WMs.
    desktop = discover_desktop()
    if desktop.get("wm") != "hyprland":
        return changes

    hyprland_conf = HOME / ".config" / "hypr" / "hyprland.conf"
    primary_hex = palette["primary"].lstrip("#")
    accent_hex = palette["accent"].lstrip("#")
    secondary_hex = palette["secondary"].lstrip("#")

    active_border = f"rgba({primary_hex}ee) rgba({accent_hex}ee) 45deg"
    inactive_border = f"rgba({secondary_hex}aa)"

    if dry_run:
        changes.append({
            "app": "hyprland", "action": "dry-run",
            "active_border": active_border,
            "inactive_border": inactive_border,
        })
        return changes

    # Live-apply via hyprctl
    run_cmd(["hyprctl", "keyword", "general:col.active_border", active_border])
    run_cmd(["hyprctl", "keyword", "general:col.inactive_border", inactive_border])

    # Persist in hyprland.conf — patch existing lines or append
    if hyprland_conf.exists():
        backup_file(hyprland_conf, backup_ts, "hyprland/hyprland.conf")
        content = hyprland_conf.read_text(errors="replace")
        new_content = content

        # Replace col.active_border line
        active_pattern = re.compile(r"(col\.active_border\s*=\s*).*")
        if active_pattern.search(new_content):
            new_content = active_pattern.sub(rf"\g<1>{active_border}", new_content)
        else:
            # Try to insert after border_size in general {}
            new_content = re.sub(
                r"(border_size\s*=\s*\d+\n)",
                rf"\1    col.active_border = {active_border}\n",
                new_content, count=1
            )

        # Replace col.inactive_border line
        inactive_pattern = re.compile(r"(col\.inactive_border\s*=\s*).*")
        if inactive_pattern.search(new_content):
            new_content = inactive_pattern.sub(rf"\g<1>{inactive_border}", new_content)
        else:
            new_content = re.sub(
                r"(col\.active_border\s*=\s*[^\n]+\n)",
                rf"\1    col.inactive_border = {inactive_border}\n",
                new_content, count=1
            )

        if new_content != content:
            hyprland_conf.write_text(new_content, encoding="utf-8")

    changes.append({
        "app": "hyprland", "action": "set_borders",
        "active_border": active_border,
        "inactive_border": inactive_border,
        "config_path": str(hyprland_conf),
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — hyprlock (lock screen)
# ---------------------------------------------------------------------------


def materialize_hyprlock(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Materialize hyprlock lock screen from the design palette.

    hyprlock has NO include/import system — the config must be fully rewritten
    to change the theme. We back up the original, write a new themed config,
    and restore from backup on undo.

    Themeable elements:
    - Background: wallpaper with blur/contrast/vibrancy tuned to palette
    - Time label: primary color, large font, centered above input
    - Date label: foreground/muted color, smaller, below time
    - Input field: primary outline, surface inner, accent dots
    - PAM failure feedback: danger color for fail_text
    """
    palette = design["palette"]
    changes = []

    # Guard: hyprlock only works on Hyprland — skip silently on other WMs.
    # We call discover_desktop() here rather than accepting it as a parameter
    # to keep the materializer contract uniform across all apps.
    desktop = discover_desktop()
    if desktop.get("wm") != "hyprland":
        return changes

    hyprlock_conf = HOME / ".config" / "hypr" / "hyprlock.conf"
    theme_name = design.get("name", "linux-ricing")

    # Derive rgba tuples (r,g,b) for reuse with different alphas
    p_r, p_g, p_b = hex_to_rgb_tuple(palette["primary"])
    fg_r, fg_g, fg_b = hex_to_rgb_tuple(palette["foreground"])
    surf_r, surf_g, surf_b = hex_to_rgb_tuple(palette["surface"])
    danger_r, danger_g, danger_b = hex_to_rgb_tuple(palette["danger"])
    succ_r, succ_g, succ_b = hex_to_rgb_tuple(palette["success"])
    warn_r, warn_g, warn_b = hex_to_rgb_tuple(palette["warning"])

    def _r(r, g, b, a): return f"{r:02x}{g:02x}{b:02x}{int(a * 255):02x}"

    p_rgba      = _r(p_r, p_g, p_b, 0.95)
    fg_rgba     = _r(fg_r, fg_g, fg_b, 0.85)
    surf_rgba   = _r(surf_r, surf_g, surf_b, 0.88)
    danger_rgba = _r(danger_r, danger_g, danger_b, 1.0)
    succ_rgba   = _r(succ_r, succ_g, succ_b, 1.0)
    warn_rgba   = _r(warn_r, warn_g, warn_b, 1.0)
    p_shadow35  = _r(p_r, p_g, p_b, 0.35)
    black65     = _r(0, 0, 0, 0.65)
    p_shadow25  = _r(p_r, p_g, p_b, 0.25)

    # Extract wallpaper path from existing config if present
    existing_wallpaper = None
    if hyprlock_conf.exists():
        text = hyprlock_conf.read_text(errors="replace")
        m = re.search(r'^\s*path\s*=\s*(.+)$', text, re.MULTILINE)
        if m:
            existing_wallpaper = m.group(1).strip()

    # Default wallpaper fallback — try to detect from active wallpaper daemon
    if not existing_wallpaper:
        existing_wallpaper, _ = _snapshot_current_wallpaper(desktop)
        if not existing_wallpaper:
            existing_wallpaper = ""

    # PAM placeholder text — adapts to theme mood
    mood_tags = design.get("mood_tags", [])
    if "maplestory" in mood_tags or "game" in mood_tags:
        pam_placeholder = '<span foreground="#d4a012">HP: ∞ | MP: ∞</span>'
        pam_fail_text = '<span foreground="#cc1133"><b>☠ ACCESS DENIED</b></span>'
    elif "gothic" in mood_tags or "dark-fantasy" in mood_tags:
        pam_placeholder = '<span foreground="#685259">Enter passphrase...</span>'
        pam_fail_text = '<span foreground="#cc1133"><b>✖ WRONG</b></span>'
    elif "void" in mood_tags or "dragon" in mood_tags:
        pam_placeholder = '<span foreground="#7ad4f0">Void gate passphrase...</span>'
        pam_fail_text = '<span foreground="#cc3090"><b>⚔ DENIED</b></span>'
    else:
        pam_placeholder = f'<span foreground="{palette["accent"]}">Enter password...</span>'
        pam_fail_text = f'<span foreground="{palette["danger"]}"><b>✖ Access Denied</b></span>'

    config_content = f"""# ═══════════════════════════════════════════════════════════════════
# HERMES-RICER — {theme_name} Lock Screen
# Generated by linux-ricing — do not edit manually
# ═══════════════════════════════════════════════════════════════════

background {{
    monitor =
    path = {existing_wallpaper}
    blur_passes = 3
    blur_size = 10
    noise = 0.04
    contrast = 0.7
    brightness = 0.2
    vibrancy = 0.3
}}

# Time — primary color, large centered
label {{
    monitor =
    text = cmd[update:1000] echo "$(date +%H:%M)"
    color = rgba({p_rgba})
    font_size = 88
    font_family = JetBrainsMono Nerd Font Bold
    position = 0, 140
    halign = center
    valign = center
    shadow_passes = 3
    shadow_size = 8
    shadow_color = rgba({p_shadow35})
}}

# Date — muted foreground, smaller
label {{
    monitor =
    text = cmd[update:60000] echo "$(date +"%A, %B %d")"
    color = rgba({fg_rgba})
    font_size = 20
    font_family = JetBrainsMono Nerd Font Bold
    position = 0, 70
    halign = center
    valign = center
    shadow_passes = 1
    shadow_size = 3
    shadow_color = rgba({black65})
}}

# Input field
input-field {{
    monitor =
    size = 300, 50
    outline_thickness = 3
    outline_color = rgba({p_rgba})
    dots_size = 0.3
    dots_spacing = 0.25
    dots_center = true
    inner_color = rgba({surf_rgba})
    font_color = rgba({fg_rgba})
    fade_on_empty = false
    placeholder_text = {pam_placeholder}
    hide_input = false
    check_color = rgba({succ_rgba})
    fail_color = rgba({danger_rgba})
    fail_text = {pam_fail_text}
    capslock_color = rgba({warn_rgba})
    position = 0, -50
    halign = center
    valign = center
    rounding = 0
    shadow_passes = 2
    shadow_size = 5
    shadow_color = rgba({p_shadow25})
}}
"""

    if dry_run:
        changes.append({
            "app": "hyprlock",
            "action": "dry-run",
            "path": str(hyprlock_conf),
            "wallpaper": existing_wallpaper,
        })
        return changes

    # Backup original before writing
    backup_path = backup_file(hyprlock_conf, backup_ts, "hyprlock/hyprlock.conf")

    # Write new config
    hyprlock_conf.parent.mkdir(parents=True, exist_ok=True)
    hyprlock_conf.write_text(config_content, encoding="utf-8")

    changes.append({
        "app": "hyprlock",
        "action": "write",
        "path": str(hyprlock_conf),
        "backup": backup_path,
        "wallpaper": existing_wallpaper,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — Kvantum (Qt widget style)
# ---------------------------------------------------------------------------

def materialize_kvantum(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set Kvantum widget style and theme."""
    changes = []
    kvantum_dir = HOME / ".config" / "Kvantum"
    kvantum_config = kvantum_dir / "kvantum.kvconfig"

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

    # Backup ONLY kvantum.kvconfig. kdeglobals is backed up in materialize_kde
    # (which runs first and takes the true pre-apply snapshot). Kvantum's own
    # change to kdeglobals is the widgetStyle key, which is restored via
    # `previous_widget_style` in the undo branch — no full-file backup needed.
    kvantum_backup = backup_file(kvantum_config, backup_ts, "kvantum/kvantum.kvconfig")

    # Write Kvantum config
    kvantum_dir.mkdir(parents=True, exist_ok=True)
    kvantum_config.write_text(f"[General]\ntheme={kvantum_theme}\n", encoding="utf-8")

    # Set widgetStyle in kdeglobals.
    # CRITICAL: value must be "kvantum" (exact Qt6 plugin name from libkvantum.so).
    # "kvantum-dark" is NOT a valid Qt6 style name and will silently fall back to Breeze.
    kwrite = _get_kwrite()
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
    kwrite = _get_kwrite()
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
    kwrite = _get_kwrite()
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
# APP HANDLERS — KDE lock screen (kscreenlocker greeter)
# ---------------------------------------------------------------------------

def materialize_kde_lockscreen(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the kscreenlocker greeter LnF to match palette brightness.

    The greeter inherits palette colors from kdeglobals automatically (materialize_kde
    handles that). This materializer sets the greeter chrome style — dark vs. light mode
    of the locker UI (input field, buttons, background tint) — via kscreenlockerrc
    [Greeter] Theme. No daemon restart needed; kscreenlocker reads config fresh on lock.
    """
    palette = design["palette"]
    kscreenlockerrc = HOME / ".config" / "kscreenlockerrc"
    changes = []

    greeter_theme = _lockscreen_lnf_for_palette(palette)

    if dry_run:
        changes.append({
            "app": "kde_lockscreen", "action": "dry-run",
            "greeter_theme": greeter_theme, "config_path": str(kscreenlockerrc),
        })
        return changes

    # Snapshot previous value for undo
    prev_theme = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kscreenlockerrc",
                                  "--group", "Greeter", "--key", "Theme"])
            if rc == 0 and out:
                prev_theme = out
            break

    kscreenlockerrc_backup = backup_file(kscreenlockerrc, backup_ts, "kscreenlocker/kscreenlockerrc")

    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kscreenlockerrc",
                 "--group", "Greeter", "--key", "Theme", greeter_theme])

    changes.append({
        "app": "kde_lockscreen", "action": "write",
        "greeter_theme": greeter_theme, "config_path": str(kscreenlockerrc),
        "backup": kscreenlockerrc_backup,
        "previous_theme": prev_theme,
    })
    return changes


def _lockscreen_lnf_for_palette(palette: dict) -> str:
    """Return breezedark or breeze LnF ID based on palette background brightness."""
    bg = palette.get("background", "#000000")
    # yiq_text_color returns "#ffffff" for dark backgrounds (needs white text)
    return (
        "org.kde.breezedark.desktop"
        if yiq_text_color(bg) == "#ffffff"
        else "org.kde.breeze.desktop"
    )


# ---------------------------------------------------------------------------
# WALLPAPER
# ---------------------------------------------------------------------------

def _snapshot_current_wallpaper(desktop: dict) -> tuple[str | None, str | None]:
    """Return (current_wallpaper_path, method_name) or (None, None).

    The method name matches what materialize_wallpaper uses when it records a
    change, so undo() can pick the right restore command. `file://` prefix is
    stripped from the path for direct use with the restore commands.
    """
    # KDE — read the live appletsrc even if snapshot_kde_state wasn't called.
    if desktop.get("wm") == "kde" and cmd_exists("plasma-apply-wallpaperimage"):
        appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
        if appletsrc.exists():
            m = re.search(r"^Image\s*=\s*(.+)$", appletsrc.read_text(errors="replace"), re.MULTILINE)
            if m:
                path = m.group(1).strip()
                if path.startswith("file://"):
                    path = path[len("file://"):]
                return path, "plasma-apply-wallpaperimage"
        return None, "plasma-apply-wallpaperimage"

    # awww (swww v0.12+ rename) — same query interface as swww.
    # Output format: "DP-1: 1920x1080, scale: 1, currently displaying: image: /path/to.png"
    # Note: `awww --get last-image` does NOT exist; `awww query` is the correct command.
    if cmd_exists("awww"):
        rc, out, _ = run_cmd(["awww", "query"], timeout=5)
        if rc == 0 and out:
            m = re.search(r"image:\s*(\S.*)$", out.splitlines()[0] if out.splitlines() else "")
            if m:
                return m.group(1).strip(), "awww img"
        return None, "awww img"

    # hyprpaper — read its config file
    if cmd_exists("hyprpaper"):
        hyprpaper_conf = HOME / ".config" / "hypr" / "hyprpaper.conf"
        if hyprpaper_conf.exists():
            for line in hyprpaper_conf.read_text().splitlines():
                m = re.match(r"^\s*wallpaper\s*=\s*[^,]*,\s*(\S+)", line)
                if m:
                    return m.group(1).strip(), "hyprpaper-config-rewrite"
        return None, "hyprpaper-config-rewrite"

    # swww — `swww query` emits per-monitor lines; grab the first image path
    if cmd_exists("swww"):
        rc, out, _ = run_cmd(["swww", "query"], timeout=5)
        if rc == 0 and out:
            # Output format: "DP-1: 1920x1080, scale: 1, currently displaying: image: /path/to.png"
            m = re.search(r"image:\s*(\S.*)$", out.splitlines()[0] if out.splitlines() else "")
            if m:
                return m.group(1).strip(), "swww img"
        return None, "swww img"

    # feh — ~/.fehbg is a shell script with the last --bg-* call
    if cmd_exists("feh"):
        fehbg = HOME / ".fehbg"
        if fehbg.exists():
            # Grab the last quoted absolute path in the script
            text = fehbg.read_text(errors="replace")
            m = re.findall(r"'(/[^']+)'", text)
            if m:
                return m[-1], "feh --bg-scale"
        return None, "feh --bg-scale"

    return None, None


def materialize_wallpaper(
    design: dict,
    wallpaper_path: str | None = None,
    backup_ts: str = "",
    dry_run: bool = False,
) -> list[dict]:
    if not wallpaper_path:
        return []

    # Resolve to absolute path
    wallpaper_path = str(Path(wallpaper_path).expanduser().resolve())

    changes = []
    desktop = discover_desktop()

    # Snapshot the current wallpaper BEFORE switching so `ricer undo` can restore it.
    prev_wallpaper, _ = _snapshot_current_wallpaper(desktop)

    if desktop["wm"] == "kde" and cmd_exists("plasma-apply-wallpaperimage"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "plasma-apply-wallpaperimage",
                            "previous_wallpaper": prev_wallpaper})
        else:
            run_cmd(["plasma-apply-wallpaperimage", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "plasma-apply-wallpaperimage",
                            "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("awww"):
        # awww (swww v0.12+ rename) — preferred Hyprland wallpaper daemon.
        # Ensure daemon is running first, then set image.
        # Note: if a specific monitor goes dark after switching wallpaper (known
        # Hyprland DPMS bug), run manually:
        #   hyprctl keyword monitor <NAME>,<WxH>@<Hz>,<POS>,1
        #   hyprctl dispatch dpms on <NAME>
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "awww img",
                            "previous_wallpaper": prev_wallpaper})
        else:
            # Start daemon if not running
            rc, _, _ = run_cmd(["pgrep", "awww-daemon"], timeout=3)
            if rc != 0:
                subprocess.Popen(["awww-daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                time.sleep(2)
            run_cmd(["awww", "img", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "awww img",
                            "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("hyprpaper"):
        # hyprpaper: rewrite config + restart daemon. IPC (socat/hyprctl hyprpaper)
        # is unreliable — wire protocol errors are common. Config rewrite is the
        # only method that works consistently.
        hyprpaper_conf = HOME / ".config" / "hypr" / "hyprpaper.conf"

        # Read existing config to find monitor names, or default to wildcard
        monitors = []
        if hyprpaper_conf.exists():
            for line in hyprpaper_conf.read_text().splitlines():
                m = re.match(r"^\s*wallpaper\s*=\s*(\S+)\s*,", line)
                if m:
                    monitors.append(m.group(1))
        if not monitors:
            # Detect monitors from hyprctl
            rc, out, _ = run_cmd(["hyprctl", "monitors", "-j"], timeout=5)
            if rc == 0:
                try:
                    for mon in json.loads(out):
                        monitors.append(mon.get("name", ""))
                except (json.JSONDecodeError, ValueError):
                    pass
        if not monitors:
            monitors = [""]  # empty = all monitors

        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "hyprpaper-config-rewrite", "monitors": monitors,
                            "previous_wallpaper": prev_wallpaper})
            return changes

        # Backup existing hyprpaper.conf
        backup_file(hyprpaper_conf, backup_ts, "hyprpaper/hyprpaper.conf")

        # Write new config
        hyprpaper_conf.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"preload = {wallpaper_path}"]
        for mon in monitors:
            lines.append(f"wallpaper = {mon}, {wallpaper_path}")
        lines.append("splash = false")
        hyprpaper_conf.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Restart hyprpaper daemon
        run_cmd(["pkill", "-x", "hyprpaper"])
        time.sleep(1)
        subprocess.Popen(["hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)

        changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                        "method": "hyprpaper-config-rewrite", "monitors": monitors,
                        "config_path": str(hyprpaper_conf),
                        "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("swww"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "swww img",
                            "previous_wallpaper": prev_wallpaper})
        else:
            run_cmd(["swww", "img", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "swww img",
                            "previous_wallpaper": prev_wallpaper})

    elif cmd_exists("feh"):
        if dry_run:
            changes.append({"app": "wallpaper", "action": "dry-run", "path": wallpaper_path,
                            "method": "feh --bg-scale",
                            "previous_wallpaper": prev_wallpaper})
        else:
            run_cmd(["feh", "--bg-scale", wallpaper_path])
            changes.append({"app": "wallpaper", "action": "set", "path": wallpaper_path,
                            "method": "feh --bg-scale",
                            "previous_wallpaper": prev_wallpaper})

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — Alacritty
# ---------------------------------------------------------------------------

def materialize_alacritty(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write colors.toml and inject import into alacritty.toml.

    Uses the template at templates/alacritty/colors.toml.template.
    Alacritty TOML import must come before other sections — inject at top.
    Also applies hue-rotation to bright color slots for variety (same as kitty).
    """
    palette = design["palette"]
    alacritty_dir = HOME / ".config" / "alacritty"
    template_path = TEMPLATES_DIR / "alacritty" / "colors.toml.template"
    colors_path = alacritty_dir / "colors.toml"
    toml_config = alacritty_dir / "alacritty.toml"
    changes = []

    context = {**palette, "name": design.get("name", "theme")}

    if template_path.exists():
        # Patch the [colors.bright] section BEFORE rendering so the {{key}}
        # placeholders are still present. Jinja2 (and simple_render) consume
        # them during render_template(), so patching after rendering would find
        # nothing to replace and silently produce un-adjusted bright colors.
        bright_map = {
            "{{muted}}":     adjust_lightness(palette["muted"], 1.4),
            "{{danger}}":    adjust_lightness(rotate_hue(palette["danger"], 15), 1.3),
            "{{success}}":   adjust_lightness(rotate_hue(palette["success"], 10), 1.3),
            "{{warning}}":   adjust_lightness(palette["warning"], 1.3),
            "{{primary}}":   adjust_lightness(rotate_hue(palette["primary"], -10), 1.3),
            "{{secondary}}": adjust_lightness(rotate_hue(palette["secondary"], 20), 1.3),
            "{{accent}}":    adjust_lightness(rotate_hue(palette["accent"], 15), 1.3),
            "{{foreground}}": adjust_lightness(palette["foreground"], 1.25),
        }
        template_str = template_path.read_text(encoding="utf-8")
        bright_start = template_str.find("[colors.bright]")
        if bright_start != -1:
            bright_section = template_str[bright_start:]
            for k, v in bright_map.items():
                bright_section = bright_section.replace(k, v, 1)
            template_str = template_str[:bright_start] + bright_section
        # Now render the pre-patched template through Jinja2 / simple_render
        if jinja2:
            env = jinja2.Environment()
            content = env.from_string(template_str).render(**context)
        else:
            content = simple_render(template_str, context)
    else:
        content = f"""# Generated by linux-ricing — {design.get('name', 'theme')}
[colors.primary]
background = "{palette['background']}"
foreground = "{palette['foreground']}"

[colors.cursor]
text   = "{palette['background']}"
cursor = "{palette['accent']}"

[colors.selection]
text       = "{palette['background']}"
background = "{palette['primary']}"

[colors.normal]
black   = "{palette['surface']}"
red     = "{palette['danger']}"
green   = "{palette['success']}"
yellow  = "{palette['warning']}"
blue    = "{palette['primary']}"
magenta = "{palette['secondary']}"
cyan    = "{palette['accent']}"
white   = "{palette['foreground']}"

[colors.bright]
black   = "{adjust_lightness(palette['muted'], 1.4)}"
red     = "{adjust_lightness(rotate_hue(palette['danger'], 15), 1.3)}"
green   = "{adjust_lightness(rotate_hue(palette['success'], 10), 1.3)}"
yellow  = "{adjust_lightness(palette['warning'], 1.3)}"
blue    = "{adjust_lightness(rotate_hue(palette['primary'], -10), 1.3)}"
magenta = "{adjust_lightness(rotate_hue(palette['secondary'], 20), 1.3)}"
cyan    = "{adjust_lightness(rotate_hue(palette['accent'], 15), 1.3)}"
white   = "{adjust_lightness(palette['foreground'], 1.25)}"
"""

    if dry_run:
        changes.append({"app": "alacritty", "action": "dry-run", "path": str(colors_path)})
        return changes

    alacritty_dir.mkdir(parents=True, exist_ok=True)

    colors_backup = backup_file(colors_path, backup_ts, "alacritty/colors.toml")
    toml_backup = backup_file(toml_config, backup_ts, "alacritty/alacritty.toml")

    colors_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "alacritty", "action": "write",
        "path": str(colors_path), "backup": colors_backup,
    })

    # Inject import at the top of alacritty.toml (must precede other sections)
    import_line = 'import = ["~/.config/alacritty/colors.toml"]'
    hermes_marker = "# linux-ricing"
    injected = False

    if toml_config.exists():
        toml_text = toml_config.read_text(encoding="utf-8")
        if "colors.toml" not in toml_text:
            toml_config.write_text(
                f"{hermes_marker}\n{import_line}\n\n" + toml_text,
                encoding="utf-8"
            )
            injected = True
    else:
        toml_config.write_text(f"{hermes_marker}\n{import_line}\n", encoding="utf-8")
        injected = True

    changes.append({
        "app": "alacritty", "action": "inject_import",
        "path": str(toml_config), "backup": toml_backup,
        "injected": injected, "marker": hermes_marker,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — picom (X11 compositor)
# ---------------------------------------------------------------------------

def materialize_picom(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write a picom theme fragment and @include it into picom.conf.

    Derives shadow color from the primary palette key — matches window border
    tones for a coherent glow effect. Uses @include (libconfig / picom >= 10).
    Falls back to prepending include if picom.conf doesn't already have @includes.
    """
    palette = design["palette"]
    picom_dir = HOME / ".config" / "picom"
    picom_conf = picom_dir / "picom.conf"
    fragment_path = picom_dir / "hermes-picom.conf"
    template_path = TEMPLATES_DIR / "picom" / "hermes-picom.conf.template"
    changes = []

    if not template_path.exists():
        print(f"[picom] template not found, skipping: {template_path}", file=sys.stderr)
        return changes

    shadow_color = adjust_lightness(palette["primary"], 0.25)
    context = {**palette, "name": design.get("name", "theme"), "shadow_color": shadow_color}
    fragment_content = render_template(template_path, context)

    if dry_run:
        changes.append({"app": "picom", "action": "dry-run", "path": str(fragment_path)})
        return changes

    picom_dir.mkdir(parents=True, exist_ok=True)

    fragment_backup = backup_file(fragment_path, backup_ts, "picom/hermes-picom.conf")
    picom_backup = backup_file(picom_conf, backup_ts, "picom/picom.conf")

    fragment_path.write_text(fragment_content, encoding="utf-8")
    changes.append({
        "app": "picom", "action": "write",
        "path": str(fragment_path), "backup": fragment_backup,
    })

    hermes_marker = "# linux-ricing"
    include_line = f'@include "{fragment_path}";'
    injected = False

    if picom_conf.exists():
        picom_text = picom_conf.read_text(encoding="utf-8")
        if "hermes-picom.conf" not in picom_text:
            picom_conf.write_text(
                f"{hermes_marker}\n{include_line}\n\n" + picom_text,
                encoding="utf-8"
            )
            injected = True
    else:
        picom_conf.write_text(
            f"{hermes_marker}\n{include_line}\n\n"
            "# Hermes wrote this starter config. Add your own settings below:\n"
            "backend = \"glx\";\nvsync = true;\n",
            encoding="utf-8"
        )
        injected = True

    changes.append({
        "app": "picom", "action": "inject_include",
        "path": str(picom_conf), "backup": picom_backup,
        "injected": injected, "marker": hermes_marker,
    })

    run_cmd(["pkill", "-HUP", "picom"], timeout=3)

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — fastfetch (terminal greeting)
# ---------------------------------------------------------------------------

def materialize_fastfetch(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Rewrite ~/.config/fastfetch/config.json with palette-derived colors and icons.

    fastfetch has no include system — full rewrite every time.
    File must be config.json (not config.jsonc); fastfetch silently ignores .jsonc.
    Separator character and icons adapt to mood_tags so the greeting matches the theme.
    """
    palette = design["palette"]
    mood_tags = design.get("mood_tags", [])
    name = design.get("name", "theme")
    fastfetch_dir = HOME / ".config" / "fastfetch"
    config_path = fastfetch_dir / "config.json"
    changes = []

    # Theme-appropriate separator and icon set
    if any(t in mood_tags for t in ["gothic", "blood", "fantasy", "dark-fantasy"]):
        separator = " ♦ "
    elif any(t in mood_tags for t in ["game", "rpg", "maplestory", "pixel"]):
        separator = " ♥ "
    elif any(t in mood_tags for t in ["void", "dragon", "cyber", "neon"]):
        separator = " 𑁍 "
    else:
        separator = " ─ "

    config = {
        "logo": {
            "type": "auto",
            "color": {"1": palette["primary"].lstrip("#"), "2": palette["accent"].lstrip("#")}
        },
        "display": {
            "separator": separator,
            "color": {
                "title": palette["primary"].lstrip("#"),
                "keys": palette["accent"].lstrip("#"),
                "separator": palette["warning"].lstrip("#"),
            }
        },
        "modules": [
            {"type": "title", "key": f"  {name.upper()}",
             "keyColor": palette["primary"].lstrip("#")},
            {"type": "separator", "string": "─"},
            {"type": "os",       "key": "  OS",     "keyColor": palette["primary"].lstrip("#")},
            {"type": "kernel",   "key": "  Kernel", "keyColor": palette["accent"].lstrip("#")},
            {"type": "uptime",   "key": "  Uptime", "keyColor": palette["success"].lstrip("#")},
            {"type": "de",       "key": "  WM",     "keyColor": palette["secondary"].lstrip("#")},
            {"type": "terminal", "key": "  Term",   "keyColor": palette["primary"].lstrip("#")},
            {"type": "shell",    "key": "  Shell",  "keyColor": palette["accent"].lstrip("#")},
            {"type": "cpu",      "key": "  CPU",    "keyColor": palette["warning"].lstrip("#")},
            {"type": "memory",   "key": "  RAM",    "keyColor": palette["danger"].lstrip("#")},
            {"type": "colors",   "paddingLeft": 2,  "symbol": "circle"},
        ]
    }

    if dry_run:
        changes.append({"app": "fastfetch", "action": "dry-run", "path": str(config_path)})
        return changes

    fastfetch_dir.mkdir(parents=True, exist_ok=True)
    config_backup = backup_file(config_path, backup_ts, "fastfetch/config.json")

    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    changes.append({
        "app": "fastfetch", "action": "write",
        "path": str(config_path), "backup": config_backup,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — mako (Wayland notification daemon)
# ---------------------------------------------------------------------------

def materialize_mako(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write ~/.config/mako/config with palette colors.

    mako uses flat key=value format with optional [criteria] sections.
    Full rewrite — mako has no include system.
    Corner radius adapts to mood: 0px for angular/game themes, 8px otherwise.
    """
    palette = design["palette"]
    mako_dir = HOME / ".config" / "mako"
    config_path = mako_dir / "config"
    template_path = TEMPLATES_DIR / "mako" / "config.template"
    changes = []

    if not template_path.exists():
        print(f"[mako] template not found, skipping: {template_path}", file=sys.stderr)
        return changes

    mood_tags = design.get("mood_tags", [])
    corner_radius = 0 if any(t in mood_tags for t in ["gothic", "game", "angular", "sharp"]) else 8
    context = {**palette, "name": design.get("name", "theme"), "corner_radius": corner_radius}
    content = render_template(template_path, context)

    if dry_run:
        changes.append({"app": "mako", "action": "dry-run", "path": str(config_path)})
        return changes

    mako_dir.mkdir(parents=True, exist_ok=True)
    config_backup = backup_file(config_path, backup_ts, "mako/config")

    config_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "mako", "action": "write",
        "path": str(config_path), "backup": config_backup,
    })

    run_cmd(["makoctl", "reload"], timeout=3)

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — wofi (Wayland launcher)
# ---------------------------------------------------------------------------

def materialize_wofi(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write ~/.config/wofi/style.css with palette colors.

    wofi uses GTK CSS. Full rewrite — no include system.
    Border-radius adapts to mood tags (0px for sharp/game themes).
    YIQ ensures readable text on selected (primary-background) items.
    """
    palette = design["palette"]
    wofi_dir = HOME / ".config" / "wofi"
    style_path = wofi_dir / "style.css"
    template_path = TEMPLATES_DIR / "wofi" / "style.css.template"
    changes = []

    if not template_path.exists():
        print(f"[wofi] template not found, skipping: {template_path}", file=sys.stderr)
        return changes

    mood_tags = design.get("mood_tags", [])
    radius = "0px" if any(t in mood_tags for t in ["gothic", "game", "angular", "sharp"]) else "8px"
    selected_text = yiq_text_color(palette["primary"])
    context = {**palette, "name": design.get("name", "theme"),
               "radius": radius, "selected_text": selected_text}
    content = render_template(template_path, context)

    if dry_run:
        changes.append({"app": "wofi", "action": "dry-run", "path": str(style_path)})
        return changes

    wofi_dir.mkdir(parents=True, exist_ok=True)
    style_backup = backup_file(style_path, backup_ts, "wofi/style.css")

    style_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "wofi", "action": "write",
        "path": str(style_path), "backup": style_backup,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — GTK / Qt theming
# ---------------------------------------------------------------------------

def materialize_gtk(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Apply GTK theme, icon theme, and cursor theme via gsettings + settings.ini.

    Writes gtk-3.0 and gtk-4.0 settings.ini for cross-toolkit coverage.
    Chooses dark vs light base from background luminance (YIQ).
    Respects design system fields gtk_theme, icon_theme, cursor_theme if set.
    gsettings calls apply immediately for running GTK apps (GNOME/KDE/Hyprland).
    """
    palette = design["palette"]
    template_path = TEMPLATES_DIR / "gtk" / "settings.ini.template"
    changes = []

    r, g, b = hex_to_rgb_tuple(palette["background"])
    luminance = (r * 299 + g * 587 + b * 114) / 1000
    is_dark = luminance < 128

    gtk_theme = design.get("gtk_theme", "Adwaita-dark" if is_dark else "Adwaita")
    icon_theme = design.get("icon_theme", "Papirus-Dark" if is_dark else "Papirus")
    cursor_theme = design.get("cursor_theme", "default")

    context = {
        **palette,
        "name": design.get("name", "theme"),
        "gtk_theme": gtk_theme,
        "icon_theme": icon_theme,
        "cursor_theme": cursor_theme,
        "font_name": "JetBrains Mono 10",
        "prefer_dark": "1" if is_dark else "0",
    }
    settings_content = render_template(template_path, context)

    if dry_run:
        changes.append({"app": "gtk", "action": "dry-run",
                        "gtk_theme": gtk_theme, "icon_theme": icon_theme,
                        "cursor_theme": cursor_theme, "dark": is_dark})
        return changes

    for gtk_dir_name in ["gtk-3.0", "gtk-4.0"]:
        gtk_dir = HOME / ".config" / gtk_dir_name
        gtk_dir.mkdir(parents=True, exist_ok=True)
        settings_path = gtk_dir / "settings.ini"
        backup = backup_file(settings_path, backup_ts, f"gtk/{gtk_dir_name}/settings.ini")
        settings_path.write_text(settings_content, encoding="utf-8")
        changes.append({
            "app": "gtk", "action": "write",
            "path": str(settings_path), "backup": backup,
        })

    # Live-apply via gsettings (works on GNOME, most Wayland compositors)
    if cmd_exists("gsettings"):
        schema = "org.gnome.desktop.interface"
        for key, val in [
            ("gtk-theme", gtk_theme),
            ("icon-theme", icon_theme),
            ("cursor-theme", cursor_theme),
        ]:
            rc, _, _ = run_cmd(["gsettings", "set", schema, key, val])
            changes.append({
                "app": "gtk", "action": "gsettings",
                "key": key, "value": val, "success": rc == 0,
            })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — polybar (X11 status bar)
# ---------------------------------------------------------------------------

def materialize_polybar(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write hermes-colors.ini and inject include-file into polybar config.ini.

    polybar colors are namespaced in a [colors] section and referenced as
    ${colors.primary} throughout bar/module configs — so injecting a separate
    colors file is cleaner than patching inline hex values.
    """
    palette = design["palette"]
    polybar_dir = HOME / ".config" / "polybar"
    config_path = polybar_dir / "config.ini"
    colors_path = polybar_dir / "hermes-colors.ini"
    template_path = TEMPLATES_DIR / "polybar" / "hermes-colors.ini.template"
    changes = []

    if not template_path.exists():
        print(f"[polybar] template not found, skipping: {template_path}", file=sys.stderr)
        return changes

    context = {**palette, "name": design.get("name", "theme")}
    colors_content = render_template(template_path, context)

    if dry_run:
        changes.append({"app": "polybar", "action": "dry-run", "path": str(colors_path)})
        return changes

    polybar_dir.mkdir(parents=True, exist_ok=True)

    colors_backup = backup_file(colors_path, backup_ts, "polybar/hermes-colors.ini")
    config_backup = backup_file(config_path, backup_ts, "polybar/config.ini")

    colors_path.write_text(colors_content, encoding="utf-8")
    changes.append({
        "app": "polybar", "action": "write",
        "path": str(colors_path), "backup": colors_backup,
    })

    hermes_marker = "; linux-ricing"
    include_line = f"include-file = {colors_path}"
    injected = False

    if config_path.exists():
        config_text = config_path.read_text(encoding="utf-8")
        if "hermes-colors.ini" not in config_text:
            config_path.write_text(
                f"{hermes_marker}\n{include_line}\n\n" + config_text,
                encoding="utf-8"
            )
            injected = True
    else:
        config_path.write_text(
            f"{hermes_marker}\n{include_line}\n\n"
            "; Add your [bar/...] and [module/...] configs below\n",
            encoding="utf-8"
        )
        injected = True

    changes.append({
        "app": "polybar", "action": "inject_include",
        "path": str(config_path), "backup": config_backup,
        "injected": injected, "marker": hermes_marker,
    })

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — swaync (SwayNotificationCenter)
# ---------------------------------------------------------------------------

def materialize_swaync(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write ~/.config/swaync/style.css for notification popups and center panel.

    swaync uses GTK CSS. Full rewrite — targets popup notifications and
    the side-panel notification center. Border-radius adapts to mood tags.
    """
    palette = design["palette"]
    swaync_dir = HOME / ".config" / "swaync"
    style_path = swaync_dir / "style.css"
    template_path = TEMPLATES_DIR / "swaync" / "style.css.template"
    changes = []

    if not template_path.exists():
        print(f"[swaync] template not found, skipping: {template_path}", file=sys.stderr)
        return changes

    mood_tags = design.get("mood_tags", [])
    radius = "0px" if any(t in mood_tags for t in ["gothic", "game", "angular", "sharp"]) else "8px"
    selected_text = yiq_text_color(palette["primary"])
    danger_text = yiq_text_color(palette["danger"])
    context = {**palette, "name": design.get("name", "theme"),
               "radius": radius, "selected_text": selected_text, "danger_text": danger_text}
    content = render_template(template_path, context)

    if dry_run:
        changes.append({"app": "swaync", "action": "dry-run", "path": str(style_path)})
        return changes

    swaync_dir.mkdir(parents=True, exist_ok=True)
    style_backup = backup_file(style_path, backup_ts, "swaync/style.css")

    style_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "swaync", "action": "write",
        "path": str(style_path), "backup": style_backup,
    })

    run_cmd(["swaync-client", "--reload-css"], timeout=3)

    return changes


# ---------------------------------------------------------------------------
# APP HANDLERS — starship (cross-shell prompt)
# ---------------------------------------------------------------------------

def materialize_starship(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write ~/.config/starship.toml with palette-derived colors.

    Uses Starship's [palettes.*] feature to map all 10 design slots as named
    colors, then styles the common prompt modules to reference those slots.
    This is a full rewrite — any previous starship.toml is replaced.
    """
    palette = design["palette"]
    raw_name = design.get("name", "rice")
    theme_name = re.sub(r"[^a-zA-Z0-9-]+", "-", raw_name).strip("-") or "rice"
    config_path = HOME / ".config" / "starship.toml"
    changes = []

    content = _build_starship_toml(palette, theme_name)

    if dry_run:
        changes.append({"app": "starship", "action": "dry-run", "path": str(config_path)})
        return changes

    config_backup = backup_file(config_path, backup_ts, "starship/starship.toml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")
    changes.append({
        "app": "starship", "action": "write",
        "path": str(config_path), "backup": config_backup,
    })

    return changes


def _build_starship_toml(palette: dict, theme_name: str) -> str:
    """Build a starship.toml using the [palettes.*] feature for named color slots."""
    p = palette
    lines = [
        f'palette = "{theme_name}"',
        "",
        f"[palettes.{theme_name}]",
        f'background = "{p["background"]}"',
        f'foreground = "{p["foreground"]}"',
        f'primary    = "{p["primary"]}"',
        f'secondary  = "{p["secondary"]}"',
        f'accent     = "{p["accent"]}"',
        f'surface    = "{p["surface"]}"',
        f'muted      = "{p["muted"]}"',
        f'danger     = "{p["danger"]}"',
        f'success    = "{p["success"]}"',
        f'warning    = "{p["warning"]}"',
        "",
        "[character]",
        'success_symbol = "[❯](bold $success)"',
        'error_symbol   = "[❯](bold $danger)"',
        "",
        "[directory]",
        'style = "bold $primary"',
        "",
        "[git_branch]",
        'style = "bold $secondary"',
        "",
        "[git_status]",
        'style = "bold $warning"',
        "",
        "[cmd_duration]",
        'style       = "bold $muted"',
        "min_time    = 2000",
        "",
        "[username]",
        'style_user = "bold $accent"',
        'style_root = "bold $danger"',
        "show_always = false",
        "",
        "[hostname]",
        'style    = "bold $accent"',
        "ssh_only = true",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MATERIALIZATION ORCHESTRATOR
# ---------------------------------------------------------------------------

APP_MATERIALIZERS = {
    # KDE stack
    "kde":            materialize_kde,
    "kvantum":        materialize_kvantum,
    "plasma_theme":   materialize_plasma_theme,
    "cursor":         materialize_cursor,
    "kde_lockscreen": materialize_kde_lockscreen,
    # Terminals
    "kitty": materialize_kitty,
    "alacritty": materialize_alacritty,
    "konsole": materialize_konsole,
    # Bars
    "waybar": materialize_waybar,
    "polybar": materialize_polybar,
    # Launchers
    "rofi": materialize_rofi,
    "wofi": materialize_wofi,
    # Notifications
    "dunst": materialize_dunst,
    "mako": materialize_mako,
    "swaync": materialize_swaync,
    # Hyprland
    "hyprland": materialize_hyprland,
    "hyprlock": materialize_hyprlock,
    # System
    "gtk": materialize_gtk,
    "picom": materialize_picom,
    "fastfetch": materialize_fastfetch,
    "starship": materialize_starship,
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
    backup_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
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
                            "config_backup", "kdeglobals_backup"]:
            bp = change.get(backup_key)

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
                    dest = Path(change["config_path"]) if "config_path" in change else HOME / ".config" / "waybar" / "config"
                elif backup_key == "kdeglobals_backup":
                    dest = HOME / ".config" / "kdeglobals"
                else:
                    continue

                try:
                    shutil.copy2(bp, dest)
                    restored.append({"app": app, "restored": str(dest), "from": bp})
                except (OSError, shutil.Error) as e:
                    failed.append({"app": app, "path": str(dest), "error": str(e)})

            elif bp and not Path(bp).exists():
                # Backup path recorded but file is gone — delete what we created
                dest_path = change.get("path")
                if dest_path and Path(dest_path).exists():
                    try:
                        Path(dest_path).unlink()
                        restored.append({"app": app, "deleted": dest_path, "note": "no backup existed — file was new, deleted"})
                    except OSError as e:
                        failed.append({"app": app, "path": dest_path, "error": str(e)})

        # ---- Remove injected include/theme/import lines ----
        if action in ("inject_include", "inject_theme", "inject_import") and change.get("injected"):
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
            kwrite = _get_kwrite()

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
            kwrite = _get_kwrite()
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
            kwrite = _get_kwrite()
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

        # ---- Wallpaper: restore previous using the same method that set it ----
        if app == "wallpaper" and action == "set":
            prev = change.get("previous_wallpaper")
            method = change.get("method", "")
            if not prev:
                skipped.append({"app": "wallpaper", "note": "no previous wallpaper recorded (likely pre-fix manifest)"})
            elif method == "plasma-apply-wallpaperimage" and cmd_exists("plasma-apply-wallpaperimage"):
                rc, _, err = run_cmd(["plasma-apply-wallpaperimage", prev], timeout=10)
                if rc == 0:
                    restored.append({"app": "wallpaper", "action": "restored", "path": prev, "method": method})
                else:
                    failed.append({"app": "wallpaper", "action": "restore", "path": prev, "error": err or f"exit code {rc}"})
            elif method == "awww img" and cmd_exists("awww"):
                rc, _, err = run_cmd(["awww", "img", prev], timeout=10)
                if rc == 0:
                    restored.append({"app": "wallpaper", "action": "restored", "path": prev, "method": method})
                else:
                    failed.append({"app": "wallpaper", "action": "restore", "path": prev, "error": err or f"exit code {rc}"})
            elif method == "swww img" and cmd_exists("swww"):
                rc, _, err = run_cmd(["swww", "img", prev], timeout=10)
                if rc == 0:
                    restored.append({"app": "wallpaper", "action": "restored", "path": prev, "method": method})
                else:
                    failed.append({"app": "wallpaper", "action": "restore", "path": prev, "error": err or f"exit code {rc}"})
            elif method == "feh --bg-scale" and cmd_exists("feh"):
                rc, _, err = run_cmd(["feh", "--bg-scale", prev], timeout=10)
                if rc == 0:
                    restored.append({"app": "wallpaper", "action": "restored", "path": prev, "method": method})
                else:
                    failed.append({"app": "wallpaper", "action": "restore", "path": prev, "error": err or f"exit code {rc}"})
            elif method == "hyprpaper-config-rewrite":
                # The config file is already restored from backup by the generic file-restore
                # loop above. We just need to restart the daemon so the restored config takes effect.
                run_cmd(["pkill", "-x", "hyprpaper"])
                time.sleep(1)
                if cmd_exists("hyprpaper"):
                    subprocess.Popen(["hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=True)
                restored.append({"app": "wallpaper", "action": "restored", "path": prev, "method": method})
            else:
                skipped.append({"app": "wallpaper", "note": f"unknown or unavailable method: {method!r}"})

    # Mark manifest as undone
    manifest["undone"] = True
    manifest["undone_at"] = datetime.now(timezone.utc).isoformat()
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
        "kvantum_theme": "catppuccin-mocha-blue",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-blue-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
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
        # Nord primary is a teal-blue; catppuccin-mocha-teal is the closest Kvantum match.
        "kvantum_theme": "catppuccin-mocha-teal",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-teal-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
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
        # KvDark: neutral fallback; no Kvantum theme closely matches gruvbox warm tones.
        "kvantum_theme": "KvDark",
        "plasma_theme": "default",
        "cursor_theme": "Adwaita",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
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
        "kvantum_theme": "catppuccin-mocha-mauve",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-mauve-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
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
        "kvantum_theme": "catppuccin-mocha-blue",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-blue-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
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
        # Primary is a soft teal; catppuccin-mocha-teal is the closest available accent.
        "kvantum_theme": "catppuccin-mocha-teal",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-teal-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
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
        "kvantum_theme": "catppuccin-mocha-sapphire",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-sapphire-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
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
        # Primary is gold; catppuccin-mocha-yellow is the closest Kvantum accent.
        "kvantum_theme": "catppuccin-mocha-yellow",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-yellow-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["dark", "gothic", "gold", "dragonfable"],
    },
    "void-dragon": {
        "name": "void-dragon",
        "description": "Deep void sky, cyan soul blade, gold filigree, dark teal dragon aura. Dark fantasy palette built around a deep navy void and ice-blue primary.",
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
        # Suggested Kvantum themes for the cyan primary:
        # catppuccin-mocha-teal (balanced), catppuccin-mocha-sky (brighter),
        # catppuccin-mocha-sapphire (deeper blue).
        "kvantum_theme": "catppuccin-mocha-teal",
        "plasma_theme": "default",
        # Suggested cursor: catppuccin-macchiato-teal-cursors (matches cyan primary).
        "cursor_theme": "catppuccin-macchiato-teal-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["void", "dragon", "cyan", "gold", "dark-fantasy"],
    },
    "shiva-temple": {
        "name": "shiva-temple",
        "description": "Lord Shiva's haunted temple — cosmic void, third-eye indigo, vermillion sindoor, temple gold.",
        "palette": {
            "background": "#0a0b1a", "foreground": "#d8d0c8", "primary": "#5b4fcf",
            "secondary": "#1a1824", "accent": "#c44820", "surface": "#151320",
            "muted": "#3a3040", "danger": "#b81830", "success": "#387048", "warning": "#c89020",
        },
        "kvantum_theme": "catppuccin-mocha-mauve",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-mauve-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["shiva", "temple", "cosmic", "indigo", "vermillion", "dark", "sacred"],
    },
    "bareblood": {
        "name": "bareblood",
        "description": "Gothic maximalist dark fantasy. Blood reds, wine blacks, muted rose-grey. Zero blues — amber fills the cyan role. Inspired by BAREBLOOD (github.com/v1ewp0rt/BAREBLOOD).",
        "palette": {
            "background": "#140607",
            "foreground": "#685259",
            "primary":    "#cc1133",
            "secondary":  "#3d2130",
            "accent":     "#e8a766",
            "surface":    "#3b0d10",
            "muted":      "#180000",
            "danger":     "#c5245c",
            "success":    "#579523",
            "warning":    "#aa301b",
        },
        # KvDark is the canonical built-in dark Kvantum theme present on most installs.
        # BreezeDark is a native Qt/KDE style, NOT a Kvantum theme — do not use it here.
        "kvantum_theme": "KvDark",
        "plasma_theme": "default",
        "cursor_theme": "default",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["gothic", "maximalist", "blood", "wine", "fantasy", "bareblood"],
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
    apply_parser.add_argument("--design", default=None, help="Path to design_system.json (omit with --extract)")
    apply_parser.add_argument("--wallpaper", default=None, help="Wallpaper image path")
    apply_parser.add_argument("--extract", action="store_true",
                              help="Derive palette from --wallpaper instead of reading --design")
    apply_parser.add_argument("--name", default=None, help="Theme name override when using --extract")
    apply_parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    apply_parser.add_argument("--only", default=None,
                              help="Restrict to this app key or element category (e.g. 'kitty', 'terminal')")
    apply_parser.add_argument("--app", default=None,
                              help="Specific sub-app to materialize (e.g. 'kitty' within 'terminal')")

    preset_parser = subparsers.add_parser("preset", help="Apply a named preset")
    preset_parser.add_argument("name", choices=list(PRESETS.keys()), help="Preset name")
    preset_parser.add_argument("--dry-run", action="store_true")

    extract_parser = subparsers.add_parser("extract", help="Extract a design system from an image")
    extract_parser.add_argument("--image", required=True, help="Path to image (wallpaper/reference)")
    extract_parser.add_argument("--out", default=None, help="Write JSON here (default: stdout)")
    extract_parser.add_argument("--name", default=None, help="Theme name (default: image stem)")

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

    if args.command == "extract":
        try:
            from palette_extractor import extract_palette
        except ImportError as e:
            print(f"extract: {e}", file=sys.stderr)
            sys.exit(1)
        try:
            design = extract_palette(args.image, name=args.name)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"extract: {e}", file=sys.stderr)
            sys.exit(1)
        output = json.dumps(design, indent=2)
        if args.out:
            Path(args.out).expanduser().write_text(output + "\n", encoding="utf-8")
            print(f"wrote {args.out}", file=sys.stderr)
        else:
            print(output)
        return

    if args.command == "apply":
        if args.extract:
            if not args.wallpaper:
                print("apply --extract requires --wallpaper", file=sys.stderr)
                sys.exit(2)
            try:
                from palette_extractor import extract_palette
            except ImportError as e:
                print(f"apply --extract: {e}", file=sys.stderr)
                sys.exit(1)
            try:
                design = extract_palette(args.wallpaper, name=args.name)
            except (FileNotFoundError, RuntimeError) as e:
                print(f"apply --extract: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            if not args.design:
                print("apply requires --design (or --extract with --wallpaper)", file=sys.stderr)
                sys.exit(2)
            with open(args.design, "r", encoding="utf-8") as f:
                design = json.load(f)
        # --app / --only: restrict materialization to a specific materializer key.
        # Fail closed: an unknown target must never fall back to applying all apps.
        only_app = args.app or args.only  # --app takes precedence
        if not only_app:
            print("apply requires --only or --app to target exactly one materializer", file=sys.stderr)
            sys.exit(2)
        if only_app not in APP_MATERIALIZERS:
            print(f"Unknown materializer: {only_app}", file=sys.stderr)
            sys.exit(2)
        all_detected = discover_apps()
        if only_app not in all_detected:
            print(f"Materializer not detected: {only_app}", file=sys.stderr)
            sys.exit(2)
        only_apps = {only_app: all_detected[only_app]}
        manifest = materialize(design, apps=only_apps, wallpaper=args.wallpaper, dry_run=args.dry_run)
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
            if action in ("inject_include", "inject_theme", "inject_import") and change.get("injected"):
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
