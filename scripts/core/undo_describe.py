"""core/undo_describe.py — Human-readable preview of a pending undo operation.

Extracted from scripts/ricer_undo.py to keep that file within the 300-line budget.
"""
from pathlib import Path


def _describe_change(change: dict) -> list[str]:
    """Return human-readable lines describing what undo would do for one change record.

    Used by the 'simulate-undo' CLI command to preview the undo plan.
    """
    lines  = []
    app    = change.get("app", "?")
    action = change.get("action", "?")

    if action == "error":
        lines.append(f"  [{app}] SKIPPED (errored during apply): {change.get('error')}")
        return lines

    for bk in ("backup", "backup_profile", "backup_colors", "backup_konsolerc", "config_backup"):
        val  = change.get(bk)
        dest = change.get("path") or change.get("profile_path") or change.get("color_scheme_path")
        if val:
            exists = Path(val).exists()
            lines.append(f"  [{app}] RESTORE {dest}")
            lines.append(f"         from    {val}  ({'EXISTS' if exists else 'MISSING — would delete dest'})")

    if action in ("inject_include", "inject_theme", "inject_import") and change.get("injected"):
        lines.append(f"  [{app}] REMOVE injected block from {change.get('path')}")
        lines.append(f"         marker: {change.get('marker')}")

    if app == "kde" and action in ("reload", "write"):
        prev = change.get("previous_colorscheme")
        if prev:
            lines.append(f"  [kde]  REAPPLY colorscheme: {prev}")

    if app == "kvantum" and action == "write":
        prev_kv = change.get("previous_kvantum_theme")
        prev_ws = change.get("previous_widget_style")
        if prev_kv:
            lines.append(f"  [kvantum] RESTORE theme:       {prev_kv}")
        lines.append(f"  [kvantum] RESTORE widgetStyle: {prev_ws}" if prev_ws
                     else "  [kvantum] DELETE widgetStyle key (was not set)")

    if app == "plasma_theme" and action == "write":
        prev = change.get("previous_theme")
        lines.append(f"  [plasma_theme] RESTORE: {prev}" if prev
                     else "  [plasma_theme] No previous theme recorded — will skip")

    if app == "cursor" and action == "write":
        prev = change.get("previous_cursor")
        lines.append(f"  [cursor] RESTORE: {prev}" if prev
                     else "  [cursor] No previous cursor recorded — will skip")

    return lines
