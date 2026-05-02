"""EWW (ElKowars Wacky Widgets) materializer.

Writes two files into ~/.config/eww/:
  hermes-palette.scss  — 10-slot palette as SCSS variables + custom chrome
  hermes-theme.yuck    — EWW top bar, side telemetry, focus card, and dock

Then injects:
  @import "hermes-palette.scss";   into eww.scss  (creates the file if absent)
  (include "./hermes-theme.yuck")  into eww.yuck  (creates the file if absent)

Finally starts/reloads EWW and opens the generated windows so KDE has visible
custom widget chrome instead of only a stock Plasma toolbar.

Undo:
  - "write"          changes → _restore_backed_up_files restores / deletes the file
  - "inject_include" changes → _undo_injections removes the marker + directive line
  - "open"           changes → _undo_eww closes Hermes windows and reloads the daemon
                               so the live state drops the now-removed config
"""
from __future__ import annotations

import sys

from core.constants import HOME, TEMPLATES_DIR
from core.process import run_cmd, cmd_exists
from core.backup import backup_file
from core.templates import render_template


# ---------------------------------------------------------------------------
# Public materializer
# ---------------------------------------------------------------------------

HERMES_WIDGET_WINDOWS = ["hermes-top-bar", "hermes-side-stack", "hermes-focus-card", "hermes-bottom-dock"]
HERMES_CHROME_WINDOWS = ["hermes-terminal-frame", "hermes-window-frame"]

def materialize_eww(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Generate and install EWW custom chrome from the design system."""
    palette    = design["palette"]
    typography = design.get("typography", {})
    eww_dir    = HOME / ".config" / "eww"

    palette_path = eww_dir / "hermes-palette.scss"
    yuck_path    = eww_dir / "hermes-theme.yuck"
    eww_scss     = eww_dir / "eww.scss"
    eww_yuck     = eww_dir / "eww.yuck"

    palette_tmpl = TEMPLATES_DIR / "eww" / "hermes-palette.scss.template"
    yuck_tmpl    = TEMPLATES_DIR / "eww" / "hermes-theme.yuck.template"

    changes: list[dict] = []

    for tmpl in (palette_tmpl, yuck_tmpl):
        if not tmpl.exists():
            print(f"[eww] template not found, skipping: {tmpl}", file=sys.stderr)
            return changes

    context = {
        **palette,
        "name":       design.get("name", "theme"),
        "ui_font":    typography.get("ui_font", "Sans"),
        "monospace":  typography.get("monospace", "Monospace"),
    }

    palette_content = render_template(palette_tmpl, context)
    yuck_content    = render_template(yuck_tmpl,    context)

    if dry_run:
        changes.append({
            "app": "eww", "action": "dry-run",
            "path": str(palette_path), "yuck_path": str(yuck_path),
            "windows": _windows_for_design(design),
        })
        return changes

    eww_dir.mkdir(parents=True, exist_ok=True)

    # ── Write hermes-palette.scss ────────────────────────────────────────────
    palette_backup = backup_file(palette_path, backup_ts, "eww/hermes-palette.scss")
    palette_path.write_text(palette_content, encoding="utf-8")
    changes.append({
        "app": "eww", "action": "write",
        "path": str(palette_path), "backup": palette_backup,
    })

    # ── Write hermes-theme.yuck ──────────────────────────────────────────────
    yuck_backup = backup_file(yuck_path, backup_ts, "eww/hermes-theme.yuck")
    yuck_path.write_text(yuck_content, encoding="utf-8")
    changes.append({
        "app": "eww", "action": "write",
        "path": str(yuck_path), "backup": yuck_backup,
    })

    # ── Inject @import into eww.scss ─────────────────────────────────────────
    scss_marker     = "/* linux-ricing */"
    scss_marker_end = "/* end-linux-ricing */"
    import_line  = '@import "hermes-palette.scss";'
    scss_injected = False
    if eww_scss.exists():
        scss_text = eww_scss.read_text(encoding="utf-8")
        if scss_marker not in scss_text:
            eww_scss.write_text(
                f"{scss_marker}\n{import_line}\n{scss_marker_end}\n\n" + scss_text,
                encoding="utf-8",
            )
            scss_injected = True
    else:
        eww_scss.write_text(
            f"{scss_marker}\n{import_line}\n{scss_marker_end}\n", encoding="utf-8"
        )
        scss_injected = True
    changes.append({
        "app": "eww", "action": "inject_include", "path": str(eww_scss),
        "injected": scss_injected, "import_line": import_line,
        "marker": scss_marker, "marker_end": scss_marker_end,
    })

    # ── Inject (include ...) into eww.yuck ──────────────────────────────────
    yuck_marker     = "; linux-ricing"
    yuck_marker_end = "; end-linux-ricing"
    include_line  = '(include "./hermes-theme.yuck")'
    yuck_injected = False
    if eww_yuck.exists():
        yuck_text = eww_yuck.read_text(encoding="utf-8")
        if yuck_marker not in yuck_text:
            eww_yuck.write_text(
                f"{yuck_marker}\n{include_line}\n{yuck_marker_end}\n\n" + yuck_text,
                encoding="utf-8",
            )
            yuck_injected = True
    else:
        eww_yuck.write_text(
            f"{yuck_marker}\n{include_line}\n{yuck_marker_end}\n", encoding="utf-8"
        )
        yuck_injected = True
    changes.append({
        "app": "eww", "action": "inject_include", "path": str(eww_yuck),
        "injected": yuck_injected, "import_line": include_line,
        "marker": yuck_marker, "marker_end": yuck_marker_end,
    })

    # ── Start/reload/open EWW windows so the widget chrome is actually visible ─
    if cmd_exists("eww"):
        run_cmd(["eww", "daemon"], timeout=5)
        reload_rc, _, _ = run_cmd(["eww", "reload"], timeout=5)
        windows = _windows_for_design(design)
        opened: list[str] = []
        for window in windows:
            rc, _, _ = run_cmd(["eww", "open", window], timeout=5)
            if rc == 0:
                opened.append(window)
        if reload_rc == 0 or opened:
            changes.append({"app": "eww", "action": "open", "windows": opened})
        else:
            print(
                "[eww] EWW installed but daemon not running — "
                "start with: eww daemon && eww open-many " + " ".join(windows),
                file=sys.stderr,
            )

    return changes


def _windows_for_design(design: dict) -> list[str]:
    """Open only the EWW surfaces justified by the user's design."""
    chrome = design.get("chrome_strategy", {}) if isinstance(design, dict) else {}
    method = str(chrome.get("method", "")).lower() if isinstance(chrome, dict) else ""
    targets = " ".join(str(t).lower() for t in chrome.get("implementation_targets", [])) if isinstance(chrome, dict) else ""
    needs_chrome = any(term in method or term in targets for term in ("frame", "border", "overlay", "eww"))
    windows: list[str] = []
    if design.get("widget_layout") or design.get("panel_layout"):
        windows.extend(HERMES_WIDGET_WINDOWS)
    if needs_chrome:
        windows.extend(HERMES_CHROME_WINDOWS)
    return windows or HERMES_CHROME_WINDOWS
