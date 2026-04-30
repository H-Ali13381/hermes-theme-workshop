"""scripts/ricer_undo.py — Undo / rollback system for Hermes Ricer.

Exports:
  undo()                  — execute rollback of one materialization manifest
  undo_session()          — walk active + history manifests newest→oldest and
                            undo each (full session rollback)
  simulate_undo_session() — list manifests + per-step describe output without
                            executing anything
  _describe_change        — used by 'simulate-undo' CLI command
  _APP_UNDO_HANDLERS      — per-app dispatch table (used by undo())
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

_BACKUP_KEYS = ("backup", "backup_profile", "backup_colors",
                "backup_konsolerc", "config_backup", "kdeglobals_backup")


def _restore_destination(change: dict, backup_key: str) -> Path | None:
    """Return the live file path for a manifest backup key."""
    if backup_key == "backup" and "path" in change:
        return Path(change["path"])
    if backup_key == "backup_profile" and "profile_path" in change:
        return Path(change["profile_path"])
    if backup_key == "backup_colors" and "color_scheme_path" in change:
        return Path(change["color_scheme_path"])
    if backup_key == "backup_konsolerc":
        return HOME / ".config" / "konsolerc"
    if backup_key == "config_backup":
        return (Path(change["config_path"]) if "config_path" in change
                else HOME / ".config" / "waybar" / "config")
    if backup_key == "kdeglobals_backup":
        return HOME / ".config" / "kdeglobals"
    return None


def _restore_backed_up_files(change: dict, restored: list, failed: list) -> None:
    """Restore any backed-up files referenced in a change record."""
    app = change.get("app", "unknown")
    for backup_key in _BACKUP_KEYS:
        if backup_key not in change:
            continue
        bp = change.get(backup_key)
        dest = _restore_destination(change, backup_key)
        if dest is None:
            continue
        if bp and Path(bp).exists():
            try:
                shutil.copy2(bp, dest)
                restored.append({"app": app, "restored": str(dest), "from": bp})
            except (OSError, shutil.Error) as e:
                failed.append({"app": app, "path": str(dest), "error": str(e)})
        else:
            # Backup gone — delete the file we created
            if dest.exists():
                try:
                    dest.unlink()
                    restored.append({"app": app, "deleted": str(dest),
                                     "note": "no backup existed — file was new, deleted"})
                except OSError as e:
                    failed.append({"app": app, "path": str(dest), "error": str(e)})


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


def _undo_eww(change: dict, restored: list, failed: list, skipped: list) -> None:
    """Live-state cleanup for EWW.

    Generic handlers already restore/delete the written files
    (``hermes-palette.scss``, ``hermes-theme.yuck``) and strip the
    ``@import`` / ``(include)`` injections from ``eww.scss`` /
    ``eww.yuck``.  This handler then closes the ``hermes-clock``
    window if it was opened and reloads the daemon so the live
    config reflects the cleaned files.
    """
    if change.get("action") != "reload":
        return
    if not cmd_exists("eww"):
        skipped.append({"app": "eww", "note": "eww binary not found"})
        return
    run_cmd(["eww", "close", "hermes-clock"], timeout=5)
    rc, _, _ = run_cmd(["eww", "reload"], timeout=5)
    if rc == 0:
        restored.append({"app": "eww", "action": "closed_window_and_reloaded",
                         "window": "hermes-clock"})
    else:
        skipped.append({"app": "eww",
                        "note": "eww reload exit != 0 (daemon may not be running)"})


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
            subprocess.Popen(["hyprpaper"], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
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
    "eww":            _undo_eww,
}


# ---------------------------------------------------------------------------
# ROLLBACK ENTRY POINT
# ---------------------------------------------------------------------------

def undo(manifest_path: Path | None = None) -> dict:
    """Undo a single materialization manifest.

    Defaults to the active manifest at ``CURRENT_DIR/manifest.json``; pass an
    explicit path to undo an archived history manifest.

    Strategy per app:
    - If the change has a 'backup' key: restore the file from backup.
    - If the change was an 'inject_include' or 'inject_theme': remove the
      injected lines using the stored marker (even if backup already restored
      the file — belt-and-suspenders).
    - For KDE: re-apply the previous colorscheme via plasma-apply-colorscheme.
    """
    if manifest_path is None:
        manifest_path = CURRENT_DIR / "manifest.json"
    if not manifest_path.exists():
        return {"status": "error",
                "manifest": str(manifest_path),
                "message": "No active theme to undo. Run 'apply' or 'preset' first."}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dry_run"):
        return {"status": "skipped", "manifest": str(manifest_path),
                "message": "Dry-run manifest — no changes were made."}
    if manifest.get("undone"):
        return {"status": "skipped", "manifest": str(manifest_path),
                "message": f"Already undone at {manifest.get('undone_at')}"}

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
        "manifest": str(manifest_path),
        "restored": restored,
        "failed":   failed,
        "skipped":  skipped,
    }


# ---------------------------------------------------------------------------
# SESSION-SPANNING ROLLBACK
# ---------------------------------------------------------------------------

def _collect_session_manifests(theme: str | None = None) -> list[Path]:
    """Return manifests for rollback, newest→oldest.

    The active manifest (``CURRENT_DIR/manifest.json``) is always first;
    archived manifests in ``CURRENT_DIR/history/manifest_*.json`` follow,
    sorted by filename descending (timestamps embedded in filenames).

    If ``theme`` is given, only manifests whose ``design_system.name`` matches
    are kept — this scopes rollback to a single session and prevents undoing
    applies from previous, unrelated sessions.
    """
    candidates: list[Path] = []
    active = CURRENT_DIR / "manifest.json"
    if active.exists():
        candidates.append(active)
    history_dir = CURRENT_DIR / "history"
    if history_dir.exists():
        archived = sorted(history_dir.glob("manifest_*.json"),
                          key=lambda p: p.name, reverse=True)
        candidates.extend(archived)
    if theme is None:
        return candidates
    matching: list[Path] = []
    for mp in candidates:
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("design_system", {}).get("name") == theme:
            matching.append(mp)
    return matching


def _active_theme_name() -> str | None:
    """Return the design_system.name of the active manifest, or None."""
    active = CURRENT_DIR / "manifest.json"
    if not active.exists():
        return None
    try:
        data = json.loads(active.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("design_system", {}).get("name")


def undo_session(all_history: bool = False) -> dict:
    """Roll back every manifest of the current session, newest→oldest.

    By default scopes to the active session's theme (matches
    ``design_system.name`` of the active manifest), preventing accidental
    rollback of unrelated previous sessions. Pass ``all_history=True`` to
    walk every manifest in history regardless of theme.

    Walks the active manifest and ``history/manifest_*.json`` in descending
    timestamp order, calling :func:`undo` on each. Manifests that are already
    undone or were dry-runs are skipped silently. Each step's restore output
    is preserved in ``per_manifest`` for auditing.
    """
    theme = None if all_history else _active_theme_name()
    manifests = _collect_session_manifests(theme)
    if not manifests:
        return {"status": "error",
                "message": "No manifests to undo (no active session)."}

    per_manifest: list[dict] = []
    total_restored = 0
    total_failed   = 0
    executed       = 0
    skipped        = 0

    for mp in manifests:
        result = undo(mp)
        per_manifest.append(result)
        if result.get("status") == "skipped":
            skipped += 1
            continue
        if result.get("status") == "error":
            continue
        executed += 1
        total_restored += len(result.get("restored", []))
        total_failed   += len(result.get("failed", []))

    return {
        "status":               "success" if total_failed == 0 else "partial",
        "scope":                "all_history" if all_history else f"theme={theme}",
        "manifests_total":      len(manifests),
        "manifests_executed":   executed,
        "manifests_skipped":    skipped,
        "total_restored":       total_restored,
        "total_failed":         total_failed,
        "per_manifest":         per_manifest,
    }


def simulate_undo_session(all_history: bool = False) -> dict:
    """Preview a session-spanning rollback without applying any changes.

    By default scopes to the active session's theme; pass ``all_history=True``
    to preview a rollback across every manifest in history.

    Returns a list of manifest summaries (one per step that *would* be undone),
    each with the same shape used by ``simulate-undo``. Skipped manifests
    (already-undone, dry-run) are included with a ``status`` field but no
    ``changes`` list.
    """
    theme = None if all_history else _active_theme_name()
    manifests = _collect_session_manifests(theme)
    summaries: list[dict] = []
    for mp in manifests:
        try:
            data = json.loads(mp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            summaries.append({"manifest": str(mp), "status": "error",
                              "message": str(e)})
            continue
        ds = data.get("design_system", {})
        entry: dict = {
            "manifest":   str(mp),
            "theme":      ds.get("name", "unknown"),
            "timestamp":  data.get("timestamp", "unknown"),
            "backup_dir": data.get("backup_dir", "unknown"),
            "undone":     bool(data.get("undone")),
            "dry_run":    bool(data.get("dry_run")),
            "apps":       sorted({c.get("app", "?")
                                  for c in data.get("changes", [])}),
        }
        if data.get("dry_run"):
            entry["status"] = "skipped"
            entry["reason"] = "dry-run"
        elif data.get("undone"):
            entry["status"] = "skipped"
            entry["reason"] = "already undone"
        else:
            entry["status"] = "would_undo"
            entry["change_descriptions"] = [
                line
                for change in data.get("changes", [])
                if change.get("action") != "error"
                for line in _describe_change(change)
            ]
        summaries.append(entry)
    return {
        "scope":           "all_history" if all_history else f"theme={theme}",
        "manifests_total": len(manifests),
        "manifests":       summaries,
    }
