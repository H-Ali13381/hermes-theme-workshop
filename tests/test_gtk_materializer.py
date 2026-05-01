"""Unit tests for GTK materialization backup coverage and gsettings snapshotting."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ricer import materialize_gtk, materialize_gnome_shell, materialize_gnome_lockscreen  # noqa: E402


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


class GtkGsettingsSnapshotTests(unittest.TestCase):
    """materialize_gtk() records schema + previous_value in gsettings change records."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _run_with_gsettings(self, previous_side_effect):
        """Run materialize_gtk with gsettings present and a controlled gsettings_get."""
        with (
            patch("materializers.system.HOME", self.tmp),
            patch("core.backup.BACKUP_DIR", self.tmp / ".cache" / "backup"),
            patch("materializers.system.cmd_exists", return_value=True),
            patch("materializers.system.run_cmd", return_value=(0, "", "")),
            patch("materializers.system.gsettings_get", side_effect=previous_side_effect),
        ):
            return materialize_gtk(_DESIGN, backup_ts="20260101_000000")

    def test_gsettings_changes_include_schema_and_previous_value(self):
        """Each gsettings change record carries schema and previous_value."""
        fake_prev = {"gtk-theme": "'Adwaita'", "icon-theme": "'Papirus'", "cursor-theme": "'default'"}
        changes = self._run_with_gsettings(lambda schema, key: fake_prev.get(key))
        gs = [c for c in changes if c.get("action") == "gsettings"]

        self.assertEqual(len(gs), 3)
        for c in gs:
            self.assertEqual(c["schema"], "org.gnome.desktop.interface")
            self.assertIn(c["key"], fake_prev)
            self.assertEqual(c["previous_value"], fake_prev[c["key"]])

    def test_gsettings_previous_value_none_when_key_unset(self):
        """previous_value is None when gsettings_get returns None (key not set)."""
        changes = self._run_with_gsettings(lambda schema, key: None)
        gs = [c for c in changes if c.get("action") == "gsettings"]

        self.assertEqual(len(gs), 3)
        self.assertTrue(all(c["previous_value"] is None for c in gs))

    def test_no_gsettings_changes_when_gsettings_absent(self):
        """No gsettings change records are appended when gsettings is not installed."""
        with (
            patch("materializers.system.HOME", self.tmp),
            patch("core.backup.BACKUP_DIR", self.tmp / ".cache" / "backup"),
            patch("materializers.system.cmd_exists", return_value=False),
        ):
            changes = materialize_gtk(_DESIGN, backup_ts="20260101_000000")
        gs = [c for c in changes if c.get("action") == "gsettings"]
        self.assertEqual(gs, [])


class GnomeShellGsettingsSnapshotTests(unittest.TestCase):
    """materialize_gnome_shell() records schema + previous_value for color-scheme."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _run(self, previous_value):
        with (
            patch("materializers.gnome.HOME", self.tmp),
            patch("core.backup.BACKUP_DIR", self.tmp / ".cache" / "backup"),
            patch("materializers.gnome.cmd_exists", return_value=True),
            patch("materializers.gnome.run_cmd", return_value=(0, "", "")),
            patch("materializers.gnome.gsettings_get", return_value=previous_value),
        ):
            return materialize_gnome_shell(_DESIGN, backup_ts="20260101_000000")

    def test_records_previous_color_scheme(self):
        changes = self._run("'default'")
        gs = [c for c in changes if c.get("action") == "gsettings"]
        self.assertEqual(len(gs), 1)
        self.assertEqual(gs[0]["schema"], "org.gnome.desktop.interface")
        self.assertEqual(gs[0]["key"], "color-scheme")
        self.assertEqual(gs[0]["previous_value"], "'default'")

    def test_previous_value_none_when_key_unset(self):
        changes = self._run(None)
        gs = [c for c in changes if c.get("action") == "gsettings"]
        self.assertEqual(len(gs), 1)
        self.assertIsNone(gs[0]["previous_value"])


class GnomeLockscreenGsettingsSnapshotTests(unittest.TestCase):
    """materialize_gnome_lockscreen() records previous_value for all three keys."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _run(self, previous_value):
        with (
            patch("materializers.gnome.HOME", self.tmp),
            patch("materializers.gnome.cmd_exists", return_value=True),
            patch("materializers.gnome.run_cmd", return_value=(0, "", "")),
            patch("materializers.gnome.gsettings_get", return_value=previous_value),
        ):
            return materialize_gnome_lockscreen(_DESIGN, backup_ts="20260101_000000")

    def test_records_previous_value_for_all_three_keys(self):
        changes = self._run("'#000000'")
        gs = [c for c in changes if c.get("action") == "gsettings"]
        self.assertEqual(len(gs), 3)
        keys = {c["key"] for c in gs}
        self.assertEqual(keys, {"primary-color", "secondary-color", "color-shading-type"})
        self.assertTrue(all(c["previous_value"] == "'#000000'" for c in gs))

    def test_previous_value_none_when_keys_unset(self):
        changes = self._run(None)
        gs = [c for c in changes if c.get("action") == "gsettings"]
        self.assertEqual(len(gs), 3)
        self.assertTrue(all(c["previous_value"] is None for c in gs))


if __name__ == "__main__":
    unittest.main()