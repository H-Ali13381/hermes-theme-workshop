"""Unit tests for KDE materializer functions in ricer.py."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
RICER_PY = ROOT / "scripts" / "ricer.py"


def _load_ricer():
    spec = importlib.util.spec_from_file_location("ricer", RICER_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ricer = _load_ricer()


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

        with (
            patch.object(ricer, "run_cmd", side_effect=fake_run_cmd),
            patch.object(ricer, "backup_file", side_effect=fake_backup),
            patch.object(ricer, "_get_kwrite", return_value="kwriteconfig6"),
            patch.object(ricer, "cmd_exists", return_value=False),
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

    def test_writes_icons_group_theme_key(self):
        """kdeglobals [Icons] Theme must be set, not a cursor or widget-style key."""
        written_args = []

        def fake_run_cmd(cmd, **kwargs):
            written_args.append(list(cmd))
            return (0, "", "")

        with (
            patch.object(ricer, "run_cmd", side_effect=fake_run_cmd),
            patch.object(ricer, "_get_kwrite", return_value="kwriteconfig6"),
            patch.object(ricer, "cmd_exists", return_value=False),
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
            patch.object(ricer, "run_cmd", side_effect=fake_run_cmd),
            patch.object(ricer, "_get_kwrite", return_value="kwriteconfig6"),
            patch.object(ricer, "cmd_exists", side_effect=lambda n: n == "kreadconfig6"),
        ):
            result = ricer.materialize_icon_theme(
                {"icon_theme": "Papirus-Dark"}, backup_ts="20260427T000000"
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["previous_icon_theme"], "Papirus")


class TestMaterializeKdeLockscreenReadconfig(unittest.TestCase):
    """materialize_kde_lockscreen: kreadconfig fallback loop must match snapshot_kde_state pattern."""

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
            patch.object(ricer, "cmd_exists", side_effect=fake_cmd_exists),
            patch.object(ricer, "run_cmd", side_effect=fake_run_cmd),
            patch.object(ricer, "backup_file", side_effect=fake_backup),
            patch.object(ricer, "_get_kwrite", return_value=None),
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


if __name__ == "__main__":
    unittest.main()
