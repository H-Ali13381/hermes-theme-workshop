"""scripts/ricer_undo.py — Undo / rollback system for Hermes Ricer.

Exports:
  undo()                  — execute rollback of one materialization manifest
  undo_session()          — walk active + history manifests newest→oldest and
                            undo each (full session rollback)
  simulate_undo_session() — list manifests + per-step describe output without
                            executing anything
  _describe_change        — used by 'simulate-undo' CLI command
  _ACTION_HANDLERS        — per-action dispatch table (gsettings, flatpak-override)
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
from typing import Callable

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
    """Return the live file path for a manifest backup key.

    For the generic "backup" key, materializers may record the destination
    under either "path" (most apps) or "config_path" (kde_lockscreen, kvantum,
    lnf, …).  Both are accepted so file-restore is not silently skipped.
    """
    if backup_key == "backup":
        if "path" in change:
            return Path(change["path"])
        if "config_path" in change:
            return Path(change["config_path"])
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


def _iter_change_artifacts(change: dict):
    """Yield (app, dest_path, has_backup) for every backup-tracked write
    in a change record.  ``has_backup`` is False when the backup file does
    not exist and the destination would be deleted on undo.
    """
    app = change.get("app", "unknown")
    for backup_key in _BACKUP_KEYS:
        if backup_key not in change:
            continue
        bp = change.get(backup_key)
        dest = _restore_destination(change, backup_key)
        if dest is None:
            continue
        yield app, dest, bool(bp and Path(bp).exists())


def collect_deletable_artifacts(manifest_path: Path) -> list[dict]:
    """Return a list of {app, path} entries that ``undo()`` would delete.

    A path is "deletable" when the backup is missing (the file was created
    fresh during apply, with no prior version to restore).  Only existing
    files are reported — already-absent paths are skipped.  Used by the CLI
    to surface destructive operations before invoking ``undo()``.
    """
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if manifest.get("dry_run") or manifest.get("undone"):
        return []
    out: list[dict] = []
    for change in manifest.get("changes", []):
        if change.get("action") == "error":
            continue
        for app, dest, has_backup in _iter_change_artifacts(change):
            if not has_backup and (dest.exists() or dest.is_symlink()):
                out.append({"app": app, "path": str(dest)})
    return out


def _restore_backed_up_files(change: dict, restored: list, failed: list,
                             delete_artifacts: bool = True) -> None:
    """Restore any backed-up files referenced in a change record.

    When ``delete_artifacts`` is False, files whose backup is missing are
    left in place (instead of being deleted) and reported under
    ``restored`` with a ``kept`` field.  Used by the CLI to honour a user
    declining the deletion prompt.
    """
    for app, dest, has_backup in _iter_change_artifacts(change):
        # Re-derive the backup path the same way _iter_change_artifacts did.
        bp = next((change[k] for k in _BACKUP_KEYS
                   if k in change and _restore_destination(change, k) == dest), None)
        if has_backup:
            try:
                if dest.is_symlink():
                    dest.unlink()
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bp, dest)
                restored.append({"app": app, "restored": str(dest), "from": bp})
            except (OSError, shutil.Error) as e:
                failed.append({"app": app, "path": str(dest), "error": str(e)})
        else:
            if not (dest.exists() or dest.is_symlink()):
                continue
            if not delete_artifacts:
                restored.append({"app": app, "kept": str(dest),
                                 "note": "no backup existed — file kept (user declined deletion)"})
                continue
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


def _make_simple_kde_theme_undo(*, app: str, field: str, file: str, group: str,
                                 key: str, apply_cmd: str, note_label: str
                                 ) -> Callable[[dict, list, list, list], None]:
    """Build an undo handler for a 'write previous value to kdeglobals-style file
    + plasma-apply-X' KDE theme component (plasma_theme, cursor, …)."""
    def handler(change: dict, restored: list, failed: list, skipped: list) -> None:
        if change.get("action") != "write":
            return
        prev = change.get(field)
        kwrite = _get_kwrite()
        if prev and kwrite:
            run_cmd([kwrite, "--file", file, "--group", group, "--key", key, prev])
        if prev and cmd_exists(apply_cmd):
            rc, _, _ = run_cmd([apply_cmd, prev], timeout=10)
            if rc == 0:
                restored.append({"app": app, "action": "restored", "theme": prev})
            else:
                failed.append({"app": app, "action": "restore",
                               "theme": prev, "error": f"exit code {rc}"})
        elif not prev:
            skipped.append({"app": app, "note": f"no previous {note_label} recorded"})
    return handler


