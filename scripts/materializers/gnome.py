"""GNOME Shell and lock-screen materializers.

window_decorations:gnome — writes a gnome-shell.css theme under
  ~/.local/share/themes/hermes-<name>/gnome-shell/ and applies the
  matching color-scheme preference via gsettings.

lock_screen:gnome — applies palette colors to the GNOME screensaver
  (lock screen background tint) via gsettings without requiring root.
"""
from __future__ import annotations

from core.constants import HOME
from core.colors import is_dark_palette
from core.process import run_cmd, cmd_exists
from core.backup import backup_file


# ---------------------------------------------------------------------------
# GNOME Shell theme
# ---------------------------------------------------------------------------

def _build_gnome_shell_css(palette: dict, theme_name: str) -> str:
    """Return a minimal gnome-shell.css that applies the palette."""
    bg   = palette["background"]
    fg   = palette["foreground"]
    pri  = palette["primary"]
    surf = palette["surface"]
    mut  = palette["muted"]
    acc  = palette["accent"]

    return f"""\
/* Hermes GNOME Shell theme: {theme_name} */
/* Generated — do not edit by hand.       */

stage {{
  color: {fg};
}}

/* Top bar */
#panel {{
  background-color: {bg};
  color: {fg};
  border-bottom: 1px solid {surf};
}}

#panel .panel-button {{
  color: {fg};
}}

#panel .panel-button:hover,
#panel .panel-button:active {{
  background-color: {surf};
  color: {pri};
}}

/* Overview / dash */
.dash-background {{
  background-color: {bg};
  border: 1px solid {surf};
  border-radius: 12px;
}}

.dash-item-container .overview-icon:hover {{
  background-color: {surf};
}}

/* App search results */
.search-result-content {{
  background-color: {surf};
  color: {fg};
  border-radius: 8px;
}}

/* Notifications */
.notification-banner {{
  background-color: {surf};
  color: {fg};
  border: 1px solid {mut};
  border-radius: 8px;
}}

/* System menu (quick settings) */
.quick-settings {{
  background-color: {bg};
  color: {fg};
}}

.quick-toggle {{
  background-color: {surf};
  color: {fg};
  border-radius: 8px;
}}

.quick-toggle:checked {{
  background-color: {pri};
  color: {acc};
}}

/* Calendar / date in quick settings */
.datemenu-today-button {{
  color: {pri};
}}

/* Workspace switcher */
.workspace-thumbnail-indicator {{
  border: 2px solid {pri};
  border-radius: 4px;
}}
"""


def materialize_gnome_shell(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Apply a GNOME Shell theme from the palette.

    Writes ~/.local/share/themes/hermes-<name>/gnome-shell/gnome-shell.css
    and sets the color-scheme gsettings key so GTK4/Libadwaita apps follow
    the dark/light preference automatically.
    """
    palette    = design["palette"]
    theme_name = f"hermes-{design.get('name', 'gnome')}"
    theme_dir  = HOME / ".local" / "share" / "themes" / theme_name / "gnome-shell"
    css_path   = theme_dir / "gnome-shell.css"
    is_dark    = is_dark_palette(palette)
    color_scheme = "prefer-dark" if is_dark else "default"
    changes: list[dict] = []

    if dry_run:
        changes.append({
            "app": "gnome_shell", "action": "dry-run",
            "path": str(css_path), "color_scheme": color_scheme,
            "description": f"Would write GNOME Shell theme '{theme_name}' and set color-scheme={color_scheme}",
        })
        return changes

    theme_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_file(css_path, backup_ts, "gnome-shell/gnome-shell.css")
    css_path.write_text(_build_gnome_shell_css(palette, theme_name), encoding="utf-8")
    changes.append({
        "app": "gnome_shell", "action": "write",
        "path": str(css_path), "backup": backup,
    })

    if cmd_exists("gsettings"):
        rc, _, _ = run_cmd(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", color_scheme])
        changes.append({
            "app": "gnome_shell", "action": "gsettings",
            "key": "color-scheme", "value": color_scheme, "success": rc == 0,
        })

    return changes


# ---------------------------------------------------------------------------
# GNOME lock screen
# ---------------------------------------------------------------------------

def materialize_gnome_lockscreen(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Apply palette colors to the GNOME lock / screensaver screen.

    Sets org.gnome.desktop.screensaver primary-color and secondary-color so
    the solid-color fallback behind the lock screen artwork matches the theme.
    No root access is required — all writes go through gsettings.
    """
    palette  = design["palette"]
    changes: list[dict] = []

    gsettings_pairs = [
        ("org.gnome.desktop.screensaver", "primary-color",   palette["background"]),
        ("org.gnome.desktop.screensaver", "secondary-color", palette["surface"]),
        # Mirror the color-scheme preference on the screensaver schema too
        ("org.gnome.desktop.screensaver", "color-shading-type", "solid"),
    ]

    if dry_run:
        changes.append({
            "app": "gnome_lockscreen", "action": "dry-run",
            "gsettings": [(s, k) for s, k, _ in gsettings_pairs],
            "description": "Would set GNOME screensaver palette colors via gsettings",
        })
        return changes

    if not cmd_exists("gsettings"):
        changes.append({
            "app": "gnome_lockscreen", "action": "skipped",
            "reason": "gsettings not found",
        })
        return changes

    for schema, key, val in gsettings_pairs:
        rc, _, _ = run_cmd(["gsettings", "set", schema, key, val])
        changes.append({
            "app": "gnome_lockscreen", "action": "gsettings",
            "schema": schema, "key": key, "value": val, "success": rc == 0,
        })

    return changes
