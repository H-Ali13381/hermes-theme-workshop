"""Unit tests for KDE-specific undo restore paths in ricer_undo.py."""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))  # make 'core' importable when run in isolation
# Undo logic now lives in scripts/ricer_undo.py (extracted from ricer.py).
# We load it directly so patches target the correct module namespace.
RICER_UNDO_PY = ROOT / "scripts" / "ricer_undo.py"


def _load_ricer_undo():
    spec = importlib.util.spec_from_file_location("ricer_undo", RICER_UNDO_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ricer_undo = _load_ricer_undo()


def _write_manifest(path: Path, changes: list[dict], dry_run: bool = False) -> None:
    path.write_text(json.dumps(
        {"design_system": {"name": "test"}, "dry_run": dry_run, "changes": changes}
    ), encoding="utf-8")


def _run_undo(changes, *, cmd_exists_fn=lambda n: False, run_cmd_fn=None,
              kwrite=None, dry_run=False):
    """Write a manifest, run ricer_undo.undo() with all I/O mocked, return
    (result, calls, manifest).  Used by every TestUndo* harness below."""
    calls = []
    default_run = lambda cmd, **kw: calls.append(list(cmd)) or (0, "", "")
    with tempfile.TemporaryDirectory() as tmp:
        manifest_path = Path(tmp) / "manifest.json"
        _write_manifest(manifest_path, changes, dry_run=dry_run)
        with (
            patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)),
            patch.object(ricer_undo, "run_cmd",
                         side_effect=run_cmd_fn or default_run),
            patch.object(ricer_undo, "cmd_exists", side_effect=cmd_exists_fn),
            patch.object(ricer_undo, "_get_kwrite", return_value=kwrite),
        ):
            result = ricer_undo.undo()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return result, calls, manifest


