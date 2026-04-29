"""scripts/ricer_undo.py — Undo / rollback system for Hermes Ricer.

Exports:
  undo()            — execute full rollback of the last materialization
  _describe_change  — used by 'simulate-undo' CLI command
  _APP_UNDO_HANDLERS — per-app dispatch table (used by undo())
"""
from __future__ import annotations

# ── stdlib ───────────────────────────────────────────────────────────────────
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

# ── bootstrap: honour sys.path set up by ricer.py (already done at import) ──
# core imports are relative to scripts/ which is already on sys.path
from core.constants import HOME, CURRENT_DIR              # noqa: E402
from core.backup import _remove_injected_block            # noqa: E402
from core.process import run_cmd, cmd_exists, _get_kwrite  # noqa: E402
from core.undo_describe import _describe_change           # noqa: E402


# ---------------------------------------------------------------------------
# FILE-LEVEL RESTORE
# ---------------------------------------------------------------------------

def _restore_backed_up_files(change: dict, restored: list, failed: list) -> None:
    """Restore any backed-up files referenced in a change record."""
    app = change.get("app", "unknown")
    for backup_key in ("backup", "backup_profile", "backup_colors",
                       "backup_konsolerc", "config_backup", "kdeglobals_backup"):
        bp = change.get(backup_key)
        if not bp:
            continue
        if Path(bp).exists():
            if backup_key == "backup" and "path" in change:
                dest = Path(change["path"])
            elif backup_key == "backup_profile" and "profile_path" in change:
                dest = Path(change["profile_path"])
            elif backup_key == "backup_colors" and "color_scheme_path" in change:
                dest = Path(change["color_scheme_path"])
            elif backup_key == "backup_konsolerc":
                dest = HOME / ".config" / "konsolerc"
            elif backup_key == "config_backup":
                dest = (Path(change["config_path"]) if "config_path" in change
                        else HOME / ".config" / "waybar" / "config")
            elif backup_key == "kdeglobals_backup":
                dest = HOME / ".config" / "kdeglobals"
            else:
                continue
            try:
                shutil.copy2(bp, dest)
                restored.append({"app": app, "restored": str(dest), "from": bp})
            except (OSError, shutil.Error) as e:
                failed.append({"app": app, "path": str(dest), "error": str(e)})
        else:
            # Backup gone — delete the file we created
            dest_path = change.get("path")
            if dest_path and Path(dest_path).exists():
                try:
                    Path(dest_path).unlink()
                    restored.append({"app": app, "deleted": dest_path,
                                     "note": "no backup existed — file was new, deleted"})
                except OSError as e:
                    failed.append({"app": app, "path": dest_path, "error": str(e)})


def _undo_injections(change: dict, restored: list, skipped: list) -> None:
    """Remove hermes-injected include/theme/import blocks from config files."""
    if change.get("action") not in ("inject_include", "inject_theme", "inject_import"):
        return
    if not change.get("injected"):
        return
    app = change.get("app", "unknown")
    path, marker = change.get("path"), change.get("marker")
    if path and marker:
        if _remove_injected_block(Path(path), marker):
            restored.append({"app": app, "action": "removed_injection", "path": path})
        else:
            skipped.append({"app": app, "path": path,
                            "note": "injection marker not found (may already be clean)"})


# ---------------------------------------------------------------------------
# PER-APP UNDO HANDLERS
# ---------------------------------------------------------------------------

def _undo_kde(change: dict, restored: list, failed: list, skipped: list) -> None:
    if change.get("action") not in ("reload", "write"):
        return
    prev = change.get("previous_colorscheme")
    if not prev:
        return
    if cmd_exists("plasma-apply-colorscheme"):
        rc, _, _ = run_cmd(["plasma-apply-colorscheme", prev], timeout=10)
        if rc == 0:
            restored.append({"app": "kde", "action": "restored_colorscheme", "scheme": prev})
        else:
            failed.append({"app": "kde", "action": "restore_colorscheme",
                           "scheme": prev, "error": f"exit code {rc}"})
    else:
        skipped.append({"app": "kde",
                        "note": "plasma-apply-colorscheme not found; previous scheme: " + prev})


def _undo_kvantum(change: dict, restored: list, failed: list, skipped: list) -> None:
    if change.get("action") != "write":
        return
    prev_kv = change.get("previous_kvantum_theme")
    prev_ws = change.get("previous_widget_style")
    kwrite = _get_kwrite()
    if prev_kv:
        kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
        kvantum_config.parent.mkdir(parents=True, exist_ok=True)
        kvantum_config.write_text(f"[General]\ntheme={prev_kv}\n", encoding="utf-8")
        restored.append({"app": "kvantum", "action": "restored_theme", "theme": prev_kv})
    if prev_ws and kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", prev_ws])
        restored.append({"app": "kvantum", "action": "restored_widgetStyle", "style": prev_ws})
    elif not prev_ws and kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", "--delete"])
        restored.append({"app": "kvantum", "action": "cleared_widgetStyle"})
    if cmd_exists("qdbus6"):
        run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)


def _undo_plasma_theme(change: dict, restored: list, failed: list, skipped: list) -> None:
    if change.get("action") != "write":
        return
    prev = change.get("previous_theme")
    kwrite = _get_kwrite()
    if prev and kwrite:
        run_cmd([kwrite, "--file", "plasmarc", "--group", "Theme", "--key", "name", prev])
    if prev and cmd_exists("plasma-apply-desktoptheme"):
        rc, _, _ = run_cmd(["plasma-apply-desktoptheme", prev], timeout=10)
        if rc == 0:
            restored.append({"app": "plasma_theme", "action": "restored", "theme": prev})
        else:
            failed.append({"app": "plasma_theme", "action": "restore",
                           "theme": prev, "error": f"exit code {rc}"})
    elif not prev:
        skipped.append({"app": "plasma_theme", "note": "no previous theme recorded"})



