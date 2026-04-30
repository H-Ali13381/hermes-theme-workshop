"""Unit tests for GTK materialization backup coverage."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ricer import materialize_gtk  # noqa: E402


_DESIGN = {
    "name": "gtk-regression",
    "palette": {
        "background": "#1a1b26",
        "foreground": "#c0caf5",
        "primary": "#7aa2f7",
        "secondary": "#bb9af7",
        "accent": "#7dcfff",
        "surface": "#24283b",
        "muted": "#565f89",
        "danger": "#f7768e",
        "success": "#9ece6a",
        "warning": "#e0af68",
    },
    "typography": {"ui_font": "Inter"},
}


class GtkMaterializerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _run(self):
        with (
            patch("materializers.system.HOME", self.tmp),
            patch("core.backup.BACKUP_DIR", self.tmp / ".cache" / "backup"),
            patch("materializers.system.cmd_exists", return_value=False),
        ):
            return materialize_gtk(_DESIGN, backup_ts="20260101_000000")

    def test_writes_gtk3_and_gtk4_css_with_manifest_backups(self):
        for rel, old in [
            (".config/gtk-3.0/gtk.css", "/* old gtk3 */\n"),
            (".config/gtk-4.0/gtk.css", "/* old gtk4 */\n"),
        ]:
            path = self.tmp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(old, encoding="utf-8")

        changes = self._run()
        css_changes = [c for c in changes if c.get("path", "").endswith("gtk.css")]

        self.assertEqual(len(css_changes), 2)
        for change in css_changes:
            path = Path(change["path"])
            self.assertTrue(path.exists())
            self.assertIn("@define-color accent_color #7aa2f7;", path.read_text(encoding="utf-8"))
            self.assertIsNotNone(change.get("backup"))
            self.assertTrue(Path(change["backup"]).exists())

    def test_new_css_files_get_backup_none_for_undo_deletion(self):
        changes = self._run()
        css_changes = [c for c in changes if c.get("path", "").endswith("gtk.css")]

        self.assertEqual(len(css_changes), 2)
        self.assertTrue(all(c.get("backup") is None for c in css_changes))
        self.assertTrue((self.tmp / ".config" / "gtk-3.0" / "gtk.css").exists())
        self.assertTrue((self.tmp / ".config" / "gtk-4.0" / "gtk.css").exists())


if __name__ == "__main__":
    unittest.main()