class TestUndoKde(unittest.TestCase):
    """KDE-specific undo restore paths."""

    def _undo(self, changes, cmd_exists_fn=lambda n: False, dry_run=False):
        return _run_undo(changes, cmd_exists_fn=cmd_exists_fn,
                         kwrite="kwriteconfig6", dry_run=dry_run)

    def test_reapplies_previous_colorscheme(self):
        result, calls, _ = self._undo(
            [{"app": "kde", "action": "reload", "previous_colorscheme": "BreezeClassic"}],
            cmd_exists_fn=lambda n: n == "plasma-apply-colorscheme",
        )
        apply = [c for c in calls if "plasma-apply-colorscheme" in c]
        self.assertTrue(apply)
        self.assertIn("BreezeClassic", apply[0])
        self.assertEqual(result["status"], "success")

    def test_widget_style_uses_delete_when_no_previous(self):
        """widgetStyle with no prior value must use --delete, not empty string."""
        _, calls, _ = self._undo([
            {"app": "kvantum", "action": "write",
             "previous_kvantum_theme": None, "previous_widget_style": None},
        ])
        widget = [c for c in calls if "widgetStyle" in c]
        self.assertTrue(widget)
        self.assertIn("--delete", widget[0])
        self.assertTrue(all("--delete" in c for c in widget),
                        f"Expected every widgetStyle call to use --delete; got: {widget}")

    def test_cursor_restored_via_plasma_apply_cursortheme(self):
        result, calls, _ = self._undo(
            [{"app": "cursor", "action": "write", "previous_cursor": "breeze_cursors"}],
            cmd_exists_fn=lambda n: n in ("kwriteconfig6", "plasma-apply-cursortheme"),
        )
        apply = [c for c in calls if "plasma-apply-cursortheme" in c]
        self.assertTrue(apply)
        self.assertIn("breeze_cursors", apply[0])
        self.assertEqual(result["status"], "success")

    def test_plasma_theme_restored(self):
        result, calls, _ = self._undo(
            [{"app": "plasma_theme", "action": "write", "previous_theme": "default"}],
            cmd_exists_fn=lambda n: n == "plasma-apply-desktoptheme",
        )
        apply = [c for c in calls if "plasma-apply-desktoptheme" in c]
        self.assertTrue(apply)
        self.assertIn("default", apply[0])
        self.assertEqual(result["status"], "success")

    def test_lockscreen_theme_restored_via_kwriteconfig(self):
        result, calls, _ = self._undo([
            {"app": "kde_lockscreen", "action": "write",
             "previous_theme": "org.kde.breeze.desktop",
             "config_path": "/home/user/.config/kscreenlockerrc"},
        ])
        lock = [c for c in calls if "kwriteconfig6" in c and "kscreenlockerrc" in c and "Theme" in c]
        self.assertTrue(lock)
        self.assertIn("org.kde.breeze.desktop", lock[0])
        self.assertEqual(result["status"], "success")

    def test_lockscreen_skipped_when_no_previous_theme(self):
        result, _, _ = self._undo([{"app": "kde_lockscreen", "action": "write", "previous_theme": None}])
        self.assertIn("kde_lockscreen", [s.get("app") for s in result.get("skipped", [])])

    def test_lockscreen_wallpaper_restored_when_previous_recorded(self):
        result, calls, _ = self._undo([
            {"app": "kde_lockscreen", "action": "write",
             "previous_theme": "org.kde.breezedark.desktop",
             "wallpaper": "/new/lock.png",
             "previous_wallpaper": "file:///old/lock.png"},
        ])
        wp = [c for c in calls if "kwriteconfig6" in c and "Image" in c]
        self.assertTrue(wp, f"no Image kwriteconfig6 call; calls={calls}")
        self.assertIn("file:///old/lock.png", wp[0])
        self.assertNotIn("--delete", wp[0])
        actions = [r.get("action") for r in result.get("restored", [])]
        self.assertIn("restored_wallpaper", actions)

    def test_lockscreen_wallpaper_cleared_when_no_previous_recorded(self):
        result, calls, _ = self._undo([
            {"app": "kde_lockscreen", "action": "write",
             "previous_theme": "org.kde.breezedark.desktop",
             "wallpaper": "/new/lock.png",
             "previous_wallpaper": None},
        ])
        wp = [c for c in calls if "kwriteconfig6" in c and "Image" in c]
        self.assertTrue(wp, f"no Image kwriteconfig6 call; calls={calls}")
        self.assertIn("--delete", wp[0])
        actions = [r.get("action") for r in result.get("restored", [])]
        self.assertIn("cleared_wallpaper", actions)

    def test_lockscreen_wallpaper_untouched_when_apply_did_not_set_one(self):
        _, calls, _ = self._undo([
            {"app": "kde_lockscreen", "action": "write",
             "previous_theme": "org.kde.breezedark.desktop"},
        ])
        wp = [c for c in calls if "kwriteconfig6" in c and "Image" in c]
        self.assertFalse(wp, f"unexpected Image kwriteconfig6 call: {wp}")

    def test_lockscreen_file_restored_from_backup_via_config_path(self):
        """kde_lockscreen records destination as 'config_path' (not 'path').

        The generic file-restore loop must resolve 'config_path' for the
        'backup' key, otherwise the kscreenlockerrc Wallpaper subgroup keys
        (Image, FillMode, WallpaperPlugin) are left in place even though a
        backup exists — only the Greeter/Theme key gets rewritten by the
        per-app handler.
        """
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            kscreenlockerrc = Path(tmp) / "kscreenlockerrc"
            backup = Path(tmp) / "backup_kscreenlockerrc"
            backup.write_text(
                "[Greeter]\nTheme=org.kde.breezedark.desktop\n"
                "[Greeter][Wallpaper][org.kde.image][General]\n"
                "Image=file:///old/wallpaper.png\n",
                encoding="utf-8")
            kscreenlockerrc.write_text(
                "[Greeter]\nTheme=org.kde.breezedark.desktop\nWallpaperPlugin=org.kde.image\n"
                "[Greeter][Wallpaper][org.kde.image][General]\n"
                "FillMode=2\nImage=file:///new/wallpaper.png\n",
                encoding="utf-8")
            _write_manifest(manifest_path, [{
                "app": "kde_lockscreen", "action": "write",
                "config_path": str(kscreenlockerrc),
                "backup": str(backup),
                "previous_theme": "org.kde.breezedark.desktop",
            }])
            with patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)):
                result = ricer_undo.undo()
            self.assertEqual(result["status"], "success")
            self.assertEqual(kscreenlockerrc.read_text(encoding="utf-8"),
                             backup.read_text(encoding="utf-8"))
            restored_paths = [r.get("restored") for r in result.get("restored", [])]
            self.assertIn(str(kscreenlockerrc), restored_paths)

    def test_manifest_marked_undone(self):
        result, _, manifest = self._undo([])
        self.assertTrue(manifest.get("undone"))
        self.assertIn("undone_at", manifest)
        self.assertEqual(result["status"], "success")

    def test_generic_write_with_no_backup_deletes_created_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            created = Path(tmp) / "gtk.css"
            created.write_text("/* generated */\n", encoding="utf-8")
            _write_manifest(manifest_path, [
                {"app": "gtk", "action": "write", "path": str(created), "backup": None},
            ])

            with patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)):
                result = ricer_undo.undo()

            self.assertEqual(result["status"], "success")
            self.assertFalse(created.exists())
            self.assertEqual(result["restored"][0]["deleted"], str(created))

    def test_generic_restore_replaces_symlink_with_backed_up_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            backup = Path(tmp) / "backup_config.json"
            target = Path(tmp) / "config.jsonc"
            dest = Path(tmp) / "config.json"
            backup.write_text('{"old": true}\n', encoding="utf-8")
            target.write_text('{"new": true}\n', encoding="utf-8")
            dest.symlink_to(target.name)
            _write_manifest(manifest_path, [
                {"app": "fastfetch", "action": "compat-symlink", "path": str(dest), "backup": str(backup)},
            ])

            with patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)):
                result = ricer_undo.undo()

            self.assertEqual(result["status"], "success")
            self.assertFalse(dest.is_symlink())
            self.assertEqual(dest.read_text(encoding="utf-8"), '{"old": true}\n')
            self.assertEqual(target.read_text(encoding="utf-8"), '{"new": true}\n')

    def test_dry_run_manifest_is_skipped(self):
        # Dry-run manifests are a soft skip (not a hard error) so that
        # undo_session() can walk past them when rolling back a session.
        result, _, _ = self._undo([], dry_run=True)
        self.assertEqual(result["status"], "skipped")
        self.assertIn("dry-run", result["message"].lower())