_undo_plasma_theme = _make_simple_kde_theme_undo(
    app="plasma_theme", field="previous_theme", file="plasmarc",
    group="Theme", key="name", apply_cmd="plasma-apply-desktoptheme",
    note_label="theme")
_undo_cursor = _make_simple_kde_theme_undo(
    app="cursor", field="previous_cursor", file="kcminputrc",
    group="Mouse", key="cursorTheme", apply_cmd="plasma-apply-cursortheme",
    note_label="cursor")


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
    # Belt-and-suspenders: the generic file-restore loop reverts kscreenlockerrc
    # via the 'config_path' fallback when a backup is present, but this handler
    # also rewrites Greeter/Theme and the Wallpaper Image key directly so a
    # missing/empty backup doesn't leave the new values in place.
    if change.get("action") != "write":
        return
    prev    = change.get("previous_theme")
    prev_wp = change.get("previous_wallpaper")
    new_wp  = change.get("wallpaper")
    kwrite  = _get_kwrite()
    if prev and kwrite:
        run_cmd([kwrite, "--file", "kscreenlockerrc", "--group", "Greeter", "--key", "Theme", prev])
        restored.append({"app": "kde_lockscreen", "action": "restored", "theme": prev})
    elif not prev:
        skipped.append({"app": "kde_lockscreen", "note": "no previous lock screen theme recorded"})
    if kwrite and new_wp is not None:
        wp_group = ["--group", "Greeter", "--group", "Wallpaper",
                    "--group", "org.kde.image", "--group", "General"]
        if prev_wp:
            run_cmd([kwrite, "--file", "kscreenlockerrc", *wp_group, "--key", "Image", prev_wp])
            restored.append({"app": "kde_lockscreen", "action": "restored_wallpaper", "path": prev_wp})
        else:
            run_cmd([kwrite, "--file", "kscreenlockerrc", *wp_group, "--key", "Image", "--delete"])
            restored.append({"app": "kde_lockscreen", "action": "cleared_wallpaper"})


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


def _undo_lnf(change: dict, restored: list, failed: list, skipped: list) -> None:
    """Reapply the previous KDE Look-and-Feel package and clean up generated hermes package.

    Handles ``action == "write"`` change records from ``materialize_lnf``.
    ``previous_lnf`` is the LookAndFeelPackage key read before apply.
    ``lnf_path`` is the generated hermes package directory; deleted only when
    it is safely under the expected hermes prefix.
    """
    if change.get("action") != "write":
        return
    prev_lnf = change.get("previous_lnf")
    lnf_path = change.get("lnf_path")

    if prev_lnf:
        if cmd_exists("plasma-apply-lookandfeel"):
            rc, _, err = run_cmd(["plasma-apply-lookandfeel", "--apply", prev_lnf], timeout=30)
            if rc == 0:
                restored.append({"app": "lnf", "action": "restored", "lnf": prev_lnf})
            else:
                failed.append({"app": "lnf", "action": "restore",
                               "lnf": prev_lnf, "error": err or f"exit code {rc}"})
        else:
            skipped.append({"app": "lnf",
                            "note": f"plasma-apply-lookandfeel not found; previous theme: {prev_lnf}"})
    else:
        skipped.append({"app": "lnf",
                        "note": "no previous Look-and-Feel recorded — will not restore"})

    # Clean up the generated Hermes LnF package only when it is safely scoped.
    # Resolve both paths to their canonical forms before comparing so that symlinks
    # in lnf_path cannot trick is_relative_to into a false positive (the check is
    # purely lexical on unresolved Path objects).
    if lnf_path:
        lnf_dir = Path(lnf_path)
        if lnf_dir.exists():
            lnf_dir_real = lnf_dir.resolve()
            expected_prefix = (HOME / ".local" / "share" / "plasma" / "look-and-feel").resolve()
            if (lnf_dir_real.is_relative_to(expected_prefix)
                    and lnf_dir_real.name.startswith("hermes-")):
                try:
                    shutil.rmtree(lnf_dir_real)
                    restored.append({"app": "lnf", "action": "removed_generated_package",
                                     "path": str(lnf_dir_real)})
                except OSError as e:
                    failed.append({"app": "lnf", "action": "remove_generated_package",
                                   "path": str(lnf_dir_real), "error": str(e)})


