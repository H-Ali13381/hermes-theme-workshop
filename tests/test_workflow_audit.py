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
        # Use a multi-item queue that is clearly non-empty so a returned
        # empty list or a partial list would also fail the assertion.
        original_queue = ["gtk_theme", "terminal:kitty", "window_decorations:kde"]
        state = {"element_queue": original_queue}
        update = self._run_audit(state)

        # audit_node must NOT emit a new element_queue when one already exists
        self.assertNotIn("element_queue", update,
                         "audit_node should not overwrite an existing element_queue")
        # The original queue in the passed-in state must be untouched
        self.assertEqual(original_queue, state["element_queue"],
                         "audit_node must not mutate the caller's state dict")
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

    def test_gnome_desktop_classified_as_gnome(self):
        state = self._audit_state_for_wm("gnome")
        self.assertEqual(state.get("device_profile", {}).get("desktop_recipe"), "gnome")


class GnomeElementQueueTests(unittest.TestCase):
    """Verify that a GNOME session produces a non-empty, correct element queue."""

    def _run_gnome_audit(self, apps: dict | None = None) -> dict:
        merged = dict(_DETECTED_APPS)
        if apps:
            merged.update(apps)
        with patch("workflow.nodes.audit.detect_wm", return_value="gnome"), \
             patch("workflow.nodes.audit.detect_chassis", return_value="desktop"), \
             patch("workflow.nodes.audit.detect_screens", return_value=1), \
             patch("workflow.nodes.audit.detect_gpu", return_value={"name": "Test GPU", "vram_mb": 0}), \
             patch("workflow.nodes.audit.detect_apps", return_value=merged), \
             patch("workflow.nodes.audit.detect_touchpad", return_value=False), \
             patch("workflow.nodes.audit.get_current_wallpaper", return_value=""):
            return audit_node({"element_queue": []})

    def test_gnome_queue_includes_window_decorations(self):
        update = self._run_gnome_audit()
        self.assertIn("window_decorations:gnome", update["element_queue"])

    def test_gnome_queue_includes_lock_screen(self):
        update = self._run_gnome_audit()
        self.assertIn("lock_screen:gnome", update["element_queue"])

    def test_gnome_queue_includes_gtk_theme(self):
        update = self._run_gnome_audit()
        self.assertIn("gtk_theme", update["element_queue"])

    def test_gnome_queue_includes_terminal_when_kitty_installed(self):
        update = self._run_gnome_audit({"kitty": True})
        self.assertIn("terminal:kitty", update["element_queue"])

    def test_gnome_queue_does_not_include_hyprland_elements(self):
        update = self._run_gnome_audit()
        queue = update["element_queue"]
        self.assertNotIn("window_decorations:hyprland", queue)
        self.assertNotIn("lock_screen:hyprlock", queue)

    def test_gnome_queue_does_not_include_kde_elements(self):
        update = self._run_gnome_audit()
        queue = update["element_queue"]
        self.assertNotIn("window_decorations:kde", queue)
        self.assertNotIn("lock_screen:kde", queue)


if __name__ == "__main__":
    unittest.main()