class TestUndoGsettings(unittest.TestCase):
    """Undo restore paths for gsettings-based change records.

    Covers gtk, gnome_shell, and gnome_lockscreen apps which all share the
    _undo_gsettings handler.  Tests use the same manifest/mock pattern as
    TestUndoKde so patches land in the correct ricer_undo namespace.
    """

    def _undo(self, changes, run_cmd_fn=None, cmd_exists_fn=None):
        result, calls, _ = _run_undo(
            changes, run_cmd_fn=run_cmd_fn,
            cmd_exists_fn=cmd_exists_fn or (lambda n: n == "gsettings"))
        return result, calls

    # ------------------------------------------------------------------
    # Happy path — fresh manifest with previous_value present
    # ------------------------------------------------------------------

    def test_gtk_gsettings_restored_for_all_three_keys(self):
        """Fresh GTK manifest: gsettings set called once per key with previous_value."""
        changes = [
            {"app": "gtk", "action": "gsettings", "schema": "org.gnome.desktop.interface",
             "key": "gtk-theme",    "value": "Adwaita-dark",  "previous_value": "'Adwaita'"},
            {"app": "gtk", "action": "gsettings", "schema": "org.gnome.desktop.interface",
             "key": "icon-theme",   "value": "Papirus-Dark",  "previous_value": "'Papirus'"},
            {"app": "gtk", "action": "gsettings", "schema": "org.gnome.desktop.interface",
             "key": "cursor-theme", "value": "Bibata-Modern", "previous_value": "'default'"},
        ]
        result, calls = self._undo(changes)

        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(len(gs_calls), 3)

        restored_actions = [r["action"] for r in result["restored"]]
        self.assertEqual(restored_actions.count("restored_gsettings"), 3)

        restored_values = {r["key"]: r["value"] for r in result["restored"]}
        self.assertEqual(restored_values["gtk-theme"],    "'Adwaita'")
        self.assertEqual(restored_values["icon-theme"],   "'Papirus'")
        self.assertEqual(restored_values["cursor-theme"], "'default'")
        self.assertEqual(result["status"], "success")

    def test_gnome_shell_color_scheme_restored(self):
        """Fresh gnome_shell manifest: color-scheme restored to previous_value."""
        result, calls = self._undo([{
            "app": "gnome_shell", "action": "gsettings",
            "schema": "org.gnome.desktop.interface",
            "key": "color-scheme", "value": "prefer-dark", "previous_value": "'default'",
        }])
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(len(gs_calls), 1)
        self.assertEqual(gs_calls[0],
                         ["gsettings", "set", "org.gnome.desktop.interface",
                          "color-scheme", "'default'"])
        self.assertEqual(result["status"], "success")

    def test_gnome_lockscreen_all_keys_restored(self):
        """Fresh gnome_lockscreen manifest: all three screensaver keys restored."""
        changes = [
            {"app": "gnome_lockscreen", "action": "gsettings",
             "schema": "org.gnome.desktop.screensaver",
             "key": "primary-color",   "value": "#1a1b26", "previous_value": "'#000000'"},
            {"app": "gnome_lockscreen", "action": "gsettings",
             "schema": "org.gnome.desktop.screensaver",
             "key": "secondary-color", "value": "#24283b", "previous_value": "'#000000'"},
            {"app": "gnome_lockscreen", "action": "gsettings",
             "schema": "org.gnome.desktop.screensaver",
             "key": "color-shading-type", "value": "solid", "previous_value": "'solid'"},
        ]
        result, calls = self._undo(changes)
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(len(gs_calls), 3)
        self.assertEqual(result["restored"][0]["schema"], "org.gnome.desktop.screensaver")
        self.assertEqual(result["status"], "success")

    # ------------------------------------------------------------------
    # Legacy manifest — previous_value absent
    # ------------------------------------------------------------------

    def test_skips_gracefully_when_previous_value_is_none(self):
        """Legacy manifest (previous_value=None): goes to skipped, not failed or crash."""
        result, calls = self._undo([{
            "app": "gtk", "action": "gsettings",
            "schema": "org.gnome.desktop.interface",
            "key": "gtk-theme", "value": "Adwaita-dark", "previous_value": None,
        }])
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(gs_calls, [], "gsettings set must not be called for a legacy record")
        skipped_apps = [s["app"] for s in result["skipped"]]
        self.assertIn("gtk", skipped_apps)
        self.assertEqual(result["status"], "success")

    def test_skips_gracefully_when_previous_value_key_absent(self):
        """Pre-fix manifest with no previous_value key at all: same skip behaviour."""
        result, calls = self._undo([{
            "app": "gnome_shell", "action": "gsettings",
            "schema": "org.gnome.desktop.interface",
            "key": "color-scheme", "value": "prefer-dark",
            # previous_value key entirely absent — simulates a pre-fix manifest
        }])
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(gs_calls, [])
        self.assertIn("gnome_shell", [s["app"] for s in result["skipped"]])

    # ------------------------------------------------------------------
    # gsettings binary absent
    # ------------------------------------------------------------------

    def test_skips_when_gsettings_not_installed(self):
        """If gsettings binary is absent, change goes to skipped."""
        result, calls = self._undo(
            [{"app": "gtk", "action": "gsettings",
              "schema": "org.gnome.desktop.interface",
              "key": "gtk-theme", "value": "Adwaita-dark", "previous_value": "'Adwaita'"}],
            cmd_exists_fn=lambda n: False,
        )
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(gs_calls, [])
        self.assertIn("gtk", [s["app"] for s in result["skipped"]])

    # ------------------------------------------------------------------
    # gsettings set failure
    # ------------------------------------------------------------------

    def test_records_failure_when_gsettings_set_returns_nonzero(self):
        """A non-zero gsettings exit code goes to failed, not silently swallowed."""
        def failing_run(cmd, **kw):
            return (1, "", "permission denied")

        result, _ = self._undo(
            [{"app": "gtk", "action": "gsettings",
              "schema": "org.gnome.desktop.interface",
              "key": "gtk-theme", "value": "Adwaita-dark", "previous_value": "'Adwaita'"}],
            run_cmd_fn=failing_run,
        )
        self.assertEqual(result["status"], "partial")
        self.assertEqual(len(result["failed"]), 1)
        self.assertEqual(result["failed"][0]["action"], "restore_gsettings")
        self.assertIn("permission denied", result["failed"][0]["error"])

    def test_skips_when_schema_or_key_missing(self):
        """Corrupted change record missing schema/key: skipped gracefully, no crash."""
        result, calls = self._undo([{
            "app": "gtk", "action": "gsettings",
            # schema and key intentionally absent
            "value": "Adwaita-dark", "previous_value": "'Adwaita'",
        }])
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(gs_calls, [])
        self.assertIn("gtk", [s["app"] for s in result["skipped"]])

    def test_apply_failure_still_attempts_restore(self):
        """success=False in the change record does not prevent undo from restoring.

        If gsettings set failed during apply, the value was never changed, so
        restoring the previous value is a harmless no-op — but we still attempt
        it rather than silently skipping, so partial-failure manifests are
        fully rolled back.
        """
        result, calls = self._undo([{
            "app": "gtk", "action": "gsettings",
            "schema": "org.gnome.desktop.interface",
            "key": "gtk-theme", "value": "Adwaita-dark",
            "previous_value": "'Adwaita'", "success": False,
        }])
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(len(gs_calls), 1,
                         "gsettings set must still be called even when apply success=False")
        self.assertEqual(gs_calls[0][-1], "'Adwaita'")
        self.assertEqual(result["status"], "success")

    def test_mixed_gtk_manifest_file_writes_and_gsettings(self):
        """Real manifest: gtk app emits both 'write' and 'gsettings' change records.

        _restore_backed_up_files handles the file write; _undo_gsettings handles
        the gsettings record.  Neither path must interfere with the other.
        """
        with tempfile.TemporaryDirectory() as tmp:
            live_css = Path(tmp) / "gtk.css"
            backup_css = Path(tmp) / "gtk.css.bak"
            backup_css.write_text("/* original */\n", encoding="utf-8")
            live_css.write_text("/* applied */\n", encoding="utf-8")

            changes = [
                {"app": "gtk", "action": "write",
                 "path": str(live_css), "backup": str(backup_css)},
                {"app": "gtk", "action": "gsettings",
                 "schema": "org.gnome.desktop.interface",
                 "key": "gtk-theme", "value": "Adwaita-dark",
                 "previous_value": "'Adwaita'"},
            ]
            manifest_path = Path(tmp) / "manifest.json"
            _write_manifest(manifest_path, changes)

            gs_calls = []

            def _run(cmd, **kw):
                gs_calls.append(list(cmd))
                return (0, "", "")

            with (
                patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)),
                patch.object(ricer_undo, "run_cmd", side_effect=_run),
                patch.object(ricer_undo, "cmd_exists", side_effect=lambda n: n == "gsettings"),
                patch.object(ricer_undo, "_get_kwrite", return_value=None),
            ):
                result = ricer_undo.undo()

            # Assertions inside the context — files still exist.
            # File must be restored from backup.
            self.assertEqual(live_css.read_text(encoding="utf-8"), "/* original */\n")
            # gsettings set must be called exactly once with the previous value.
            set_calls = [c for c in gs_calls if c[:2] == ["gsettings", "set"]]
            self.assertEqual(len(set_calls), 1)
            self.assertEqual(set_calls[0][-1], "'Adwaita'")
            self.assertEqual(result["status"], "success")