def _undo_cursor(change: dict, restored: list, failed: list, skipped: list) -> None:
    if change.get("action") != "write":
        return
    prev = change.get("previous_cursor")
    kwrite = _get_kwrite()
    if prev and kwrite:
        run_cmd([kwrite, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", prev])
    if prev and cmd_exists("plasma-apply-cursortheme"):
        rc, _, _ = run_cmd(["plasma-apply-cursortheme", prev], timeout=10)
        if rc == 0:
            restored.append({"app": "cursor", "action": "restored", "theme": prev})
        else:
            failed.append({"app": "cursor", "action": "restore",
                           "theme": prev, "error": f"exit code {rc}"})
    elif not prev:
        skipped.append({"app": "cursor", "note": "no previous cursor recorded"})


def _undo_icon_theme(change: dict, restored: list, failed: list, skipped: list) -> None:
    if change.get("action") != "write":
        return
    prev = change.get("previous_icon_theme")
    kwrite = _get_kwrite()
    if prev and kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", prev])
        if cmd_exists("qdbus6"):
            run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)
        restored.append({"app": "icon_theme", "action": "restored", "theme": prev})
    elif not prev and kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", "--delete"])
        restored.append({"app": "icon_theme", "action": "cleared"})
    else:
        skipped.append({"app": "icon_theme", "note": "no previous icon theme recorded"})


def _undo_kde_lockscreen(change: dict, restored: list, failed: list, skipped: list) -> None:
    # The generic file-backup loop skips kde_lockscreen (uses "config_path" not "path");
    # this handler is the authoritative restore path.
    if change.get("action") != "write":
        return
    prev = change.get("previous_theme")
    kwrite = _get_kwrite()
    if prev and kwrite:
        run_cmd([kwrite, "--file", "kscreenlockerrc", "--group", "Greeter", "--key", "Theme", prev])
        restored.append({"app": "kde_lockscreen", "action": "restored", "theme": prev})
    elif not prev:
        skipped.append({"app": "kde_lockscreen", "note": "no previous lock screen theme recorded"})


# method string → binary to check; command is built as method.split() + [prev_path]
_WALLPAPER_CMD_MAP: dict[str, str] = {
    "plasma-apply-wallpaperimage": "plasma-apply-wallpaperimage",
    "awww img":                    "awww",
    "swww img":                    "swww",
    "feh --bg-scale":              "feh",
}


def _undo_wallpaper(change: dict, restored: list, failed: list, skipped: list) -> None:
    if change.get("action") != "set":
        return
    prev   = change.get("previous_wallpaper")
    method = change.get("method", "")
    if not prev:
        skipped.append({"app": "wallpaper",
                        "note": "no previous wallpaper recorded (likely pre-fix manifest)"})
        return
    if method in _WALLPAPER_CMD_MAP:
        binary = _WALLPAPER_CMD_MAP[method]
        cmd    = method.split() + [prev]
        if cmd_exists(binary):
            rc, _, err = run_cmd(cmd, timeout=10)
            if rc == 0:
                restored.append({"app": "wallpaper", "action": "restored",
                                 "path": prev, "method": method})
            else:
                failed.append({"app": "wallpaper", "action": "restore",
                               "path": prev, "error": err or f"exit code {rc}"})
        else:
            skipped.append({"app": "wallpaper",
                            "note": f"binary not available for method {method!r}: {binary}"})
    elif method == "hyprpaper-config-rewrite":
        run_cmd(["pkill", "-x", "hyprpaper"])
        time.sleep(1)
        if cmd_exists("hyprpaper"):
            subprocess.Popen(["hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        restored.append({"app": "wallpaper", "action": "restored", "path": prev, "method": method})
    else:
        skipped.append({"app": "wallpaper", "note": f"unknown or unavailable method: {method!r}"})


# Registry: app key → undo handler function
_APP_UNDO_HANDLERS: dict[str, object] = {
    "kde":            _undo_kde,
    "kvantum":        _undo_kvantum,
    "plasma_theme":   _undo_plasma_theme,
    "cursor":         _undo_cursor,
    "icon_theme":     _undo_icon_theme,
    "kde_lockscreen": _undo_kde_lockscreen,
    "wallpaper":      _undo_wallpaper,
}



# _describe_change moved to core/undo_describe.py and re-exported above.


# ---------------------------------------------------------------------------
# ROLLBACK ENTRY POINT
# ---------------------------------------------------------------------------

def undo() -> dict:
    """Undo the most recent materialization.

    Strategy per app:
    - If the change has a 'backup' key: restore the file from backup.
    - If the change was an 'inject_include' or 'inject_theme': remove the
      injected lines using the stored marker (even if backup already restored
      the file — belt-and-suspenders).
    - For KDE: re-apply the previous colorscheme via plasma-apply-colorscheme.
    """
    manifest_path = CURRENT_DIR / "manifest.json"
    if not manifest_path.exists():
        return {"status": "error",
                "message": "No active theme to undo. Run 'apply' or 'preset' first."}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dry_run"):
        return {"status": "error", "message": "Cannot undo a dry-run — no changes were made."}

    restored, failed, skipped = [], [], []

    for change in manifest.get("changes", []):
        if change.get("action") == "error":
            continue
        _restore_backed_up_files(change, restored, failed)
        _undo_injections(change, restored, skipped)
        handler = _APP_UNDO_HANDLERS.get(change.get("app", ""))
        if handler:
            handler(change, restored, failed, skipped)

    manifest["undone"]    = True
    manifest["undone_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "status":   "success" if not failed else "partial",
        "restored": restored,
        "failed":   failed,
        "skipped":  skipped,
    }