def _undo_flatpak_override(change: dict, restored: list, failed: list, skipped: list) -> None:
    """Remove Flatpak filesystem overrides that Hermes added during apply.

    Handles ``action == "flatpak-override"`` change records from ``materialize_gtk``.
    Only overrides recorded in ``filesystems_added`` are removed, so pre-existing
    user overrides are left intact.
    """
    if change.get("action") != "flatpak-override":
        return
    filesystems_added = change.get("filesystems_added")
    if not filesystems_added:
        skipped.append({"app": "gtk",
                        "note": "no filesystems_added in manifest (legacy) — "
                                "Flatpak overrides not reverted"})
        return
    if not cmd_exists("flatpak"):
        skipped.append({"app": "gtk", "note": "flatpak not found — cannot revert overrides"})
        return
    for fs in filesystems_added:
        fs_name = fs.split(":")[0]  # strip :ro/:rw suffix for --nofilesystem
        rc, _, err = run_cmd(["flatpak", "override", "--user",
                               f"--nofilesystem={fs_name}"], timeout=10)
        if rc == 0:
            restored.append({"app": "gtk", "action": "removed_flatpak_override",
                             "filesystem": fs_name})
        else:
            failed.append({"app": "gtk", "action": "remove_flatpak_override",
                           "filesystem": fs_name, "error": err or f"exit code {rc}"})


def _undo_hyprland(change: dict, restored: list, failed: list, skipped: list) -> None:
    """Revert live Hyprland border keywords to their pre-apply values.

    Handles ``action == "set_borders"`` change records from ``materialize_hyprland``.
    ``previous_active_border`` / ``previous_inactive_border`` are the gradient
    strings captured via ``hyprctl getoption`` before apply.  If not recorded
    (legacy manifest or getoption not available), the live state is not reverted
    (the config-file restore still applies on the next Hyprland reload).
    """
    if change.get("action") != "set_borders":
        return
    prev_active   = change.get("previous_active_border")
    prev_inactive = change.get("previous_inactive_border")

    if not cmd_exists("hyprctl"):
        skipped.append({"app": "hyprland",
                        "note": "hyprctl not found — cannot revert live keywords"})
        return

    if prev_active is None and prev_inactive is None:
        skipped.append({"app": "hyprland",
                        "note": "no previous border values recorded — live state not reverted "
                                "(config file restore still applied)"})
        return

    for key, val in [("general:col.active_border",   prev_active),
                     ("general:col.inactive_border", prev_inactive)]:
        if val is None:
            continue
        rc, _, err = run_cmd(["hyprctl", "keyword", key, val], timeout=5)
        if rc == 0:
            restored.append({"app": "hyprland", "action": "reverted_keyword",
                             "key": key, "value": val})
        else:
            failed.append({"app": "hyprland", "action": "revert_keyword",
                           "key": key, "error": err or f"exit code {rc}"})


