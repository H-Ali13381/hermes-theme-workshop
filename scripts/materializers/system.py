"""System-level materializers: GTK, Picom, Fastfetch, Starship prompt."""
import json
import re
import sys

from core.constants import HOME, TEMPLATES_DIR
from core.colors import is_dark_palette, yiq_text_color, adjust_lightness
from core.process import run_cmd, cmd_exists
from core.backup import backup_file
from core.templates import render_template


# ---------------------------------------------------------------------------
# GTK
# ---------------------------------------------------------------------------

def materialize_gtk(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Apply GTK theme, icon theme, and cursor theme via gsettings + settings.ini."""
    palette = design["palette"]
    template_path = TEMPLATES_DIR / "gtk" / "settings.ini.template"
    changes = []

    is_dark = is_dark_palette(palette)
    gtk_theme    = design.get("gtk_theme",    "Adwaita-dark" if is_dark else "Adwaita")
    icon_theme   = design.get("icon_theme",   "Papirus-Dark" if is_dark else "Papirus")
    cursor_theme = design.get("cursor_theme", "default")

    ui_font = design.get("typography", {}).get("ui_font", "JetBrains Mono")
    context = {
        **palette,
        "name": design.get("name", "theme"),
        "gtk_theme": gtk_theme,
        "icon_theme": icon_theme,
        "cursor_theme": cursor_theme,
        "font_name": f"{ui_font} 10",
        "prefer_dark": "1" if is_dark else "0",
    }
    settings_content = render_template(template_path, context)

    if dry_run:
        changes.append({"app": "gtk", "action": "dry-run", "gtk_theme": gtk_theme,
                        "icon_theme": icon_theme, "cursor_theme": cursor_theme, "dark": is_dark})
        return changes

    for gtk_dir_name in ["gtk-3.0", "gtk-4.0"]:
        gtk_dir = HOME / ".config" / gtk_dir_name
        gtk_dir.mkdir(parents=True, exist_ok=True)
        settings_path = gtk_dir / "settings.ini"
        backup = backup_file(settings_path, backup_ts, f"gtk/{gtk_dir_name}/settings.ini")
        settings_path.write_text(settings_content, encoding="utf-8")
        changes.append({"app": "gtk", "action": "write", "path": str(settings_path), "backup": backup})

    if cmd_exists("gsettings"):
        schema = "org.gnome.desktop.interface"
        for key, val in [("gtk-theme", gtk_theme), ("icon-theme", icon_theme), ("cursor-theme", cursor_theme)]:
            rc, _, _ = run_cmd(["gsettings", "set", schema, key, val])
            changes.append({"app": "gtk", "action": "gsettings", "key": key, "value": val, "success": rc == 0})

    return changes


# ---------------------------------------------------------------------------
# Picom
# ---------------------------------------------------------------------------

def materialize_picom(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write a picom theme fragment and @include it into picom.conf."""
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
    changes.append({"app": "picom", "action": "write", "path": str(fragment_path), "backup": fragment_backup})

    hermes_marker = "# linux-ricing"
    include_line = f'@include "{fragment_path}";'
    injected = False
    if picom_conf.exists():
        picom_text = picom_conf.read_text(encoding="utf-8")
        if "hermes-picom.conf" not in picom_text:
            picom_conf.write_text(f"{hermes_marker}\n{include_line}\n\n" + picom_text, encoding="utf-8")
            injected = True
    else:
        picom_conf.write_text(
            f"{hermes_marker}\n{include_line}\n\n"
            "# Hermes wrote this starter config. Add your own settings below:\n"
            'backend = "glx";\nvsync = true;\n',
            encoding="utf-8"
        )
        injected = True

    changes.append({"app": "picom", "action": "inject_include", "path": str(picom_conf),
                    "backup": picom_backup, "injected": injected, "marker": hermes_marker})
    run_cmd(["pkill", "-HUP", "picom"], timeout=3)
    return changes


# ---------------------------------------------------------------------------
# Fastfetch
# ---------------------------------------------------------------------------

def materialize_fastfetch(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Rewrite ~/.config/fastfetch/config.json with palette-derived colors."""
    palette = design["palette"]
    mood_tags = design.get("mood_tags", [])
    name = design.get("name", "theme")
    fastfetch_dir = HOME / ".config" / "fastfetch"
    config_path = fastfetch_dir / "config.json"
    changes = []

    if any(t in mood_tags for t in ["gothic", "blood", "fantasy", "dark-fantasy"]):
        separator = " ♦ "
    elif any(t in mood_tags for t in ["game", "rpg", "maplestory", "pixel"]):
        separator = " ♥ "
    elif any(t in mood_tags for t in ["void", "dragon", "cyber", "neon"]):
        separator = " 𑁍 "
    else:
        separator = " ─ "

    config = {
        "logo":    {"type": "auto", "color": {"1": palette["primary"].lstrip("#"), "2": palette["accent"].lstrip("#")}},
        "display": {"separator": separator, "color": {
            "title": palette["primary"].lstrip("#"),
            "keys":  palette["accent"].lstrip("#"),
            "separator": palette["warning"].lstrip("#"),
        }},
        "modules": [
            {"type": "title",    "key": f"  {name.upper()}",  "keyColor": palette["primary"].lstrip("#")},
            {"type": "separator","string": "─"},
            {"type": "os",       "key": "  OS",     "keyColor": palette["primary"].lstrip("#")},
            {"type": "kernel",   "key": "  Kernel", "keyColor": palette["accent"].lstrip("#")},
            {"type": "uptime",   "key": "  Uptime", "keyColor": palette["success"].lstrip("#")},
            {"type": "de",       "key": "  WM",     "keyColor": palette["secondary"].lstrip("#")},
            {"type": "terminal", "key": "  Term",   "keyColor": palette["primary"].lstrip("#")},
            {"type": "shell",    "key": "  Shell",  "keyColor": palette["accent"].lstrip("#")},
            {"type": "cpu",      "key": "  CPU",    "keyColor": palette["warning"].lstrip("#")},
            {"type": "memory",   "key": "  RAM",    "keyColor": palette["danger"].lstrip("#")},
            {"type": "colors",   "paddingLeft": 2,  "symbol": "circle"},
        ],
    }

    if dry_run:
        changes.append({"app": "fastfetch", "action": "dry-run", "path": str(config_path)})
        return changes

    fastfetch_dir.mkdir(parents=True, exist_ok=True)
    config_backup = backup_file(config_path, backup_ts, "fastfetch/config.json")
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    changes.append({"app": "fastfetch", "action": "write", "path": str(config_path), "backup": config_backup})
    return changes


# ---------------------------------------------------------------------------
# Starship prompt
# ---------------------------------------------------------------------------

def materialize_starship(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Write ~/.config/starship.toml with palette-derived colors."""
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
    changes.append({"app": "starship", "action": "write", "path": str(config_path), "backup": config_backup})
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
