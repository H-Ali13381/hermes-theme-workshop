"""KDE sub-system materializers: Kvantum, Plasma theme, cursor, icon theme, lock screen."""
import os

from core.constants import HOME
from core.colors import is_dark_palette
from core.process import run_cmd, cmd_exists, _get_kwrite
from core.backup import backup_file
from core.config_parsers import _read_kvantum_theme

# Optional icon theme generator
icon_theme_gen = None
try:
    import icon_theme_gen  # type: ignore[import]
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Kvantum
# ---------------------------------------------------------------------------

def materialize_kvantum(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set Kvantum widget style and theme."""
    changes = []
    kvantum_dir = HOME / ".config" / "Kvantum"
    kvantum_config = kvantum_dir / "kvantum.kvconfig"

    kvantum_theme = design.get("kvantum_theme")
    if not kvantum_theme:
        return []

    if dry_run:
        changes.append({"app": "kvantum", "action": "dry-run", "theme": kvantum_theme, "config_path": str(kvantum_config)})
        return changes

    prev_kvantum_theme = _read_kvantum_theme(kvantum_config) if kvantum_config.exists() else None
    prev_widget_style = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle"])
            if rc == 0 and out:
                prev_widget_style = out
                break

    kvantum_backup = backup_file(kvantum_config, backup_ts, "kvantum/kvantum.kvconfig")
    kvantum_dir.mkdir(parents=True, exist_ok=True)
    kvantum_config.write_text(f"[General]\ntheme={kvantum_theme}\n", encoding="utf-8")

    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", "kvantum"])

    if cmd_exists("qdbus6"):
        run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)

    changes.append({
        "app": "kvantum", "action": "write",
        "theme": kvantum_theme, "config_path": str(kvantum_config),
        "backup": kvantum_backup,
        "previous_kvantum_theme": prev_kvantum_theme,
        "previous_widget_style": prev_widget_style,
    })
    return changes


# ---------------------------------------------------------------------------
# Plasma theme
# ---------------------------------------------------------------------------

def materialize_plasma_theme(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the Plasma desktop theme (panel SVGs, task buttons, etc.)."""
    changes = []
    plasma_theme = design.get("plasma_theme")
    if not plasma_theme:
        return changes

    plasmarc = HOME / ".config" / "plasmarc"
    if dry_run:
        changes.append({"app": "plasma_theme", "action": "dry-run", "theme": plasma_theme, "config_path": str(plasmarc)})
        return changes

    prev_theme = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "plasmarc", "--group", "Theme", "--key", "name"])
            if rc == 0 and out:
                prev_theme = out
                break

    plasmarc_backup = backup_file(plasmarc, backup_ts, "plasma/plasmarc")
    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "plasmarc", "--group", "Theme", "--key", "name", plasma_theme])
    if cmd_exists("plasma-apply-desktoptheme"):
        run_cmd(["plasma-apply-desktoptheme", plasma_theme])

    changes.append({"app": "plasma_theme", "action": "write", "theme": plasma_theme,
                    "config_path": str(plasmarc), "backup": plasmarc_backup, "previous_theme": prev_theme})
    return changes


# ---------------------------------------------------------------------------
# Cursor
# ---------------------------------------------------------------------------

