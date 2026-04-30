"""Tests for cleanup reload functions propagating errors."""
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from workflow.nodes.cleanup.reloader import (
    reload_dunst, reload_mako, reload_swaync, reload_waybar,
)


class ReloadErrorPropagationTests(unittest.TestCase):
    def test_waybar_not_found_appends_to_errors(self):
        errors, reloaded = [], []
        with patch("workflow.nodes.cleanup.reloader.subprocess.run") as mock_run, \
             patch("workflow.nodes.cleanup.reloader.subprocess.Popen",
                   side_effect=FileNotFoundError):
            mock_run.return_value.returncode = 1
            reload_waybar(reloaded, errors)

        matching = [e for e in errors if "waybar" in e]
        self.assertTrue(matching, f"Expected 'waybar' error, got: {errors}")

    def test_dunst_not_found_appends_to_errors(self):
        errors, reloaded = [], []
        with patch("workflow.nodes.cleanup.reloader.subprocess.run"), \
             patch("workflow.nodes.cleanup.reloader.subprocess.Popen",
                   side_effect=FileNotFoundError):
            reload_dunst(reloaded, errors)

        matching = [e for e in errors if "dunst" in e]
        self.assertTrue(matching, f"Expected 'dunst' error, got: {errors}")

    def test_mako_not_found_appends_to_errors(self):
        errors, reloaded = [], []
        with patch("workflow.nodes.cleanup.reloader.subprocess.run") as mock_run, \
             patch("workflow.nodes.cleanup.reloader.subprocess.Popen",
                   side_effect=FileNotFoundError):
            mock_run.return_value.returncode = 1
            reload_mako(reloaded, errors)

        matching = [e for e in errors if "mako" in e]
        self.assertTrue(matching, f"Expected 'mako' error, got: {errors}")

    def test_swaync_not_found_appends_to_errors(self):
        errors, reloaded = [], []
        with patch("workflow.nodes.cleanup.reloader.subprocess.run") as mock_run, \
             patch("workflow.nodes.cleanup.reloader.subprocess.Popen",
                   side_effect=FileNotFoundError):
            mock_run.return_value.returncode = 1
            reload_swaync(reloaded, errors)

        matching = [e for e in errors if "swaync" in e]
        self.assertTrue(matching, f"Expected 'swaync' error, got: {errors}")

    def test_successful_reload_no_errors(self):
        errors, reloaded = [], []
        ok = MagicMock()
        ok.returncode = 0
        with patch("workflow.nodes.cleanup.reloader.subprocess.run", return_value=ok):
            reload_waybar(reloaded, errors)

        self.assertEqual(errors, [])
        self.assertIn("waybar", reloaded)


if __name__ == "__main__":
    unittest.main()