class TestDescribeChangeGsettings(unittest.TestCase):
    """_describe_change renders correct human-readable lines for gsettings records.

    core/undo_describe.py is directly imported (scripts/ is already on sys.path)
    so tests target the function in its own module, independent of ricer_undo.
    """

    @classmethod
    def setUpClass(cls):
        from core.undo_describe import _describe_change
        cls._describe = staticmethod(_describe_change)

    def test_with_previous_value_shows_restore_line(self):
        """A gsettings change with previous_value produces a RESTORE line."""
        change = {
            "app": "gtk", "action": "gsettings",
            "schema": "org.gnome.desktop.interface",
            "key": "gtk-theme", "previous_value": "'Adwaita'",
        }
        lines = self._describe(change)
        self.assertEqual(len(lines), 1)
        self.assertIn("RESTORE gsettings", lines[0])
        self.assertIn("gtk-theme", lines[0])
        self.assertIn("'Adwaita'", lines[0])

    def test_without_previous_value_none_shows_skip_line(self):
        """previous_value=None (legacy manifest) produces a 'will skip' line."""
        change = {
            "app": "gnome_shell", "action": "gsettings",
            "schema": "org.gnome.desktop.interface",
            "key": "color-scheme", "previous_value": None,
        }
        lines = self._describe(change)
        self.assertEqual(len(lines), 1)
        self.assertIn("pre-fix manifest", lines[0])
        self.assertIn("will skip", lines[0])

    def test_missing_previous_value_key_shows_skip_line(self):
        """previous_value key entirely absent (pre-fix manifest) → 'will skip' line."""
        change = {
            "app": "gtk", "action": "gsettings",
            "schema": "org.gnome.desktop.interface",
            "key": "gtk-theme",
            # previous_value key entirely absent
        }
        lines = self._describe(change)
        self.assertEqual(len(lines), 1)
        self.assertIn("will skip", lines[0])

    def test_dry_run_action_produces_no_gsettings_lines(self):
        """dry-run change records are not gsettings actions; no lines expected."""
        change = {
            "app": "gtk", "action": "dry-run",
            "gtk_theme": "Adwaita-dark", "icon_theme": "Papirus",
        }
        lines = self._describe(change)
        self.assertEqual(lines, [])


