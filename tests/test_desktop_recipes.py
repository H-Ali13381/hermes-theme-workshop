"""Regression tests for desktop-environment recipe selection and validation."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from workflow.validators import WorkflowValidator
from workflow.nodes.audit import audit_node
from workflow.nodes.audit.detectors import desktop_recipe_for_wm
from workflow.nodes.refine import build_system_prompt, _validate_design


BASE_DESIGN = {
    "name": "recipe-test",
    "description": "Test design",
    "palette": {
        "background": "#000000",
        "foreground": "#ffffff",
        "primary": "#ff0000",
        "secondary": "#00ff00",
        "accent": "#0000ff",
        "surface": "#111111",
        "muted": "#222222",
        "danger": "#cc0000",
        "success": "#00cc00",
        "warning": "#cccc00",
    },
    "mood_tags": ["test"],
}


def design_with(*keys: str) -> dict:
    design = dict(BASE_DESIGN)
    values = {
        "kvantum_theme": "KvDark",
        "plasma_theme": "default",
        "gtk_theme": "Adwaita-dark",
        "cursor_theme": "default",
        "icon_theme": "Papirus-Dark",
    }
    for key in keys:
        design[key] = values[key]
    return design


class DesktopRecipeTests(unittest.TestCase):
    def test_desktop_recipe_for_wm_maps_supported_desktops(self):
        self.assertEqual(desktop_recipe_for_wm("KDE"), "kde")
        self.assertEqual(desktop_recipe_for_wm("plasma"), "kde")
        self.assertEqual(desktop_recipe_for_wm("GNOME"), "gnome")
        self.assertEqual(desktop_recipe_for_wm("Hyprland"), "hyprland")

    def test_desktop_recipe_for_wm_returns_other_for_unsupported_desktops(self):
        self.assertEqual(desktop_recipe_for_wm("xfce"), "other")
        self.assertEqual(desktop_recipe_for_wm("unknown"), "other")

    def test_audit_reports_unsupported_message_for_other_desktops(self):
        with patch("workflow.nodes.audit.detect_wm", return_value="xfce"), \
             patch("workflow.nodes.audit.detect_chassis", return_value="desktop"), \
             patch("workflow.nodes.audit.detect_screens", return_value=1), \
             patch("workflow.nodes.audit.detect_gpu", return_value={"name": "Test GPU", "vram_mb": 0}), \
             patch("workflow.nodes.audit.detect_apps", return_value={"kitty": True}), \
             patch("workflow.nodes.audit.detect_touchpad", return_value=False), \
             patch("workflow.nodes.audit.get_current_wallpaper", return_value=""):
            update = audit_node({"element_queue": []})

        profile = update["device_profile"]
        self.assertEqual(profile["desktop_recipe"], "other")
        self.assertIn("unsupported", profile["unsupported_message"].lower())
        self.assertIn("GitHub", profile["unsupported_message"])
        self.assertNotIn("element_queue", update)

    def test_validator_uses_recipe_specific_required_keys(self):
        validator = WorkflowValidator()

        kde_ok, kde_reason = validator.design_complete(
            design_with("kvantum_theme", "plasma_theme", "gtk_theme", "cursor_theme", "icon_theme"),
            {"desktop_recipe": "kde"},
        )
        self.assertTrue(kde_ok, kde_reason)

        kde_missing_ok, kde_missing_reason = validator.design_complete(
            design_with("kvantum_theme", "gtk_theme", "cursor_theme", "icon_theme"),
            {"desktop_recipe": "kde"},
        )
        self.assertFalse(kde_missing_ok)
        self.assertIn("plasma_theme", kde_missing_reason)

        gnome_ok, gnome_reason = validator.design_complete(
            design_with("gtk_theme", "cursor_theme", "icon_theme"),
            {"desktop_recipe": "gnome"},
        )
        self.assertTrue(gnome_ok, gnome_reason)

        hyprland_ok, hyprland_reason = validator.design_complete(
            design_with("gtk_theme", "cursor_theme", "icon_theme"),
            {"desktop_recipe": "hyprland"},
        )
        self.assertTrue(hyprland_ok, hyprland_reason)

    def test_other_recipe_is_not_considered_supported_for_validation(self):
        validator = WorkflowValidator()
        ok, reason = validator.design_complete(design_with("gtk_theme", "cursor_theme", "icon_theme"), {"desktop_recipe": "other"})

        self.assertFalse(ok)
        self.assertIn("unsupported", reason.lower())
        self.assertIn("GitHub", reason)

    def test_refine_prompt_is_recipe_specific(self):
        kde_prompt = build_system_prompt("kde")
        gnome_prompt = build_system_prompt("gnome")
        hyprland_prompt = build_system_prompt("hyprland")

        self.assertIn("plasma_theme", kde_prompt)
        self.assertIn("kvantum_theme", kde_prompt)
        self.assertNotIn("plasma_theme", gnome_prompt)
        self.assertNotIn("kvantum_theme", gnome_prompt)
        self.assertNotIn("plasma_theme", hyprland_prompt)

    def test_refine_json_validation_uses_recipe(self):
        self.assertTrue(_validate_design(
            design_with("kvantum_theme", "plasma_theme", "gtk_theme", "cursor_theme", "icon_theme"),
            "kde",
        ))
        self.assertFalse(_validate_design(
            design_with("kvantum_theme", "gtk_theme", "cursor_theme", "icon_theme"),
            "kde",
        ))
        self.assertTrue(_validate_design(
            design_with("gtk_theme", "cursor_theme", "icon_theme"),
            "gnome",
        ))


if __name__ == "__main__":
    unittest.main()
