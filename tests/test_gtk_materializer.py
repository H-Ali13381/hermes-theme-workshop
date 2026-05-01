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

    def test_no_gsettings_change_when_gsettings_absent(self):
        """When gsettings is not installed the CSS file is still written but no
        gsettings change record is emitted — the cmd_exists guard must fire."""
        with (
            patch("materializers.gnome.HOME", self.tmp),
            patch("core.backup.BACKUP_DIR", self.tmp / ".cache" / "backup"),
            patch("materializers.gnome.cmd_exists", return_value=False),
            patch("materializers.gnome.run_cmd", return_value=(0, "", "")),
            patch("materializers.gnome.gsettings_get", return_value=None),
        ):
            changes = materialize_gnome_shell(_DESIGN, backup_ts="20260101_000000")

        gs = [c for c in changes if c.get("action") == "gsettings"]
        self.assertEqual(gs, [], "no gsettings record expected when binary absent")
        # The theme CSS write must still happen regardless.
        write = [c for c in changes if c.get("action") == "write"]
        self.assertEqual(len(write), 1)


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

    def test_skipped_when_gsettings_absent(self):
        """When gsettings is not installed, a single 'skipped' record is returned
        and no gsettings set is attempted — the materializer is purely gsettings-based."""
        with (
            patch("materializers.gnome.HOME", self.tmp),
            patch("materializers.gnome.cmd_exists", return_value=False),
        ):
            changes = materialize_gnome_lockscreen(_DESIGN, backup_ts="20260101_000000")

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["action"], "skipped")
        self.assertEqual(changes[0]["reason"], "gsettings not found")
        gs = [c for c in changes if c.get("action") == "gsettings"]
        self.assertEqual(gs, [])


