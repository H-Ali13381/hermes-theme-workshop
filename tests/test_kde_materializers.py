"""Unit tests for KDE materializer functions in ricer.py."""
from __future__ import annotations

import importlib.util
import re
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

_MINIMAL_PALETTE = {
    "background": "#1e1e2e", "foreground": "#cdd6f4", "primary": "#89b4fa",
    "secondary": "#f5c2e7", "accent": "#fab387", "surface": "#313244",
    "muted": "#6c7086", "danger": "#f38ba8", "success": "#a6e3a1", "warning": "#f9e2af",
}
_MINIMAL_DESIGN = {"name": "test-theme", "palette": _MINIMAL_PALETTE}

# All-None snapshot returned when we don't care about previous state values.
_NULL_STATE = {k: None for k in (
    "active_colorscheme", "look_and_feel", "kvantum_theme", "widget_style",
    "plasma_theme", "cursor_theme", "icon_theme", "wallpaper", "wallpaper_plugin",
)}


class TestMaterializeKvantumFallback(unittest.TestCase):
    """materialize_kvantum: absent kvantum_theme must be a no-op."""

    def test_no_kvantum_theme_returns_empty(self):
        """Regression: must not fall back to 'kvantum-dark' (not a valid Kvantum theme)."""
        result = ricer.materialize_kvantum({}, backup_ts="20260427T000000")
        self.assertEqual(result, [])

    def test_empty_string_kvantum_theme_returns_empty(self):
        result = ricer.materialize_kvantum({"kvantum_theme": ""}, backup_ts="20260427T000000")
        self.assertEqual(result, [])

    def test_none_kvantum_theme_returns_empty(self):
        result = ricer.materialize_kvantum({"kvantum_theme": None}, backup_ts="20260427T000000")
        self.assertEqual(result, [])

    def test_dry_run_with_valid_theme_records_change(self):
        result = ricer.materialize_kvantum(
            {"kvantum_theme": "KvDark"}, backup_ts="20260427T000000", dry_run=True
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["action"], "dry-run")
        self.assertEqual(result[0]["theme"], "KvDark")

    def test_widget_style_written_as_kvantum_not_kvantum_dark(self):
        """Regression: widgetStyle must be 'kvantum', never 'kvantum-dark'."""
        written_args = []

        def fake_run_cmd(cmd, **kwargs):
            written_args.append(list(cmd))
            return (0, "", "")

        def fake_backup(path, ts, rel):
            return None

        # materialize_kvantum lives in materializers.kde_extras — patch there.
        with (
            patch("materializers.kde_extras.run_cmd", side_effect=fake_run_cmd),
            patch("materializers.kde_extras.backup_file", side_effect=fake_backup),
            patch("materializers.kde_extras._get_kwrite", return_value="kwriteconfig6"),
            patch("materializers.kde_extras.cmd_exists", return_value=False),
        ):
            ricer.materialize_kvantum(
                {"kvantum_theme": "KvDark"}, backup_ts="20260427T000000"
            )

        widget_style_calls = [
            a for a in written_args if "widgetStyle" in a
        ]
        self.assertTrue(widget_style_calls, "widgetStyle was never written")
        for call in widget_style_calls:
            idx = call.index("widgetStyle")
            actual_value = call[idx + 1]
            self.assertEqual(
                actual_value,
                "kvantum",
                f"widgetStyle must be 'kvantum', got {actual_value!r}",
            )
            self.assertNotEqual(actual_value, "kvantum-dark")