class TestUndoLnf(unittest.TestCase):
    """_undo_lnf: KDE Look-and-Feel rollback handler."""

    def _undo(self, changes, cmd_exists_fn=lambda n: True):
        result, calls, _ = _run_undo(changes, cmd_exists_fn=cmd_exists_fn)
        return result, calls

    def test_previous_lnf_is_reapplied(self):
        """When previous_lnf is set, plasma-apply-lookandfeel --apply is called."""
        result, calls = self._undo([{
            "app": "lnf", "action": "write",
            "lnf_id": "hermes-test.desktop",
            "lnf_path": "/tmp/hermes-test.desktop",
            "previous_lnf": "org.kde.breezedark.desktop",
        }], cmd_exists_fn=lambda n: n == "plasma-apply-lookandfeel")
        lnf_calls = [c for c in calls if "plasma-apply-lookandfeel" in c]
        self.assertEqual(len(lnf_calls), 1)
        self.assertIn("org.kde.breezedark.desktop", lnf_calls[0])
        self.assertEqual(result["status"], "success")
        lnf_restored = [r for r in result["restored"]
                        if r.get("action") == "restored" and r.get("app") == "lnf"]
        self.assertEqual(len(lnf_restored), 1)

    def test_skips_restore_when_no_previous_lnf(self):
        """Without previous_lnf, a skip record is added and no apply is attempted."""
        result, calls = self._undo([{
            "app": "lnf", "action": "write",
            "lnf_id": "hermes-test.desktop",
            "lnf_path": "/tmp/hermes-test.desktop",
            "previous_lnf": None,
        }], cmd_exists_fn=lambda n: n == "plasma-apply-lookandfeel")
        lnf_calls = [c for c in calls if "plasma-apply-lookandfeel" in c]
        self.assertEqual(lnf_calls, [])
        skip_notes = [s["note"] for s in result["skipped"] if s.get("app") == "lnf"]
        self.assertTrue(any("no previous" in n for n in skip_notes))

    def test_generated_package_removed_from_safe_prefix(self):
        """A hermes-* lnf_path under the expected prefix is deleted on undo."""
        with tempfile.TemporaryDirectory() as tmp:
            lnf_base = Path(tmp) / ".local" / "share" / "plasma" / "look-and-feel"
            lnf_dir = lnf_base / "hermes-myrice.desktop"
            lnf_dir.mkdir(parents=True)
            (lnf_dir / "metadata.json").write_text("{}", encoding="utf-8")

            manifest_path = Path(tmp) / "manifest.json"
            _write_manifest(manifest_path, [{
                "app": "lnf", "action": "write",
                "lnf_id": "hermes-myrice.desktop",
                "lnf_path": str(lnf_dir),
                "previous_lnf": "org.kde.breezedark.desktop",
            }])
            with (
                patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)),
                patch.object(ricer_undo, "run_cmd", return_value=(0, "", "")),
                patch.object(ricer_undo, "cmd_exists",
                             side_effect=lambda n: n == "plasma-apply-lookandfeel"),
                patch.object(ricer_undo, "_get_kwrite", return_value=None),
                patch.object(ricer_undo, "HOME", Path(tmp)),
            ):
                result = ricer_undo.undo()

            self.assertFalse(lnf_dir.exists(), "generated lnf directory should be deleted")
            removed = [r for r in result["restored"]
                       if r.get("action") == "removed_generated_package"]
            self.assertEqual(len(removed), 1)

    def test_skips_when_plasma_apply_not_found(self):
        """If plasma-apply-lookandfeel is absent, the restore is skipped (not failed)."""
        result, calls = self._undo([{
            "app": "lnf", "action": "write",
            "lnf_id": "hermes-test.desktop",
            "lnf_path": "/tmp/hermes-test.desktop",
            "previous_lnf": "org.kde.breeze.desktop",
        }], cmd_exists_fn=lambda n: False)
        lnf_calls = [c for c in calls if "plasma-apply-lookandfeel" in c]
        self.assertEqual(lnf_calls, [])
        self.assertIn("lnf", [s["app"] for s in result["skipped"]])

    def test_restore_command_failure_recorded_in_failed(self):
        """When plasma-apply-lookandfeel returns non-zero, a failure entry is recorded."""
        result, _, _ = _run_undo(
            [{"app": "lnf", "action": "write",
              "lnf_id": "hermes-myrice.desktop", "lnf_path": None,
              "previous_lnf": "org.kde.breeze.desktop"}],
            run_cmd_fn=lambda cmd, **kw: (1, "", "apply failed"),
            cmd_exists_fn=lambda n: n == "plasma-apply-lookandfeel",
        )
        self.assertIn("lnf", [f["app"] for f in result["failed"]])
        self.assertEqual(result["status"], "partial")

    def test_generated_package_not_removed_when_outside_prefix(self):
        """lnf_path outside the hermes prefix is NOT deleted (safety guard).

        This test verifies that the resolve+is_relative_to guard prevents rmtree
        from running on a path that happens to start with 'hermes-' but lives
        outside ~/.local/share/plasma/look-and-feel/.
        """
        with tempfile.TemporaryDirectory() as tmp:
            # Create a directory with a hermes- name but outside the expected prefix.
            unsafe_dir = Path(tmp) / "unsafe" / "hermes-escape.desktop"
            unsafe_dir.mkdir(parents=True)
            (unsafe_dir / "metadata.json").write_text("{}", encoding="utf-8")

            manifest_path = Path(tmp) / "manifest.json"
            _write_manifest(manifest_path, [{
                "app": "lnf", "action": "write",
                "lnf_id": "hermes-escape.desktop",
                "lnf_path": str(unsafe_dir),
                "previous_lnf": "org.kde.breeze.desktop",
            }])
            lnf_prefix = Path(tmp) / ".local" / "share" / "plasma" / "look-and-feel"
            lnf_prefix.mkdir(parents=True)
            with (
                patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)),
                patch.object(ricer_undo, "run_cmd", return_value=(0, "", "")),
                patch.object(ricer_undo, "cmd_exists",
                             side_effect=lambda n: n == "plasma-apply-lookandfeel"),
                patch.object(ricer_undo, "_get_kwrite", return_value=None),
                patch.object(ricer_undo, "HOME", Path(tmp)),
            ):
                result = ricer_undo.undo()

            self.assertTrue(unsafe_dir.exists(),
                            "Directory outside the hermes prefix must NOT be deleted")
            removed = [r for r in result["restored"]
                       if r.get("action") == "removed_generated_package"]
            self.assertEqual(removed, [], "No removed_generated_package record should exist")