def _undo_gsettings(change: dict, restored: list, failed: list, skipped: list) -> None:
    """Restore a single gsettings key to its pre-apply value.

    Handles ``action == "gsettings"`` change records produced by
    ``materialize_gtk``, ``materialize_gnome_shell``, and
    ``materialize_gnome_lockscreen``.  The ``previous_value`` field must be
    the raw GVariant string captured by ``gsettings_get`` before apply; it is
    passed directly to ``gsettings set`` which accepts GVariant syntax.
    """
    if change.get("action") != "gsettings":
        return
    app    = change.get("app", "unknown")
    schema = change.get("schema")
    key    = change.get("key")
    previous_value = change.get("previous_value")

    if not schema or not key:
        skipped.append({"app": app,
                        "note": f"gsettings change missing schema/key — cannot restore: {change}"})
        return
    if previous_value is None:
        skipped.append({"app": app,
                        "note": f"no previous_value recorded for {schema} {key} "
                                "(pre-fix manifest) — cannot restore"})
        return
    if not cmd_exists("gsettings"):
        skipped.append({"app": app, "note": "gsettings not found"})
        return

    rc, _, err = run_cmd(["gsettings", "set", schema, key, previous_value])
    if rc == 0:
        restored.append({"app": app, "action": "restored_gsettings",
                         "schema": schema, "key": key, "value": previous_value})
    else:
        failed.append({"app": app, "action": "restore_gsettings",
                       "schema": schema, "key": key,
                       "error": err or f"exit code {rc}"})


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


_UndoHandler = Callable[[dict, list, list, list], None]

# Registry: action → handler. Action handlers are app-agnostic; they self-gate
# on the change record's "action" field and run on *every* change record. This
# lets gtk / gnome_shell / gnome_lockscreen share the same gsettings restore
# path without per-app wrapper functions.
_ACTION_HANDLERS: dict[str, _UndoHandler] = {
    "gsettings":        _undo_gsettings,
    "flatpak-override": _undo_flatpak_override,
}

# Registry: app key → handler. App handlers self-gate on action and run after
# the action handler so apps with bespoke live-state cleanup (KDE plasma reload,
# eww daemon close, hyprland keyword revert, …) can do their own work.
_APP_UNDO_HANDLERS: dict[str, _UndoHandler] = {
    "kde":              _undo_kde,
    "kvantum":          _undo_kvantum,
    "plasma_theme":     _undo_plasma_theme,
    "cursor":           _undo_cursor,
    "icon_theme":       _undo_icon_theme,
    "kde_lockscreen":   _undo_kde_lockscreen,
    "lnf":              _undo_lnf,
    "wallpaper":        _undo_wallpaper,
    "eww":              _undo_eww,
    "hyprland":         _undo_hyprland,
}


# ---------------------------------------------------------------------------
# ROLLBACK ENTRY POINT
# ---------------------------------------------------------------------------

def undo(manifest_path: Path | None = None,
         delete_artifacts: bool = True) -> dict:
    """Undo a single materialization manifest.

    Defaults to the active manifest at ``CURRENT_DIR/manifest.json``; pass an
    explicit path to undo an archived history manifest.

    Strategy per app:
    - If the change has a 'backup' key: restore the file from backup.
    - If the change was an 'inject_include' or 'inject_theme': remove the
      injected lines using the stored marker (even if backup already restored
      the file — belt-and-suspenders).
    - For KDE: re-apply the previous colorscheme via plasma-apply-colorscheme.

    When ``delete_artifacts`` is False, files written without a backup
    (i.e. created fresh during apply) are kept on disk instead of deleted.
    Use :func:`collect_deletable_artifacts` to preview what would be removed.
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
        _restore_backed_up_files(change, restored, failed,
                                 delete_artifacts=delete_artifacts)
        _undo_injections(change, restored, skipped)
        action_handler = _ACTION_HANDLERS.get(change.get("action", ""))
        if action_handler:
            action_handler(change, restored, failed, skipped)
        app_handler = _APP_UNDO_HANDLERS.get(change.get("app", ""))
        if app_handler:
            app_handler(change, restored, failed, skipped)

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


def undo_session(all_history: bool = False,
                 delete_artifacts: bool = True) -> dict:
    """Roll back every manifest of the current session, newest→oldest.

    By default scopes to the active session's theme (matches
    ``design_system.name`` of the active manifest), preventing accidental
    rollback of unrelated previous sessions. Pass ``all_history=True`` to
    walk every manifest in history regardless of theme.

    Walks the active manifest and ``history/manifest_*.json`` in descending
    timestamp order, calling :func:`undo` on each. Manifests that are already
    undone or were dry-runs are skipped silently. Each step's restore output
    is preserved in ``per_manifest`` for auditing.

    ``delete_artifacts`` is forwarded to :func:`undo` for every manifest.
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
        result = undo(mp, delete_artifacts=delete_artifacts)
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
