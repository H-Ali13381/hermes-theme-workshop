"""Unit tests for materialize_kde_lockscreen and _lockscreen_lnf_for_palette."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ricer import materialize_kde_lockscreen, _lockscreen_lnf_for_palette  # noqa: E402

_DARK_PALETTE = {
    "background": "#1a1b26",
    "foreground": "#c0caf5",
    "primary":    "#7aa2f7",
    "secondary":  "#bb9af7",
    "accent":     "#7dcfff",
    "surface":    "#24283b",
    "muted":      "#565f89",
    "danger":     "#f7768e",
    "success":    "#9ece6a",
    "warning":    "#e0af68",
}

_LIGHT_PALETTE = {**_DARK_PALETTE, "background": "#f8f8f2"}

_DARK_DESIGN  = {"name": "ghost-blade", "palette": _DARK_PALETTE, "mood_tags": []}
_LIGHT_DESIGN = {"name": "airy-day",    "palette": _LIGHT_PALETTE, "mood_tags": []}


class LnfSelectionTests(unittest.TestCase):
    def test_dark_background_selects_breezedark(self):
        self.assertEqual(
            _lockscreen_lnf_for_palette(_DARK_PALETTE),
            "org.kde.breezedark.desktop",
        )

    def test_light_background_selects_breeze(self):
        self.assertEqual(
            _lockscreen_lnf_for_palette(_LIGHT_PALETTE),
            "org.kde.breeze.desktop",
        )

    def test_missing_background_defaults_to_breezedark(self):
        # Palette with no background key → falls back to #000000 (dark)
        self.assertEqual(
            _lockscreen_lnf_for_palette({}),
            "org.kde.breezedark.desktop",
        )

    def test_midtone_boundary(self):
        # YIQ of #808080: (128*299 + 128*587 + 128*114) / 1000 = 128 → dark → breezedark
        mid = {**_DARK_PALETTE, "background": "#808080"}
        self.assertEqual(_lockscreen_lnf_for_palette(mid), "org.kde.breezedark.desktop")


class MaterializeKdeLockscreenTests(unittest.TestCase):
    # After the modular refactor, materialize_kde_lockscreen lives in
    # materializers.kde_extras and its helpers in core.{backup,process}.
    # Patches must target the module where each symbol is actually used.
    _HOME_PATCH       = "materializers.kde_extras.HOME"
    _BACKUP_DIR_PATCH = "core.backup.BACKUP_DIR"
    _CMD_EXISTS_PATCH = "materializers.kde_extras.cmd_exists"
    _GET_KWRITE_PATCH = "materializers.kde_extras._get_kwrite"
    _RUN_CMD_PATCH    = "materializers.kde_extras.run_cmd"
    _KREAD_PATCH      = "materializers.kde_extras._kread"
    # Lock-screen materializer also resolves a wallpaper. Patch the resolver
    # to return None by default so the existing focused tests assert only the
    # greeter-theme write path; wallpaper-injection is covered separately.
    _RESOLVE_WP_PATCH = "materializers.kde_extras._resolve_lockscreen_wallpaper"

    def test_dry_run_returns_single_change_without_writing(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        with patch(self._HOME_PATCH, new=tmpdir):
            changes = materialize_kde_lockscreen(_DARK_DESIGN, backup_ts="20260101_000000", dry_run=True)

        self.assertEqual(len(changes), 1)
        change = changes[0]
        self.assertEqual(change["app"], "kde_lockscreen")
        self.assertEqual(change["action"], "dry-run")
        self.assertEqual(change["greeter_theme"], "org.kde.breezedark.desktop")
        self.assertIn("kscreenlockerrc", change["config_path"])

        # Nothing written
        config_path = tmpdir / ".config" / "kscreenlockerrc"
        self.assertFalse(config_path.exists())

    def test_dark_palette_writes_breezedark_theme(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        with patch(self._HOME_PATCH, new=tmpdir), \
             patch(self._BACKUP_DIR_PATCH, new=tmpdir / "backup"), \
             patch(self._CMD_EXISTS_PATCH, return_value=False), \
             patch(self._GET_KWRITE_PATCH, return_value="kwriteconfig6"), \
             patch(self._RESOLVE_WP_PATCH, return_value=None), \
             patch(self._RUN_CMD_PATCH) as mock_run:
            mock_run.return_value = (0, "", "")
            changes = materialize_kde_lockscreen(_DARK_DESIGN, backup_ts="20260101_000000")

        self.assertEqual(len(changes), 1)
        change = changes[0]
        self.assertEqual(change["app"], "kde_lockscreen")
        self.assertEqual(change["action"], "write")
        self.assertEqual(change["greeter_theme"], "org.kde.breezedark.desktop")

        # kwriteconfig6 called with correct args (only the greeter Theme write
        # when no wallpaper is resolved).
        kwrite_calls = [c for c in mock_run.call_args_list
                        if c.args[0][0] == "kwriteconfig6"]
        self.assertEqual(len(kwrite_calls), 1)
        cmd = kwrite_calls[0].args[0]
        self.assertIn("--group", cmd)
        self.assertIn("Greeter", cmd)
        self.assertIn("--key", cmd)
        self.assertIn("Theme", cmd)
        self.assertIn("org.kde.breezedark.desktop", cmd)

    def test_light_palette_writes_breeze_theme(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        with patch(self._HOME_PATCH, new=tmpdir), \
             patch(self._BACKUP_DIR_PATCH, new=tmpdir / "backup"), \
             patch(self._CMD_EXISTS_PATCH, return_value=False), \
             patch(self._GET_KWRITE_PATCH, return_value="kwriteconfig6"), \
             patch(self._RESOLVE_WP_PATCH, return_value=None), \
             patch(self._RUN_CMD_PATCH) as mock_run:
            mock_run.return_value = (0, "", "")
            changes = materialize_kde_lockscreen(_LIGHT_DESIGN, backup_ts="20260101_000000")

        self.assertEqual(changes[0]["greeter_theme"], "org.kde.breeze.desktop")
        kwrite_calls = [c for c in mock_run.call_args_list
                        if c.args[0][0] == "kwriteconfig6"]
        self.assertIn("org.kde.breeze.desktop", kwrite_calls[0].args[0])

    def test_change_record_has_all_required_fields(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        with patch(self._HOME_PATCH, new=tmpdir), \
             patch(self._BACKUP_DIR_PATCH, new=tmpdir / "backup"), \
             patch(self._CMD_EXISTS_PATCH, return_value=False), \
             patch(self._GET_KWRITE_PATCH, return_value=None), \
             patch(self._RESOLVE_WP_PATCH, return_value=None), \
             patch(self._RUN_CMD_PATCH, return_value=(0, "", "")):
            changes = materialize_kde_lockscreen(_DARK_DESIGN, backup_ts="20260101_000000")

        change = changes[0]
        # The materializer now also records wallpaper context for rollback +
        # downstream consumers (lockscreen materializer was extended to write
        # the lock-screen wallpaper alongside the greeter theme).
        for field in ("app", "action", "greeter_theme", "config_path", "backup",
                      "previous_theme", "wallpaper", "previous_wallpaper", "fill_mode"):
            self.assertIn(field, change, f"missing field: {field}")

    def test_previous_theme_captured_when_kreadconfig_succeeds(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)

        # _kread is imported into kde_extras; patch it there to return the
        # "currently active" lock screen theme without running kreadconfig.
        with patch(self._HOME_PATCH, new=tmpdir), \
             patch(self._BACKUP_DIR_PATCH, new=tmpdir / "backup"), \
             patch(self._CMD_EXISTS_PATCH, return_value=False), \
             patch(self._GET_KWRITE_PATCH, return_value=None), \
             patch(self._RESOLVE_WP_PATCH, return_value=None), \
             patch(self._RUN_CMD_PATCH, return_value=(0, "", "")), \
             patch(self._KREAD_PATCH, return_value="org.kde.breeze.desktop"):
            changes = materialize_kde_lockscreen(_DARK_DESIGN, backup_ts="20260101_000000")

        self.assertEqual(changes[0]["previous_theme"], "org.kde.breeze.desktop")

    def test_backup_created_when_kscreenlockerrc_exists(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        backup_dir = tmpdir / "backup"
        config_path = tmpdir / ".config" / "kscreenlockerrc"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("[Daemon]\nTimeout=15\n", encoding="utf-8")

        with patch(self._HOME_PATCH, new=tmpdir), \
             patch(self._BACKUP_DIR_PATCH, new=backup_dir), \
             patch(self._CMD_EXISTS_PATCH, return_value=False), \
             patch(self._GET_KWRITE_PATCH, return_value=None), \
             patch(self._RESOLVE_WP_PATCH, return_value=None), \
             patch(self._RUN_CMD_PATCH, return_value=(0, "", "")):
            changes = materialize_kde_lockscreen(_DARK_DESIGN, backup_ts="20260101_000000")

        self.assertIsNotNone(changes[0]["backup"])
        backup_path = Path(changes[0]["backup"])
        self.assertTrue(backup_path.exists())
        self.assertIn("Timeout", backup_path.read_text(encoding="utf-8"))

    def test_wallpaper_writes_image_and_fill_mode(self):
        # When _resolve_lockscreen_wallpaper returns a path, the materializer
        # also writes WallpaperPlugin, the Image URI, and FillMode in addition
        # to the greeter Theme.
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        wp = "/tmp/lockscreen-test.png"
        with patch(self._HOME_PATCH, new=tmpdir), \
             patch(self._BACKUP_DIR_PATCH, new=tmpdir / "backup"), \
             patch(self._CMD_EXISTS_PATCH, return_value=False), \
             patch(self._GET_KWRITE_PATCH, return_value="kwriteconfig6"), \
             patch(self._RESOLVE_WP_PATCH, return_value=wp), \
             patch(self._RUN_CMD_PATCH) as mock_run:
            mock_run.return_value = (0, "", "")
            changes = materialize_kde_lockscreen(_DARK_DESIGN, backup_ts="20260101_000000")

        kwrite_calls = [c for c in mock_run.call_args_list
                        if c.args[0][0] == "kwriteconfig6"]
        self.assertEqual(len(kwrite_calls), 4)
        flat = [tok for c in kwrite_calls for tok in c.args[0]]
        self.assertIn("Theme", flat)
        self.assertIn("WallpaperPlugin", flat)
        self.assertIn("Image", flat)
        self.assertIn("FillMode", flat)
        self.assertIn(f"file://{wp}", flat)
        self.assertEqual(changes[0]["wallpaper"], wp)
        self.assertEqual(changes[0]["fill_mode"], "2")


class RoutingTests(unittest.TestCase):
    def setUp(self):
        from workflow.nodes.implement.apply import _element_to_materializer
        self._map = _element_to_materializer

    def test_lock_screen_kde_maps_to_kde_lockscreen(self):
        self.assertEqual(self._map("lock_screen:kde"), "kde_lockscreen")

    def test_lock_screen_kde_does_not_map_to_kde(self):
        self.assertNotEqual(self._map("lock_screen:kde"), "kde")

    def test_lock_screen_hyprlock_unchanged(self):
        self.assertEqual(self._map("lock_screen:hyprlock"), "hyprlock")

    def test_shell_prompt_starship_unchanged(self):
        self.assertEqual(self._map("shell_prompt:starship"), "starship")

    def test_terminal_kitty_unchanged(self):
        self.assertEqual(self._map("terminal:kitty"), "kitty")

    def test_window_decorations_gnome_maps_to_gnome_shell(self):
        self.assertEqual(self._map("window_decorations:gnome"), "gnome_shell")

    def test_lock_screen_gnome_maps_to_gnome_lockscreen(self):
        self.assertEqual(self._map("lock_screen:gnome"), "gnome_lockscreen")

    def test_window_decorations_gnome_does_not_map_to_gnome(self):
        self.assertNotEqual(self._map("window_decorations:gnome"), "gnome")

    def test_lock_screen_gnome_does_not_map_to_gnome(self):
        self.assertNotEqual(self._map("lock_screen:gnome"), "gnome")


if __name__ == "__main__":
    unittest.main()