class TestUndoHyprland(unittest.TestCase):
    """_undo_hyprland: live border keyword rollback handler."""

    def _undo(self, changes, cmd_exists_fn=lambda n: True):
        result, calls, _ = _run_undo(changes, cmd_exists_fn=cmd_exists_fn)
        return result, calls

    def test_reverts_both_border_keywords(self):
        """Both active and inactive border keywords are reverted via hyprctl keyword."""
        result, calls = self._undo([{
            "app": "hyprland", "action": "set_borders",
            "active_border": "rgba(aabbccee)",
            "inactive_border": "rgba(aabbccaa)",
            "previous_active_border": "rgba(ffffffee) rgba(ffffffee) 0deg",
            "previous_inactive_border": "rgba(888888aa)",
            "path": "/home/user/.config/hypr/hyprland.conf",
            "backup": None,
        }], cmd_exists_fn=lambda n: n == "hyprctl")
        kw_calls = [c for c in calls if c[:2] == ["hyprctl", "keyword"]]
        self.assertEqual(len(kw_calls), 2)
        keys_reverted = {c[2] for c in kw_calls}
        self.assertIn("general:col.active_border", keys_reverted)
        self.assertIn("general:col.inactive_border", keys_reverted)
        # Values must be the previous ones
        active_call = next(c for c in kw_calls if c[2] == "general:col.active_border")
        self.assertEqual(active_call[3], "rgba(ffffffee) rgba(ffffffee) 0deg")
        self.assertEqual(result["status"], "success")

    def test_skips_when_no_previous_border_values(self):
        """Without previous border values (legacy manifest), live state is skipped."""
        result, calls = self._undo([{
            "app": "hyprland", "action": "set_borders",
            "active_border": "rgba(aabbccee)",
            "inactive_border": "rgba(aabbccaa)",
            # no previous_active_border / previous_inactive_border
            "path": "/home/user/.config/hypr/hyprland.conf",
            "backup": None,
        }], cmd_exists_fn=lambda n: n == "hyprctl")
        kw_calls = [c for c in calls if c[:2] == ["hyprctl", "keyword"]]
        self.assertEqual(kw_calls, [])
        self.assertIn("hyprland", [s["app"] for s in result["skipped"]])

    def test_skips_when_hyprctl_absent(self):
        """Without hyprctl, no keyword commands are run and a skip record is added."""
        result, calls = self._undo([{
            "app": "hyprland", "action": "set_borders",
            "active_border": "rgba(aabbccee)",
            "inactive_border": "rgba(aabbccaa)",
            "previous_active_border": "rgba(ffffffee) rgba(ffffffee) 0deg",
            "previous_inactive_border": "rgba(888888aa)",
            "path": "/home/user/.config/hypr/hyprland.conf",
            "backup": None,
        }], cmd_exists_fn=lambda n: False)
        kw_calls = [c for c in calls if c[:2] == ["hyprctl", "keyword"]]
        self.assertEqual(kw_calls, [])
        self.assertIn("hyprland", [s["app"] for s in result["skipped"]])

    def test_keyword_failure_recorded_in_failed(self):
        """When hyprctl keyword returns non-zero, the failure is recorded (not silently ignored)."""
        result, _, _ = _run_undo(
            [{"app": "hyprland", "action": "set_borders",
              "previous_active_border": "rgba(ffffffee)",
              "previous_inactive_border": "rgba(888888aa)",
              "path": "/home/user/.config/hypr/hyprland.conf",
              "backup": None}],
            run_cmd_fn=lambda cmd, **kw: (1, "", "hyprctl: no compositor running"),
            cmd_exists_fn=lambda n: n == "hyprctl",
        )
        self.assertIn("hyprland", [f["app"] for f in result["failed"]])
        self.assertEqual(result["status"], "partial")

    def test_reverts_only_non_none_border_when_one_is_missing(self):
        """When only one previous border value is recorded, only that one is reverted."""
        result, calls = self._undo([{
            "app": "hyprland", "action": "set_borders",
            "active_border": "rgba(aabbccee)",
            "inactive_border": "rgba(aabbccaa)",
            "previous_active_border": "rgba(ffffffee) rgba(ffffffee) 0deg",
            "previous_inactive_border": None,  # not recorded
            "path": "/home/user/.config/hypr/hyprland.conf",
            "backup": None,
        }], cmd_exists_fn=lambda n: n == "hyprctl")
        kw_calls = [c for c in calls if c[:2] == ["hyprctl", "keyword"]]
        self.assertEqual(len(kw_calls), 1, "Only the non-None border should be reverted")
        self.assertEqual(kw_calls[0][2], "general:col.active_border")


