"""Tests for platform capability probes."""
from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from workflow.nodes.cleanup.capabilities import probe_capabilities


class CapabilityProbeTests(unittest.TestCase):
    def test_non_kde_state_is_empty(self):
        self.assertEqual(probe_capabilities({"device_profile": {"wm": "gnome"}}), {})

    def test_konsole_transparency_marked_unsupported_on_plasma_wayland(self):
        def fake_run(cmd, **_kwargs):
            result = MagicMock()
            result.returncode = 0
            if cmd[:2] == ["plasmashell", "--version"]:
                result.stdout = "plasmashell 6.6.4\n"
            elif any("Compositing.active" in part for part in cmd):
                result.stdout = "true\n"
            elif any("isEffectLoaded" in part for part in cmd):
                result.stdout = "true\n"
            else:
                result.stdout = ""
            return result

        def fake_which(name):
            return f"/usr/bin/{name}" if name in {"konsole", "kitty"} else None

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}), \
             patch("workflow.nodes.cleanup.capabilities.subprocess.run", side_effect=fake_run), \
             patch("workflow.nodes.cleanup.capabilities.shutil.which", side_effect=fake_which):
            report = probe_capabilities({"device_profile": {"wm": "kde"}})

        self.assertEqual(report["plasma_version"], "6.6.4")
        self.assertTrue(report["kwin_compositing_active"])
        self.assertTrue(report["kwin_blur_loaded"])
        self.assertEqual(report["features"]["konsole_transparency"]["status"], "unsupported")
        self.assertEqual(report["features"]["kitty_transparency"]["status"], "supported")


if __name__ == "__main__":
    unittest.main()