class TestMaterializeIconTheme(unittest.TestCase):
    """materialize_icon_theme: absent theme is a no-op; present theme writes correct key."""

    def test_no_icon_theme_returns_empty(self):
        result = ricer.materialize_icon_theme({}, backup_ts="20260427T000000")
        self.assertEqual(result, [])

    def test_dry_run_records_change(self):
        result = ricer.materialize_icon_theme(
            {"icon_theme": "Papirus-Dark"}, backup_ts="20260427T000000", dry_run=True
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["action"], "dry-run")
        self.assertEqual(result[0]["theme"], "Papirus-Dark")

    # materialize_icon_theme lives in materializers.kde_extras
    _ICON_MOD = "materializers.kde_extras"

    def test_writes_icons_group_theme_key(self):
        """kdeglobals [Icons] Theme must be set, not a cursor or widget-style key."""
        written_args = []

        def fake_run_cmd(cmd, **kwargs):
            written_args.append(list(cmd))
            return (0, "", "")

        with (
            patch(f"{self._ICON_MOD}.run_cmd", side_effect=fake_run_cmd),
            patch(f"{self._ICON_MOD}._get_kwrite", return_value="kwriteconfig6"),
            patch(f"{self._ICON_MOD}.cmd_exists", return_value=False),
        ):
            result = ricer.materialize_icon_theme(
                {"icon_theme": "Papirus-Dark"}, backup_ts="20260427T000000"
            )

        icon_writes = [
            a for a in written_args
            if "kdeglobals" in a and "Icons" in a and "Theme" in a
        ]
        self.assertTrue(icon_writes, "kdeglobals [Icons] Theme was never written")
        last = icon_writes[-1]
        self.assertIn("Papirus-Dark", last)

    def test_change_entry_includes_previous_icon_theme(self):
        def fake_run_cmd(cmd, **kwargs):
            if "kreadconfig6" in cmd:
                return (0, "Papirus", "")
            return (0, "", "")

        with (
            patch(f"{self._ICON_MOD}.run_cmd", side_effect=fake_run_cmd),
            patch(f"{self._ICON_MOD}._get_kwrite", return_value="kwriteconfig6"),
            patch(f"{self._ICON_MOD}.cmd_exists", side_effect=lambda n: n == "kreadconfig6"),
        ):
            result = ricer.materialize_icon_theme(
                {"icon_theme": "Papirus-Dark"}, backup_ts="20260427T000000"
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["previous_icon_theme"], "Papirus")


class TestMaterializeKdeLockscreenReadconfig(unittest.TestCase):
    """materialize_kde_lockscreen: kreadconfig fallback loop must match snapshot_kde_state pattern."""

    # materialize_kde_lockscreen lives in materializers.kde_extras
    _MOD = "materializers.kde_extras"

    def _run_with_read_sequence(self, tool_outputs: dict[str, tuple[int, str, str]]):
        """Run materialize_kde_lockscreen with faked cmd_exists and run_cmd.

        tool_outputs maps tool name -> (rc, stdout, stderr).
        Returns the list of run_cmd calls made.
        """
        calls = []

        def fake_cmd_exists(name):
            return name in tool_outputs

        def fake_run_cmd(cmd, **kwargs):
            tool = cmd[0]
            calls.append(list(cmd))
            return tool_outputs.get(tool, (1, "", "error"))

        def fake_backup(path, ts, rel):
            return None

        design = {"palette": {"background": "#1e1e2e"}}
        with (
            patch(f"{self._MOD}.cmd_exists", side_effect=fake_cmd_exists),
            patch(f"{self._MOD}.run_cmd", side_effect=fake_run_cmd),
            patch(f"{self._MOD}.backup_file", side_effect=fake_backup),
            patch(f"{self._MOD}._get_kwrite", return_value=None),
        ):
            result = ricer.materialize_kde_lockscreen(design, backup_ts="20260427T000000")

        return calls, result

    def test_break_only_when_value_found_falls_through_to_kreadconfig5(self):
        """Regression: if kreadconfig6 returns empty output, kreadconfig5 must still be tried."""
        calls, result = self._run_with_read_sequence({
            "kreadconfig6": (0, "", ""),                          # installed, but key unset
            "kreadconfig5": (0, "org.kde.breeze.desktop", ""),   # has the value
        })
        read_tools_called = [c[0] for c in calls if "kreadconfig" in c[0]]
        self.assertIn("kreadconfig5", read_tools_called,
                      "kreadconfig5 must be tried when kreadconfig6 returns empty output")
        self.assertEqual(result[0]["previous_theme"], "org.kde.breeze.desktop")

    def test_break_when_kreadconfig6_returns_value(self):
        """kreadconfig5 must NOT be called when kreadconfig6 already found a value."""
        calls, result = self._run_with_read_sequence({
            "kreadconfig6": (0, "org.kde.breezedark.desktop", ""),
            "kreadconfig5": (0, "org.kde.breeze.desktop", ""),
        })
        read_tools_called = [c[0] for c in calls if "kreadconfig" in c[0]]
        self.assertNotIn("kreadconfig5", read_tools_called,
                         "kreadconfig5 must not be called when kreadconfig6 already succeeded")
        self.assertEqual(result[0]["previous_theme"], "org.kde.breezedark.desktop")