def materialize_cursor(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the cursor theme."""
    changes = []
    cursor_theme = design.get("cursor_theme")
    if not cursor_theme:
        return changes

    kcminputrc = HOME / ".config" / "kcminputrc"
    if dry_run:
        changes.append({"app": "cursor", "action": "dry-run", "theme": cursor_theme, "config_path": str(kcminputrc)})
        return changes

    prev_cursor = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme"])
            if rc == 0 and out:
                prev_cursor = out
                break

    cursor_backup = backup_file(kcminputrc, backup_ts, "cursor/kcminputrc")
    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", cursor_theme])
    if cmd_exists("plasma-apply-cursortheme"):
        run_cmd(["plasma-apply-cursortheme", cursor_theme])

    changes.append({"app": "cursor", "action": "write", "theme": cursor_theme,
                    "config_path": str(kcminputrc), "backup": cursor_backup, "previous_cursor": prev_cursor})
    return changes


# ---------------------------------------------------------------------------
# Icon theme
# ---------------------------------------------------------------------------

def materialize_icon_theme(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the KDE icon theme, generating one via recolor or fal.ai if not installed."""
    changes = []
    icon_theme = design.get("icon_theme")
    if not icon_theme:
        return changes

    if dry_run:
        changes.append({"app": "icon_theme", "action": "dry-run", "theme": icon_theme, "generated": False})
        return changes

    generated = False
    if icon_theme_gen is not None and not icon_theme_gen.is_installed(icon_theme):
        palette = design.get("palette", {})
        is_dark = is_dark_palette(palette)
        base = "breeze-dark" if is_dark else "breeze"
        new_theme = icon_theme_gen.create_palette_icon_theme(design, base_theme=base)
        if new_theme:
            icon_theme = new_theme
            generated = True
            changes.append({"app": "icon_theme", "action": "generated-recolor", "base_theme": base, "theme": icon_theme})
        else:
            fal_key = os.environ.get("FAL_KEY", "").strip()
            if fal_key:
                theme_name = f"{design.get('name', 'rice')}-icons"
                icon_dir = HOME / ".local" / "share" / "icons" / theme_name / "apps"
                ok = icon_theme_gen.generate_icon_via_fal(design, fal_key, icon_dir)
                if ok:
                    out_root = HOME / ".local" / "share" / "icons" / theme_name
                    icon_theme_gen._write_index_theme(
                        out_root, theme_name, f"{base},hicolor",
                        [s for s in (22, 48) if (icon_dir / str(s)).exists()],
                    )
                    icon_theme_gen._update_icon_cache(out_root)
                    icon_theme = theme_name
                    generated = True
                    changes.append({"app": "icon_theme", "action": "generated-fal", "theme": icon_theme})

    prev_icon_theme = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kdeglobals", "--group", "Icons", "--key", "Theme"])
            if rc == 0 and out:
                prev_icon_theme = out
                break

    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", icon_theme])
    if cmd_exists("qdbus6"):
        run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)

    changes.append({"app": "icon_theme", "action": "write", "theme": icon_theme,
                    "generated": generated, "previous_icon_theme": prev_icon_theme})
    return changes


# ---------------------------------------------------------------------------
# KDE lock screen
# ---------------------------------------------------------------------------

def _lockscreen_lnf_for_palette(palette: dict) -> str:
    """Return breezedark or breeze LnF ID based on palette background brightness."""
    return "org.kde.breezedark.desktop" if is_dark_palette(palette) else "org.kde.breeze.desktop"


def materialize_kde_lockscreen(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the kscreenlocker greeter LnF to match palette brightness."""
    palette = design["palette"]
    kscreenlockerrc = HOME / ".config" / "kscreenlockerrc"
    changes = []

    greeter_theme = _lockscreen_lnf_for_palette(palette)

    if dry_run:
        changes.append({"app": "kde_lockscreen", "action": "dry-run",
                        "greeter_theme": greeter_theme, "config_path": str(kscreenlockerrc)})
        return changes

    prev_theme = None
    for tool in ["kreadconfig6", "kreadconfig5"]:
        if cmd_exists(tool):
            rc, out, _ = run_cmd([tool, "--file", "kscreenlockerrc", "--group", "Greeter", "--key", "Theme"])
            if rc == 0 and out:
                prev_theme = out
                break

    kscreenlockerrc_backup = backup_file(kscreenlockerrc, backup_ts, "kscreenlocker/kscreenlockerrc")
    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kscreenlockerrc", "--group", "Greeter", "--key", "Theme", greeter_theme])

    changes.append({"app": "kde_lockscreen", "action": "write",
                    "greeter_theme": greeter_theme, "config_path": str(kscreenlockerrc),
                    "backup": kscreenlockerrc_backup, "previous_theme": prev_theme})
    return changes