class FlatpakOverrideSnapshotTests(unittest.TestCase):
    """materialize_gtk snapshots and tracks Flatpak overrides correctly."""

    def setUp(self):
        self._tmp_obj = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp_obj.name)

    def tearDown(self):
        self._tmp_obj.cleanup()

    def _run(self, flatpak_snapshot_out: str, existing_filesystems: list | None = None):
        """Run materialize_gtk with flatpak present; return changes."""
        if existing_filesystems is None:
            existing_filesystems = []

        def _run_cmd(cmd, **kw):
            if cmd[:4] == ["flatpak", "override", "--user", "--show"]:
                return (0, flatpak_snapshot_out, "")
            return (0, "", "")

        with (
            patch("materializers.system.HOME", self.tmp),
            patch("core.backup.BACKUP_DIR", self.tmp / ".cache" / "backup"),
            patch("materializers.system.cmd_exists", side_effect=lambda n: n == "flatpak"),
            patch("materializers.system.gsettings_get", return_value=None),
            patch("materializers.system.run_cmd", side_effect=_run_cmd),
            patch("materializers.system.render_template", return_value=""),
        ):
            return materialize_gtk(_DESIGN, backup_ts="20260101_000000")

    def test_flatpak_override_change_record_emitted(self):
        """A flatpak-override change record is emitted when flatpak is present."""
        changes = self._run("")
        fp = [c for c in changes if c.get("action") == "flatpak-override"]
        self.assertEqual(len(fp), 1)

    def test_filesystems_added_excludes_existing_overrides(self):
        """filesystems_added does not include overrides already in the snapshot."""
        # Simulate xdg-config/gtk-3.0 already present in user overrides
        snapshot = "[Context]\nfilesystems=xdg-config/gtk-3.0:ro;\n"
        changes = self._run(snapshot)
        fp = [c for c in changes if c.get("action") == "flatpak-override"][0]
        added = fp["filesystems_added"]
        self.assertNotIn("xdg-config/gtk-3.0:ro", added,
                         "Already-present override should not be in filesystems_added")
        self.assertIn("xdg-config/gtk-4.0:ro", added)
        self.assertIn("xdg-data/icons:ro", added)

    def test_filesystems_added_all_new_when_snapshot_empty(self):
        """When no overrides existed, all three filesystems are tracked as added."""
        changes = self._run("")
        fp = [c for c in changes if c.get("action") == "flatpak-override"][0]
        added = fp["filesystems_added"]
        self.assertIn("xdg-config/gtk-3.0:ro", added)
        self.assertIn("xdg-config/gtk-4.0:ro", added)
        self.assertIn("xdg-data/icons:ro", added)

    def test_flatpak_override_snapshot_stored(self):
        """The raw snapshot output is stored in the manifest for auditability."""
        snapshot = "[Context]\nfilesystems=xdg-data/icons:ro;\n"
        changes = self._run(snapshot)
        fp = [c for c in changes if c.get("action") == "flatpak-override"][0]
        self.assertIn("flatpak_override_snapshot", fp)
        self.assertIn("xdg-data/icons", fp["flatpak_override_snapshot"])

    def test_filesystems_added_excludes_via_exact_path_not_substring(self):
        """Existing override 'xdg-data/icons' must not shadow 'xdg-data/icons/extra'.

        The old substring check would incorrectly treat a path as already-present
        when the snapshot contains a path that happens to be a prefix of it.
        This test guards the inverse: 'xdg-data/icons-extra' in the snapshot must
        NOT prevent 'xdg-data/icons:ro' from being tracked as newly added.
        """
        # Snapshot contains 'xdg-data/icons-extra:ro' — a different path from 'xdg-data/icons'.
        # Old substring check: 'xdg-data/icons' IN 'filesystems=xdg-data/icons-extra:ro;' → True!
        # New exact-set check: 'xdg-data/icons' not in {'xdg-data/icons-extra'} → correctly False.
        snapshot = "[Context]\nfilesystems=xdg-data/icons-extra:ro;\n"
        changes = self._run(snapshot)
        fp = [c for c in changes if c.get("action") == "flatpak-override"][0]
        added = fp["filesystems_added"]
        self.assertIn("xdg-data/icons:ro", added,
                      "xdg-data/icons:ro should be in filesystems_added; "
                      "'xdg-data/icons-extra' is a different path")

    def test_flatpak_show_failure_tracks_all_filesystems_as_added(self):
        """When flatpak override --show fails (rc=1), all filesystems are tracked as added.

        Previously the rc was silently ignored (prefixed with _); a failing snapshot
        would yield an empty string and all paths would be treated as newly added —
        but the change record would not reflect that the snapshot was unreliable.
        After the fix the logic is explicit: rc != 0 → snapshot = "" → all added.
        """
        def _run_cmd(cmd, **kw):
            if cmd[:4] == ["flatpak", "override", "--user", "--show"]:
                return (1, "", "error: not connected to daemon")  # failure
            return (0, "", "")

        with (
            patch("materializers.system.HOME", self.tmp),
            patch("core.backup.BACKUP_DIR", self.tmp / ".cache" / "backup"),
            patch("materializers.system.cmd_exists", side_effect=lambda n: n == "flatpak"),
            patch("materializers.system.gsettings_get", return_value=None),
            patch("materializers.system.run_cmd", side_effect=_run_cmd),
            patch("materializers.system.render_template", return_value=""),
        ):
            changes = materialize_gtk(_DESIGN, backup_ts="20260101_000000")

        fp = [c for c in changes if c.get("action") == "flatpak-override"][0]
        # All three should be tracked as added since the snapshot couldn't be read.
        self.assertEqual(len(fp["filesystems_added"]), 3,
                         "All three filesystems should be in filesystems_added when snapshot fails")
        self.assertEqual(fp["flatpak_override_snapshot"], "",
                         "Snapshot field should be empty when --show command fails")

    def test_filesystems_added_empty_when_all_already_present(self):
        """When all three GTK overrides already exist in the snapshot, filesystems_added is [].

        The undo handler skips removal only when filesystems_added is falsy ([] or absent).
        An empty list is the correct signal that nothing new was added.
        """
        # All three Hermes filesystems already present.
        snapshot = (
            "[Context]\n"
            "filesystems=xdg-config/gtk-3.0:ro;xdg-config/gtk-4.0:ro;xdg-data/icons:ro;\n"
        )
        changes = self._run(snapshot)
        fp = [c for c in changes if c.get("action") == "flatpak-override"][0]
        self.assertEqual(fp["filesystems_added"], [],
                         "filesystems_added should be empty when all overrides pre-existed")


