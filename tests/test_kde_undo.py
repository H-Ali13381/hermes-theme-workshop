"""Unit tests for KDE-specific undo restore paths in ricer.py."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
RICER_PY = ROOT / "scripts" / "ricer.py"


def _load_ricer():
    spec = importlib.util.spec_from_file_location("ricer", RICER_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ricer = _load_ricer()


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
                patch.object(ricer, "CURRENT_DIR", Path(tmp)),
                patch.object(ricer, "run_cmd",
                             side_effect=lambda cmd, **kw: calls.append(list(cmd)) or (0, "", "")),
                patch.object(ricer, "cmd_exists", side_effect=cmd_exists_fn),
                patch.object(ricer, "_get_kwrite", return_value="kwriteconfig6"),
            ):
                result = ricer.undo()
            manifest = json.loads(manifest_path.read_text())
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
        self.assertFalse([c for c in widget if "" in c and "--delete" not in c])

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

    def test_manifest_marked_undone(self):
        result, _, manifest = self._undo([])
        self.assertTrue(manifest.get("undone"))
        self.assertIn("undone_at", manifest)
        self.assertEqual(result["status"], "success")

    def test_dry_run_manifest_returns_error(self):
        result, _, _ = self._undo([], dry_run=True)
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
