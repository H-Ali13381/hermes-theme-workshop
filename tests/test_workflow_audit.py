"""Regression tests for workflow audit state updates."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from workflow.nodes.audit import audit_node


_DETECTED_APPS = {
    "kitty": True,
    "waybar": False,
    "polybar": False,
    "rofi": False,
    "wofi": False,
    "dunst": False,
    "mako": False,
    "swaync": False,
    "hyprlock": False,
    "swaylock": False,
    "starship": False,
    "fastfetch": False,
    "neofetch": False,
}


class AuditNodeStateTests(unittest.TestCase):
    def _run_audit(self, state: dict) -> dict:
        with patch("workflow.nodes.audit.detect_wm", return_value="kde"), \
             patch("workflow.nodes.audit.detect_chassis", return_value="desktop"), \
             patch("workflow.nodes.audit.detect_screens", return_value=1), \
             patch("workflow.nodes.audit.detect_gpu", return_value={"name": "Test GPU", "vram_mb": 0}), \
             patch("workflow.nodes.audit.detect_apps", return_value=dict(_DETECTED_APPS)), \
             patch("workflow.nodes.audit.detect_touchpad", return_value=False), \
             patch("workflow.nodes.audit.get_current_wallpaper", return_value=""):
            return audit_node(state)

    def test_initial_audit_populates_element_queue(self):
        update = self._run_audit({"element_queue": []})

        self.assertIn("element_queue", update)
        self.assertIn("terminal:kitty", update["element_queue"])
        self.assertIn("gtk_theme", update["element_queue"])

    def test_resume_audit_does_not_overwrite_existing_element_queue(self):
        update = self._run_audit({"element_queue": ["gtk_theme"]})

        self.assertNotIn("element_queue", update)
        self.assertEqual("kde", update["device_profile"]["wm"])


class UnsupportedDesktopEarlyStopTests(unittest.TestCase):
    def _audit_state_for_wm(self, wm: str) -> dict:
        with patch("workflow.nodes.audit.detect_wm", return_value=wm), \
             patch("workflow.nodes.audit.detect_chassis", return_value="desktop"), \
             patch("workflow.nodes.audit.detect_screens", return_value=1), \
             patch("workflow.nodes.audit.detect_gpu", return_value={"name": "GPU", "vram_mb": 0}), \
             patch("workflow.nodes.audit.detect_apps", return_value=dict(_DETECTED_APPS)), \
             patch("workflow.nodes.audit.detect_touchpad", return_value=False), \
             patch("workflow.nodes.audit.get_current_wallpaper", return_value=""):
            return audit_node({})

    def test_unsupported_desktop_classified_as_other(self):
        # graph.py routes to END when desktop_recipe == "other"
        state = self._audit_state_for_wm("i3")
        self.assertEqual(state.get("device_profile", {}).get("desktop_recipe"), "other")

    def test_unsupported_desktop_message_is_set(self):
        state = self._audit_state_for_wm("i3")
        msg = state.get("device_profile", {}).get("unsupported_message", "")
        self.assertIn("unsupported", msg.lower())

    def test_supported_desktop_not_classified_as_other(self):
        state = self._audit_state_for_wm("kde")
        self.assertEqual(state.get("device_profile", {}).get("desktop_recipe"), "kde")


if __name__ == "__main__":
    unittest.main()