class TestMaterializeKde(unittest.TestCase):
    """materialize_kde: colorscheme file format, apply logic, backup ordering."""

    # materialize_kde lives in materializers.kde
    _KDE = "materializers.kde"

    def _run(self, design=None, dry_run=False, snap_scheme="BreezeClassic",
             apply_output="applied"):
        """Run materialize_kde with all I/O mocked; return (changes, run_cmd_calls)."""
        if design is None:
            design = dict(_MINIMAL_DESIGN)
        calls = []
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(f"{self._KDE}.HOME", Path(tmp)),
            patch(f"{self._KDE}.snapshot_kde_state",
                  return_value={**_NULL_STATE, "active_colorscheme": snap_scheme}),
            patch(f"{self._KDE}.run_cmd", side_effect=lambda cmd, **kw: calls.append(list(cmd)) or (0, apply_output, "")),
            patch(f"{self._KDE}.backup_file", return_value="/tmp/backup"),
            patch(f"{self._KDE}.cmd_exists", return_value=True),
        ):
            changes = ricer.materialize_kde(design, backup_ts="ts", dry_run=dry_run)
        return changes, calls

    def _run_real(self, design=None) -> str:
        """Run with a real tmpdir; return the written .colors file content."""
        if design is None:
            design = dict(_MINIMAL_DESIGN)
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(f"{self._KDE}.HOME", Path(tmp)),
            patch(f"{self._KDE}.snapshot_kde_state", return_value=_NULL_STATE),
            patch(f"{self._KDE}.run_cmd", return_value=(0, "", "")),
            patch(f"{self._KDE}.backup_file", return_value=None),
            patch(f"{self._KDE}.cmd_exists", return_value=False),
        ):
            ricer.materialize_kde(design, backup_ts="ts")
            files = list((Path(tmp) / ".local" / "share" / "color-schemes").glob("*.colors"))
            return files[0].read_text(encoding="utf-8") if files else ""

    def test_generated_colors_file_uses_decimal_rgb_not_hex(self):
        """KDE .colors format requires 'r,g,b' — no '#rrggbb' strings allowed."""
        content = self._run_real()
        self.assertEqual(re.findall(r"Color\s*=\s*#[0-9a-fA-F]{6}", content), [],
                         "Found hex values in .colors")
        self.assertNotEqual(re.findall(r"Color\s*=\s*\d+,\d+,\d+", content), [],
                            "No decimal RGB values found in .colors")

    def test_plasma_apply_colorscheme_called(self):
        changes, calls = self._run()
        apply_calls = [c for c in calls if "plasma-apply-colorscheme" in c]
        self.assertTrue(apply_calls, "plasma-apply-colorscheme was never called")

    def test_breezeClassic_bounce_when_scheme_already_set(self):
        """If the current scheme name matches what we're applying, bounce via BreezeClassic."""
        # Snap returns same name as what materialize_kde would generate
        snap_scheme = "hermes-test-theme"
        _, calls = self._run(snap_scheme=snap_scheme, apply_output="already set")
        apply_calls = [c for c in calls if "plasma-apply-colorscheme" in c]
        themes_applied = [c[-1] for c in apply_calls]
        self.assertIn("BreezeClassic", themes_applied,
                      "BreezeClassic bounce missing when scheme already active")

    def test_kdeglobals_backup_recorded_in_changes(self):
        changes, _ = self._run()
        write_changes = [c for c in changes if c.get("action") == "write"]
        self.assertTrue(write_changes, "No write change recorded")
        self.assertIn("kdeglobals_backup", write_changes[0],
                      "kdeglobals_backup key missing from write change entry")

    def test_dry_run_returns_one_change_no_commands(self):
        changes, calls = self._run(dry_run=True)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["action"], "dry-run")
        apply_calls = [c for c in calls if "plasma-apply-colorscheme" in c]
        self.assertEqual(apply_calls, [], "plasma-apply-colorscheme must not be called on dry-run")

    def test_no_hex_in_colors_parametrized(self):
        """All built-in presets must produce decimal-only .colors output."""
        for preset_name, preset in ricer.PRESETS.items():
            with self.subTest(preset=preset_name):
                content = self._run_real(design=preset)
                hex_hits = re.findall(r"Color\s*=\s*#[0-9a-fA-F]{6}", content)
                self.assertEqual(hex_hits, [], f"Preset {preset_name!r}: hex in .colors")