class HyprlandGeoptionSnapshotTests(unittest.TestCase):
    """materialize_hyprland snapshots live border values via hyprctl getoption."""

    # Per-option outputs with DIFFERENT gradient values so we can verify each
    # option is read separately (the old test used the same output for both, which
    # would pass even if the code called getoption only once and reused the result).
    _ACTIVE_GEO_OUT = (
        "option general:col.active_border    int (legacy) = 0\n"
        "    gradient = rgba(aabbccee) rgba(aabbccee) 45deg\n"
        "    set = 0\n"
    )
    _INACTIVE_GEO_OUT = (
        "option general:col.inactive_border    int (legacy) = 0\n"
        "    gradient = rgba(888888aa)\n"
        "    set = 0\n"
    )

    def _run(self, getoption_outputs: dict[str, str | None] | None = None):
        """Run materialize_hyprland with per-option mocked hyprctl; return changes.

        ``getoption_outputs`` maps option names to their output string, or None
        to simulate a failure for that option.  Pass ``None`` for the whole dict
        to simulate hyprctl being unavailable (all options fail).
        """
        _HYPR_DESIGN = {**_DESIGN, "name": "hypr-test"}

        def _run_cmd(cmd, **kw):
            if cmd[:2] == ["hyprctl", "getoption"]:
                option = cmd[2] if len(cmd) > 2 else ""
                if getoption_outputs is None:
                    return (1, "", "")
                out = getoption_outputs.get(option)
                if out is None:
                    return (1, "", "")
                return (0, out, "")
            return (0, "", "")

        with (
            patch("materializers.hyprland.HOME", Path("/tmp/fake-home")),
            patch("materializers.hyprland.run_cmd", side_effect=_run_cmd),
            # _hyprctl_getoption_gradient now lives in core.process and uses
            # core.process.run_cmd — patch that name binding too so the helper
            # picks up the same mocked behaviour.
            patch("core.process.run_cmd", side_effect=_run_cmd),
            patch("materializers.hyprland.cmd_exists", return_value=True),
            patch("materializers.hyprland.discover_desktop",
                  return_value={"wm": "hyprland"}),
            patch("materializers.hyprland.backup_file", return_value=None),
            patch("pathlib.Path.exists", return_value=False),
        ):
            from materializers.hyprland import materialize_hyprland
            return materialize_hyprland(_HYPR_DESIGN, backup_ts="20260101_000000")

    def test_previous_borders_stored_with_distinct_values(self):
        """Active and inactive borders are captured separately with their distinct values."""
        changes = self._run({
            "general:col.active_border":   self._ACTIVE_GEO_OUT,
            "general:col.inactive_border": self._INACTIVE_GEO_OUT,
        })
        sb = [c for c in changes if c.get("action") == "set_borders"]
        self.assertEqual(len(sb), 1)
        self.assertEqual(sb[0]["previous_active_border"],
                         "rgba(aabbccee) rgba(aabbccee) 45deg",
                         "Active border should reflect the active option output")
        self.assertEqual(sb[0]["previous_inactive_border"],
                         "rgba(888888aa)",
                         "Inactive border should reflect the inactive option output")

    def test_previous_borders_none_when_getoption_fails(self):
        """When getoption fails (e.g. hyprctl unavailable), previous values are None."""
        changes = self._run(None)
        sb = [c for c in changes if c.get("action") == "set_borders"]
        self.assertEqual(len(sb), 1)
        self.assertIsNone(sb[0]["previous_active_border"])
        self.assertIsNone(sb[0]["previous_inactive_border"])

    def test_gradient_without_angle_is_captured(self):
        """A single-stop gradient (no angle suffix) is stored correctly."""
        single_stop = (
            "option general:col.inactive_border    int (legacy) = 0\n"
            "    gradient = rgba(444444ff)\n"
            "    set = 0\n"
        )
        changes = self._run({
            "general:col.active_border":   self._ACTIVE_GEO_OUT,
            "general:col.inactive_border": single_stop,
        })
        sb = [c for c in changes if c.get("action") == "set_borders"]
        self.assertEqual(sb[0]["previous_inactive_border"], "rgba(444444ff)")


if __name__ == "__main__":
    unittest.main()