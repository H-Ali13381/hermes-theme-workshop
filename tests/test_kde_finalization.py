"""Regression tests for deterministic KDE cleanup finalization."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from workflow.nodes.cleanup.kde_finalize import _forbidden_command_reason, _run, finalize_kde


class KdeFinalizationTests(unittest.TestCase):
    def test_non_kde_state_is_noop(self):
        errors: list[str] = []
        reloaded: list[str] = []

        actions = finalize_kde({"device_profile": {"wm": "gnome"}}, reloaded, errors)

        self.assertEqual(actions, [])
        self.assertEqual(reloaded, [])
        self.assertEqual(errors, [])

    def test_kde_finalization_runs_safe_idempotent_actions(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        ff = tmp / ".config" / "fastfetch" / "config.jsonc"
        ff.parent.mkdir(parents=True)
        ff.write_text("{}\n", encoding="utf-8")
        scheme = tmp / ".local" / "share" / "color-schemes" / "hermes-moss.colors"
        scheme.parent.mkdir(parents=True)
        scheme.write_text("[General]\nName=hermes-moss\n", encoding="utf-8")
        wallpaper = tmp / "wall.png"
        wallpaper.write_text("fake", encoding="utf-8")

        state = {
            "device_profile": {"wm": "kde"},
            "design": {"name": "moss", "wallpaper_path": str(wallpaper), "kvantum_theme": "MossIron"},
            "impl_log": [
                {"element": "fastfetch"},
                {"element": "terminal:kitty"},
                {"element": "window_decorations:kde"},
                {"element": "kvantum_theme"},
                {"element": "cursor_theme"},
            ],
        }
        calls: list[list[str]] = []

        def fake_run(cmd, **_kwargs):
            calls.append(list(cmd))
            ok = MagicMock()
            ok.returncode = 0
            ok.stdout = "123\n" if cmd[:2] == ["pgrep", "-x"] else ""
            ok.stderr = ""
            return ok

        with patch("workflow.nodes.cleanup.kde_finalize.Path.home", return_value=tmp), \
             patch("workflow.nodes.cleanup.kde_finalize.shutil.which", return_value="/usr/bin/tool"), \
             patch("workflow.nodes.cleanup.kde_finalize.subprocess.run", side_effect=fake_run):
            errors: list[str] = []
            reloaded: list[str] = []
            actions = finalize_kde(state, reloaded, errors)

        self.assertEqual(errors, [])
        self.assertTrue((ff.parent / "config.json").is_symlink())
        self.assertNotIn(["pkill", "-SIGUSR1", "kitty"], calls)
        self.assertIn(["plasma-apply-colorscheme", "hermes-moss"], calls)
        self.assertIn(["kwriteconfig6", "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", "kvantum"], calls)
        self.assertIn(["plasma-apply-wallpaperimage", str(wallpaper)], calls)
        self.assertIn(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], calls)
        self.assertEqual((tmp / ".config" / "Kvantum" / "kvantum.kvconfig").read_text(encoding="utf-8"), "[General]\ntheme=MossIron\n")
        self.assertIn("kde-colorscheme", reloaded)
        self.assertIn("kvantum-theme", reloaded)
        self.assertTrue([a for a in actions if a["action"] == "kitty-reload" and a["status"] == "deferred"])
        self.assertTrue([a for a in actions if a["action"] == "plasmashell-health" and a["status"] == "ok"])

    def test_command_guard_blocks_raw_kwin_replace_and_terminal_broadcasts(self):
        self.assertIn("kwin_wayland", _forbidden_command_reason(["kwin_wayland", "--replace"]))
        self.assertIn("terminal", _forbidden_command_reason(["pkill", "-SIGUSR1", "kitty"]))
        self.assertIn("terminal", _forbidden_command_reason(["killall", "konsole"]))
        self.assertIsNone(_forbidden_command_reason(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"]))

    def test_guarded_run_does_not_execute_forbidden_command(self):
        with patch("workflow.nodes.cleanup.kde_finalize.subprocess.run") as run:
            result = _run(["kwin_wayland", "--replace"])

        self.assertIsNone(result)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()