class TestMaterializeKvantumAdditional(unittest.TestCase):

    # materialize_kvantum lives in materializers.kde_extras
    _KE = "materializers.kde_extras"

    def _run(self):
        calls = []
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(f"{self._KE}.HOME", Path(tmp)),
            patch(f"{self._KE}.run_cmd", side_effect=lambda cmd, **kw: calls.append(list(cmd)) or (0, "", "")),
            patch(f"{self._KE}.backup_file", return_value=None),
            patch(f"{self._KE}._get_kwrite", return_value="kwriteconfig6"),
            patch(f"{self._KE}.cmd_exists", side_effect=lambda n: n == "qdbus6"),
        ):
            ricer.materialize_kvantum({"kvantum_theme": "KvDark"}, backup_ts="ts")
        return calls

    def test_qdbus_reconfigure_called_after_write(self):
        calls = self._run()
        qdbus_idx = [i for i, c in enumerate(calls) if "qdbus6" in c]
        write_idx = [i for i, c in enumerate(calls) if "kwriteconfig6" in c]
        self.assertTrue(qdbus_idx, "qdbus6 reconfigure was never called")
        self.assertTrue(write_idx, "kwriteconfig6 was never called")
        self.assertGreater(min(qdbus_idx), min(write_idx),
                           "qdbus6 must be called AFTER kwriteconfig6")

    def test_kvconfig_written_not_kdeglobals(self):
        """Kvantum materializer must backup kvantum.kvconfig but never kdeglobals."""
        backed = []
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch(f"{self._KE}.HOME", Path(tmp)),
            patch(f"{self._KE}.run_cmd", return_value=(0, "", "")),
            patch(f"{self._KE}.backup_file", side_effect=lambda p, ts, rel: backed.append(rel)),
            patch(f"{self._KE}._get_kwrite", return_value="kwriteconfig6"),
            patch(f"{self._KE}.cmd_exists", return_value=False),
        ):
            ricer.materialize_kvantum({"kvantum_theme": "KvDark"}, backup_ts="ts")
        self.assertTrue(any("kvantum" in r for r in backed), "kvantum.kvconfig not backed up")
        self.assertFalse(any("kdeglobals" in r for r in backed), f"kdeglobals must not be backed up; got {backed}")


class TestSnapshotKdeState(unittest.TestCase):
    """snapshot_kde_state: all 9 fields, fallbacks, edge cases."""

    _ALL_FIELDS = (
        "active_colorscheme", "look_and_feel", "kvantum_theme", "widget_style",
        "plasma_theme", "cursor_theme", "icon_theme", "wallpaper", "wallpaper_plugin",
    )

    # snapshot_kde_state lives in core.snapshots
    _SNAP = "core.snapshots"

    def _snap(self, outputs: dict[str, str],
              kvconfig: str | None = None, appletsrc: str | None = None):
        """Run snapshot_kde_state inside a fresh tmpdir; return the result dict."""
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            if kvconfig is not None:
                kv = home / ".config" / "Kvantum" / "kvantum.kvconfig"
                kv.parent.mkdir(parents=True, exist_ok=True)
                kv.write_text(kvconfig, encoding="utf-8")
            if appletsrc is not None:
                src = home / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
                src.parent.mkdir(parents=True, exist_ok=True)
                src.write_text(appletsrc, encoding="utf-8")
            with (
                patch(f"{self._SNAP}.HOME", home),
                patch(f"{self._SNAP}.cmd_exists", side_effect=lambda n: n == "kreadconfig6"),
                patch(f"{self._SNAP}.run_cmd",
                      side_effect=lambda cmd, **kw: (0, outputs.get(cmd[-1] if cmd else "", ""), "")),
            ):
                return ricer.snapshot_kde_state()

    def test_all_nine_fields_present(self):
        result = self._snap(
            {"ColorScheme": "BreezeClassic", "LookAndFeelPackage": "org.kde.breeze.desktop",
             "widgetStyle": "kvantum", "name": "default", "cursorTheme": "breeze_cursors",
             "Theme": "Papirus-Dark"},
            kvconfig="[General]\ntheme=KvDark\n",
        )
        for field in self._ALL_FIELDS:
            self.assertIn(field, result, f"Field {field!r} missing from snapshot")

    def test_lookandfeel_fallback_when_colorscheme_missing(self):
        result = self._snap({"ColorScheme": "", "LookAndFeelPackage": "org.kde.breezedark.desktop"})
        self.assertIsNone(result["active_colorscheme"])
        self.assertEqual(result["look_and_feel"], "org.kde.breezedark.desktop")

    def test_wallpaper_plugin_captured_from_appletsrc(self):
        result = self._snap({}, appletsrc=(
            "[Containments][1][Wallpaper][org.kde.image]\nImage=/home/user/wall.jpg\nWallpaperplugin=org.kde.image\n"
        ))
        self.assertEqual(result["wallpaper_plugin"], "org.kde.image")

    def test_missing_kvantum_config_returns_none(self):
        self.assertIsNone(self._snap({})["kvantum_theme"])