class TestUndoFlatpakOverride(unittest.TestCase):
    """_undo_flatpak_override: removes only Hermes-added Flatpak filesystem overrides."""

    def _undo(self, changes, cmd_exists_fn=lambda n: True):
        result, calls, _ = _run_undo(changes, cmd_exists_fn=cmd_exists_fn)
        return result, calls

    def test_removes_all_filesystems_added(self):
        """Each filesystem in filesystems_added is removed via --nofilesystem."""
        added = ["xdg-config/gtk-3.0:ro", "xdg-data/icons:ro"]
        result, calls = self._undo([{
            "app": "gtk", "action": "flatpak-override",
            "gtk_theme": "Adwaita-dark", "icon_theme": "Papirus", "success": True,
            "flatpak_override_snapshot": "",
            "filesystems_added": added,
        }], cmd_exists_fn=lambda n: n == "flatpak")
        no_fs_calls = [c for c in calls
                       if c[:3] == ["flatpak", "override", "--user"]
                       and any("--nofilesystem" in a for a in c)]
        self.assertEqual(len(no_fs_calls), 2)
        removed_names = {a.split("=", 1)[1] for c in no_fs_calls for a in c if a.startswith("--nofilesystem=")}
        self.assertEqual(removed_names, {"xdg-config/gtk-3.0", "xdg-data/icons"})
        self.assertEqual(result["status"], "success")

    def test_skips_when_no_filesystems_added(self):
        """Legacy manifests without filesystems_added produce a skip, not a crash."""
        result, calls = self._undo([{
            "app": "gtk", "action": "flatpak-override",
            "gtk_theme": "Adwaita-dark", "success": True,
            # filesystems_added absent (legacy)
        }], cmd_exists_fn=lambda n: n == "flatpak")
        no_fs_calls = [c for c in calls if "--nofilesystem" in str(c)]
        self.assertEqual(no_fs_calls, [])
        self.assertIn("gtk", [s["app"] for s in result["skipped"]])

    def test_skips_when_flatpak_absent(self):
        """Without the flatpak binary, overrides are not removed and a skip is recorded."""
        result, calls = self._undo([{
            "app": "gtk", "action": "flatpak-override",
            "gtk_theme": "Adwaita-dark", "success": True,
            "filesystems_added": ["xdg-config/gtk-3.0:ro"],
        }], cmd_exists_fn=lambda n: False)
        no_fs_calls = [c for c in calls if "--nofilesystem" in str(c)]
        self.assertEqual(no_fs_calls, [])
        self.assertIn("gtk", [s["app"] for s in result["skipped"]])

    def test_gsettings_and_flatpak_override_in_same_gtk_manifest(self):
        """A single gtk manifest with both gsettings and flatpak-override records works correctly."""
        added = ["xdg-config/gtk-3.0:ro"]
        result, calls = self._undo([
            {"app": "gtk", "action": "gsettings",
             "schema": "org.gnome.desktop.interface", "key": "gtk-theme",
             "value": "Adwaita-dark", "previous_value": "'Adwaita'"},
            {"app": "gtk", "action": "flatpak-override",
             "gtk_theme": "Adwaita-dark", "success": True,
             "filesystems_added": added},
        ], cmd_exists_fn=lambda n: n in ("gsettings", "flatpak"))
        gs_calls = [c for c in calls if c[:2] == ["gsettings", "set"]]
        self.assertEqual(len(gs_calls), 1)
        self.assertEqual(gs_calls[0][-1], "'Adwaita'")
        no_fs_calls = [c for c in calls if "--nofilesystem" in str(c)]
        self.assertEqual(len(no_fs_calls), 1)
        self.assertEqual(result["status"], "success")

    def test_skips_gracefully_when_filesystems_added_is_empty_list(self):
        """An empty filesystems_added list (all overrides pre-existed) skips without crashing.

        This is distinct from the key being absent (legacy): the key IS present but
        nothing was newly added.  The skip note should still be descriptive.
        """
        result, calls = self._undo([{
            "app": "gtk", "action": "flatpak-override",
            "gtk_theme": "Adwaita-dark", "success": True,
            "filesystems_added": [],  # present but empty — nothing was added
        }], cmd_exists_fn=lambda n: n == "flatpak")
        no_fs_calls = [c for c in calls if "--nofilesystem" in str(c)]
        self.assertEqual(no_fs_calls, [],
                         "No --nofilesystem calls should be made when nothing was added")
        skip_apps = [s["app"] for s in result["skipped"]]
        self.assertIn("gtk", skip_apps)


