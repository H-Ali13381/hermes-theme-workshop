"""Hyprland and Hyprlock materializers."""
import re

from core.constants import HOME
from core.colors import hex_to_rgb_tuple, is_dark_palette
from core.process import run_cmd, cmd_exists
from core.backup import backup_file
from core.config_parsers import _patch_hypr_conf_key, _hyprlock_background_path
from desktop_utils import discover_desktop


# ---------------------------------------------------------------------------
# Hyprland border colors
# ---------------------------------------------------------------------------

def materialize_hyprland(design: dict, backup_ts: str, dry_run: bool = False,
                          desktop: dict | None = None) -> list[dict]:
    """Set Hyprland window border colors from the palette."""
    palette = design["palette"]
    changes = []

    if desktop is None:
        desktop = discover_desktop()
    if desktop.get("wm") != "hyprland":
        return changes

    hyprland_conf = HOME / ".config" / "hypr" / "hyprland.conf"
    primary_hex   = palette["primary"].lstrip("#")
    accent_hex    = palette["accent"].lstrip("#")
    secondary_hex = palette["secondary"].lstrip("#")

    active_border   = f"rgba({primary_hex}ee) rgba({accent_hex}ee) 45deg"
    inactive_border = f"rgba({secondary_hex}aa)"

    if dry_run:
        changes.append({"app": "hyprland", "action": "dry-run",
                        "active_border": active_border, "inactive_border": inactive_border})
        return changes

    run_cmd(["hyprctl", "keyword", "general:col.active_border",   active_border])
    run_cmd(["hyprctl", "keyword", "general:col.inactive_border", inactive_border])

    hyprland_backup = None
    if hyprland_conf.exists():
        hyprland_backup = backup_file(hyprland_conf, backup_ts, "hyprland/hyprland.conf")
        content = hyprland_conf.read_text(encoding="utf-8", errors="replace")
        new_content, found_active   = _patch_hypr_conf_key(content,      "col.active_border",   active_border)
        new_content, found_inactive = _patch_hypr_conf_key(new_content,  "col.inactive_border", inactive_border)

        if not found_active:
            new_content = re.sub(
                r"(border_size\s*=\s*\d+\n)",
                rf"\1    col.active_border = {active_border}\n",
                new_content, count=1,
            )
        if not found_inactive:
            new_content = re.sub(
                r"(col\.active_border\s*=\s*[^\n]+\n)",
                rf"\1    col.inactive_border = {inactive_border}\n",
                new_content, count=1,
            )

        if new_content != content:
            hyprland_conf.write_text(new_content, encoding="utf-8")

    changes.append({"app": "hyprland", "action": "set_borders",
                    "active_border": active_border, "inactive_border": inactive_border,
                    "path": str(hyprland_conf), "backup": hyprland_backup,
                    "config_path": str(hyprland_conf)})
    return changes


# ---------------------------------------------------------------------------
# Hyprlock lock screen
# ---------------------------------------------------------------------------

def materialize_hyprlock(design: dict, backup_ts: str, dry_run: bool = False,
                          desktop: dict | None = None) -> list[dict]:
    """Materialize hyprlock lock screen from the design palette."""
    palette = design["palette"]
    changes = []

    if desktop is None:
        desktop = discover_desktop()
    if desktop.get("wm") != "hyprland":
        return changes

    hyprlock_conf = HOME / ".config" / "hypr" / "hyprlock.conf"
    theme_name = design.get("name", "linux-ricing")

    p_r, p_g, p_b       = hex_to_rgb_tuple(palette["primary"])
    fg_r, fg_g, fg_b    = hex_to_rgb_tuple(palette["foreground"])
    surf_r, surf_g, surf_b = hex_to_rgb_tuple(palette["surface"])
    danger_r, danger_g, danger_b = hex_to_rgb_tuple(palette["danger"])
    succ_r, succ_g, succ_b   = hex_to_rgb_tuple(palette["success"])
    warn_r, warn_g, warn_b   = hex_to_rgb_tuple(palette["warning"])

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

    existing_wallpaper = None
    if hyprlock_conf.exists():
        existing_wallpaper = _hyprlock_background_path(hyprlock_conf.read_text(encoding="utf-8", errors="replace"))

    if not existing_wallpaper:
        from materializers.wallpaper import _snapshot_current_wallpaper
        existing_wallpaper, _ = _snapshot_current_wallpaper(desktop)
        if not existing_wallpaper:
            existing_wallpaper = ""

    mood_tags = design.get("mood_tags", [])
    if "maplestory" in mood_tags or "game" in mood_tags:
        pam_placeholder = '<span foreground="#d4a012">HP: ∞ | MP: ∞</span>'
        pam_fail_text   = '<span foreground="#cc1133"><b>☠ ACCESS DENIED</b></span>'
    elif "gothic" in mood_tags or "dark-fantasy" in mood_tags:
        pam_placeholder = '<span foreground="#685259">Enter passphrase...</span>'
        pam_fail_text   = '<span foreground="#cc1133"><b>✖ WRONG</b></span>'
    elif "void" in mood_tags or "dragon" in mood_tags:
        pam_placeholder = '<span foreground="#7ad4f0">Void gate passphrase...</span>'
        pam_fail_text   = '<span foreground="#cc3090"><b>⚔ DENIED</b></span>'
    else:
        pam_placeholder = f'<span foreground="{palette["accent"]}">Enter password...</span>'
        pam_fail_text   = f'<span foreground="{palette["danger"]}"><b>✖ Access Denied</b></span>'

    config_content = _build_hyprlock_config(
        theme_name, existing_wallpaper,
        p_rgba, fg_rgba, surf_rgba, danger_rgba, succ_rgba, warn_rgba,
        p_shadow35, black65, p_shadow25,
        pam_placeholder, pam_fail_text,
    )

    if dry_run:
        changes.append({"app": "hyprlock", "action": "dry-run",
                        "path": str(hyprlock_conf), "wallpaper": existing_wallpaper})
        return changes

    backup_path = backup_file(hyprlock_conf, backup_ts, "hyprlock/hyprlock.conf")
    hyprlock_conf.parent.mkdir(parents=True, exist_ok=True)
    hyprlock_conf.write_text(config_content, encoding="utf-8")
    changes.append({"app": "hyprlock", "action": "write",
                    "path": str(hyprlock_conf), "backup": backup_path, "wallpaper": existing_wallpaper})
    return changes


def _build_hyprlock_config(
    theme_name, wallpaper,
    p_rgba, fg_rgba, surf_rgba, danger_rgba, succ_rgba, warn_rgba,
    p_shadow35, black65, p_shadow25,
    pam_placeholder, pam_fail_text,
) -> str:
    return f"""# ═══════════════════════════════════════════════════════════════════
# HERMES-RICER — {theme_name} Lock Screen
# Generated by linux-ricing — do not edit manually
# ═══════════════════════════════════════════════════════════════════

background {{
    monitor =
    path = {wallpaper}
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