class TestMaterializeCursor(unittest.TestCase):

    # materialize_cursor lives in materializers.kde_extras
    _KE = "materializers.kde_extras"

    def _run(self, design, dry_run=False, prev_cursor="breeze_cursors"):
        calls = []
        with (
            patch(f"{self._KE}.HOME", Path("/tmp/fake-home")),
            patch(f"{self._KE}.run_cmd",
                  side_effect=lambda cmd, **kw: calls.append(list(cmd)) or
                  (0, prev_cursor if "cursorTheme" in cmd else "", "")),
            patch(f"{self._KE}.backup_file", return_value="/tmp/backup"),
            patch(f"{self._KE}._get_kwrite", return_value="kwriteconfig6"),
            patch(f"{self._KE}.cmd_exists",
                  side_effect=lambda n: n in ("kreadconfig6", "plasma-apply-cursortheme")),
        ):
            changes = ricer.materialize_cursor(design, backup_ts="ts", dry_run=dry_run)
        return changes, calls

    def test_skip_when_no_cursor_theme_in_design(self):
        self.assertEqual(ricer.materialize_cursor({}, backup_ts="ts"), [])

    def test_dry_run_no_writes(self):
        changes, calls = self._run({"cursor_theme": "Breeze"}, dry_run=True)
        self.assertEqual(changes[0]["action"], "dry-run")
        self.assertEqual([c for c in calls if "kwriteconfig6" in c], [])

    def test_kcminputrc_written_with_theme_name(self):
        _, calls = self._run({"cursor_theme": "Breeze"})
        self.assertTrue([c for c in calls if "kcminputrc" in c and "cursorTheme" in c and "Breeze" in c])

    def test_plasma_apply_cursortheme_called(self):
        _, calls = self._run({"cursor_theme": "Breeze"})
        apply = [c for c in calls if "plasma-apply-cursortheme" in c]
        self.assertTrue(apply)
        self.assertIn("Breeze", apply[0])

    def test_previous_value_captured_in_change_record(self):
        changes, _ = self._run({"cursor_theme": "Breeze"}, prev_cursor="breeze_cursors")
        write = [c for c in changes if c.get("action") == "write"]
        self.assertEqual(write[0]["previous_cursor"], "breeze_cursors")


class TestMaterializePlasmaTheme(unittest.TestCase):

    # materialize_plasma_theme lives in materializers.kde_extras
    _KE = "materializers.kde_extras"

    def _run(self, design, dry_run=False, prev_theme="default"):
        calls, backed = [], []
        with (
            patch(f"{self._KE}.run_cmd",
                  side_effect=lambda cmd, **kw: calls.append(list(cmd)) or
                  (0, prev_theme if "name" in cmd else "", "")),
            patch(f"{self._KE}.backup_file",
                  side_effect=lambda p, ts, rel: backed.append(rel)),
            patch(f"{self._KE}._get_kwrite", return_value="kwriteconfig6"),
            patch(f"{self._KE}.cmd_exists",
                  side_effect=lambda n: n in ("kreadconfig6", "plasma-apply-desktoptheme")),
        ):
            changes = ricer.materialize_plasma_theme(design, backup_ts="ts", dry_run=dry_run)
        return changes, calls, backed

    def test_skip_when_no_plasma_theme_in_design(self):
        changes, _, _ = self._run({"palette": _MINIMAL_PALETTE})
        self.assertEqual(changes, [])

    def test_dry_run_returns_single_change(self):
        changes, calls, _ = self._run({"palette": _MINIMAL_PALETTE, "plasma_theme": "breeze-dark"},
                                      dry_run=True)
        self.assertEqual(changes[0]["action"], "dry-run")
        self.assertFalse([c for c in calls if "kwriteconfig6" in c])

    def test_writes_plasmarc_group_theme_key_name(self):
        _, calls, _ = self._run({"palette": _MINIMAL_PALETTE, "plasma_theme": "breeze-dark"})
        target = [c for c in calls
                  if "kwriteconfig6" in c and "plasmarc" in c
                  and "Theme" in c and "name" in c and "breeze-dark" in c]
        self.assertTrue(target, f"kwriteconfig6 --file plasmarc --group Theme --key name not called; calls={calls}")

    def test_plasma_apply_desktoptheme_called(self):
        _, calls, _ = self._run({"palette": _MINIMAL_PALETTE, "plasma_theme": "breeze-dark"})
        apply_calls = [c for c in calls if "plasma-apply-desktoptheme" in c]
        self.assertTrue(apply_calls, "plasma-apply-desktoptheme was not called")
        self.assertIn("breeze-dark", apply_calls[0])

    def test_backup_is_plasmarc_not_kdeglobals(self):
        _, _, backup_labels = self._run({"palette": _MINIMAL_PALETTE, "plasma_theme": "breeze-dark"})
        self.assertTrue(any("plasmarc" in lbl for lbl in backup_labels),
                        f"plasmarc must be backed up; got: {backup_labels}")
        self.assertFalse(any("kdeglobals" in lbl for lbl in backup_labels),
                         f"plasma_theme must NOT backup kdeglobals; got: {backup_labels}")