class TestDescribeChangeNewHandlers(unittest.TestCase):
    """_describe_change renders correct lines for lnf, flatpak-override, and hyprland."""

    @classmethod
    def setUpClass(cls):
        from core.undo_describe import _describe_change
        cls._describe = staticmethod(_describe_change)

    def test_lnf_with_previous_shows_reapply_line(self):
        lines = self._describe({
            "app": "lnf", "action": "write",
            "lnf_id": "hermes-test.desktop",
            "lnf_path": "/home/user/.local/share/plasma/look-and-feel/hermes-test.desktop",
            "previous_lnf": "org.kde.breezedark.desktop",
        })
        self.assertTrue(any("REAPPLY Look-and-Feel" in l for l in lines))
        self.assertTrue(any("org.kde.breezedark.desktop" in l for l in lines))
        self.assertTrue(any("REMOVE generated package" in l for l in lines))

    def test_lnf_without_previous_shows_skip_line(self):
        lines = self._describe({
            "app": "lnf", "action": "write",
            "lnf_id": "hermes-test.desktop",
            "lnf_path": None,
            "previous_lnf": None,
        })
        self.assertTrue(any("will skip restore" in l for l in lines))

    def test_flatpak_override_with_filesystems_shows_remove_line(self):
        lines = self._describe({
            "app": "gtk", "action": "flatpak-override",
            "filesystems_added": ["xdg-config/gtk-3.0:ro", "xdg-data/icons:ro"],
        })
        self.assertTrue(any("REMOVE Flatpak filesystem overrides" in l for l in lines))
        self.assertTrue(any("xdg-config/gtk-3.0:ro" in l for l in lines))

    def test_flatpak_override_legacy_shows_skip_line(self):
        lines = self._describe({
            "app": "gtk", "action": "flatpak-override",
            # no filesystems_added
        })
        self.assertTrue(any("will skip" in l for l in lines))

    def test_hyprland_with_previous_borders_shows_revert_lines(self):
        lines = self._describe({
            "app": "hyprland", "action": "set_borders",
            "previous_active_border": "rgba(ffffffee) rgba(ffffffee) 0deg",
            "previous_inactive_border": "rgba(888888aa)",
        })
        self.assertTrue(any("col.active_border" in l for l in lines))
        self.assertTrue(any("col.inactive_border" in l for l in lines))
        self.assertTrue(any("rgba(ffffffee)" in l for l in lines))

    def test_hyprland_without_previous_borders_shows_skip_line(self):
        lines = self._describe({
            "app": "hyprland", "action": "set_borders",
            # no previous border values
        })
        self.assertTrue(any("not reverted" in l for l in lines))


if __name__ == "__main__":
    unittest.main()
