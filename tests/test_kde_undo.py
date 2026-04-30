"""Unit tests for KDE-specific undo restore paths in ricer_undo.py."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
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


class TestUndoKde(unittest.TestCase):
    """KDE-specific undo restore paths."""

    def _undo(self, changes, cmd_exists_fn=lambda n: False, dry_run=False):
        """Write a manifest, run undo() with all I/O mocked, return (result, calls, manifest)."""
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            manifest_path = Path(tmp) / "manifest.json"
            _write_manifest(manifest_path, changes, dry_run=dry_run)
            with (
                patch.object(ricer_undo, "CURRENT_DIR", Path(tmp)),
                patch.object(ricer_undo, "run_cmd",
                             side_effect=lambda cmd, **kw: calls.append(list(cmd)) or (0, "", "")),
                patch.object(ricer_undo, "cmd_exists", side_effect=cmd_exists_fn),
                patch.object(ricer_undo, "_get_kwrite", return_value="kwriteconfig6"),
            ):
                result = ricer_undo.undo()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return result, calls, manifest

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

    def test_dry_run_manifest_is_skipped(self):
        # Dry-run manifests are a soft skip (not a hard error) so that
        # undo_session() can walk past them when rolling back a session.
        result, _, _ = self._undo([], dry_run=True)
        self.assertEqual(result["status"], "skipped")
        self.assertIn("dry-run", result["message"].lower())


if __name__ == "__main__":
    unittest.main()