class TestMaterializeKonsole(unittest.TestCase):

    # materialize_konsole lives in materializers.terminals
    _TERM = "materializers.terminals"

    def _run(self, dry_run=False):
        """Return (changes, colorscheme_contents) — contents read before tmpdir is deleted."""
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            with (
                patch(f"{self._TERM}.HOME", home),
                patch(f"{self._TERM}.run_cmd", return_value=(0, "", "")),
                patch(f"{self._TERM}.backup_file", return_value=None),
                patch(f"{self._TERM}._get_kwrite", return_value="kwriteconfig6"),
                patch(f"{self._TERM}.cmd_exists", return_value=False),
                patch(f"{self._TERM}.snapshot_konsole_state",
                      return_value={"default_profile": "Default.profile"}),
            ):
                changes = ricer.materialize_konsole(_MINIMAL_DESIGN, backup_ts="ts", dry_run=dry_run)
            konsole_dir = home / ".local" / "share" / "konsole"
            contents = [f.read_text(encoding="utf-8") for f in konsole_dir.glob("*.colorscheme")] if konsole_dir.exists() else []
        return changes, contents

    def test_colorscheme_file_written_to_local_share_konsole(self):
        _, contents = self._run()
        self.assertTrue(contents, "No .colorscheme file written to ~/.local/share/konsole/")

    def test_colorscheme_has_required_sections(self):
        _, contents = self._run()
        self.assertTrue(contents)
        for section in ("[Background]", "[Foreground]", "[Color0]", "[Color7]",
                        "[Color0Intense]", "[Color7Intense]"):
            self.assertIn(section, contents[0], f"Missing section {section!r}")

    def test_dry_run_no_files(self):
        changes, contents = self._run(dry_run=True)
        self.assertEqual(changes[0]["action"], "dry-run")
        self.assertFalse(contents)

    def test_previous_profile_captured(self):
        changes, _ = self._run()
        write = [c for c in changes if c.get("action") == "write"]
        self.assertIn("profile_path", write[0])
        self.assertEqual(write[0]["previous_profile"], "Default.profile")


class TestDiscoverAppsKde(unittest.TestCase):

    # discover_apps lives in core.discovery
    _DISC = "core.discovery"

    def test_all_four_kde_subsystems_registered_when_kde_detected(self):
        with (
            patch(f"{self._DISC}.cmd_exists", side_effect=lambda n: n in ("plasmashell", "kwriteconfig6")),
            patch(f"{self._DISC}._get_kwrite", return_value="kwriteconfig6"),
        ):
            apps = ricer.discover_apps()
        for key in ("kvantum", "plasma_theme", "cursor", "kde_lockscreen"):
            self.assertIn(key, apps, f"{key!r} missing from discover_apps")

    def test_kde_subsystems_absent_without_kde(self):
        with (
            patch(f"{self._DISC}.cmd_exists", return_value=False),
            patch(f"{self._DISC}._get_kwrite", return_value=None),
            patch(f"{self._DISC}.os.environ.get", return_value=""),
        ):
            apps = ricer.discover_apps()
        for key in ("kvantum", "plasma_theme", "cursor", "kde_lockscreen"):
            self.assertNotIn(key, apps, f"KDE sub-system {key!r} should not appear when KDE not detected")


if __name__ == "__main__":
    unittest.main()
