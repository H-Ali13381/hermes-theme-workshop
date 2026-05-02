"""Regression tests for Explore → Refine prompt handoff."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from workflow.config import PALETTE_SLOTS
from workflow.nodes.refine import DESIGN_SENTINEL, refine_node, _queue_design_elements


def _valid_design() -> dict:
    return {
        "name": "Shadow Signal",
        "description": "Dark readable test theme.",
        "palette": {slot: "#111111" for slot in PALETTE_SLOTS},
        "mood_tags": ["dark", "readable"],
        "kvantum_theme": "KvDark",
        "plasma_theme": "default",
        "cursor_theme": "default",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "originality_strategy": {
            "vision_alignment": "quiet signal-desk, not generic KDE",
            "non_default_moves": ["signal rail", "floating command frame", "terminal border ritual"],
        },
        "chrome_strategy": {
            "method": "eww_frame + terminal_config",
            "rounded_corners": {"enabled": True, "radius_px": 28},
            "implementation_targets": ["widgets:eww", "terminal:kitty"],
        },
        "panel_layout": {
            "mode": "eww-overlay",
            "placement": "top command strip plus bottom dock",
            "shape": "floating capsule chrome",
            "controls": ["workspaces", "launcher", "system meters"],
        },
        "widget_layout": [
            {"name": "clock altar", "position": "top right", "data": "time", "visual": "glowing capsule"},
            {"name": "system spine", "position": "left rail", "data": "cpu ram", "visual": "stacked gauges"},
            {"name": "focus card", "position": "bottom right", "data": "date note", "visual": "floating plaque"},
        ],
    }


class _FakeLLM:
    def __init__(self):
        self.messages = []

    def invoke(self, messages):
        self.messages = messages
        return AIMessage(
            content=f"Ready\n{DESIGN_SENTINEL}\n```json\n{json.dumps(_valid_design())}\n```"
        )


class RefinePromptHandoffTests(unittest.TestCase):
    def test_refine_seeds_own_prompt_after_explore_messages(self):
        fake = _FakeLLM()

        with patch("workflow.nodes.refine.get_llm", return_value=fake):
            update = refine_node({
                "messages": [HumanMessage(content="explore chatter")],
                "design": {"stance": "Ghost", "name_hypothesis": "shadow-signal"},
                "device_profile": {"desktop_recipe": "kde"},
                "loop_counts": {},
                "element_queue": ["terminal:kitty", "gtk_theme"],
            })

        self.assertIn("complete design_system JSON", fake.messages[0].content)
        self.assertEqual(update["current_step"], 3)
        self.assertEqual(update["design"]["name"], "Shadow Signal")
        self.assertIn("widgets:eww", update["element_queue"])


class WidgetFrameworkSelectionTests(unittest.TestCase):
    """Verify _queue_design_elements picks Quickshell vs EWW correctly."""

    _DESIGN_GENERIC = {
        "widget_layout": [{"name": "clock", "position": "top right"}],
        "chrome_strategy": {"method": "overlay", "implementation_targets": []},
    }

    def test_hyprland_defaults_to_quickshell(self):
        queue = _queue_design_elements([], self._DESIGN_GENERIC, {"wm": "hyprland", "session_type": "wayland"})
        self.assertIn("widgets:quickshell", queue)
        self.assertNotIn("widgets:eww", queue)

    def test_kde_wayland_defaults_to_quickshell(self):
        queue = _queue_design_elements([], self._DESIGN_GENERIC, {"wm": "kde", "session_type": "wayland"})
        self.assertIn("widgets:quickshell", queue)
        self.assertNotIn("widgets:eww", queue)

    def test_kde_x11_falls_back_to_eww(self):
        queue = _queue_design_elements([], self._DESIGN_GENERIC, {"wm": "kde", "session_type": "x11"})
        self.assertIn("widgets:eww", queue)
        self.assertNotIn("widgets:quickshell", queue)

    def test_gnome_falls_back_to_eww(self):
        queue = _queue_design_elements([], self._DESIGN_GENERIC, {"wm": "gnome", "session_type": "wayland"})
        self.assertIn("widgets:eww", queue)

    def test_unknown_session_falls_back_to_eww(self):
        queue = _queue_design_elements([], self._DESIGN_GENERIC, {"wm": "kde", "session_type": ""})
        self.assertIn("widgets:eww", queue)

    def test_explicit_eww_target_overrides_default_on_hyprland(self):
        design = {
            "widget_layout": [{"name": "clock"}],
            "chrome_strategy": {"method": "eww_frame", "implementation_targets": ["widgets:eww"]},
        }
        queue = _queue_design_elements([], design, {"wm": "hyprland", "session_type": "wayland"})
        self.assertIn("widgets:eww", queue)
        self.assertNotIn("widgets:quickshell", queue)

    def test_explicit_quickshell_target_overrides_default_on_kde_x11(self):
        design = {
            "widget_layout": [{"name": "clock"}],
            "chrome_strategy": {"method": "overlay", "implementation_targets": ["widgets:quickshell"]},
        }
        queue = _queue_design_elements([], design, {"wm": "kde", "session_type": "x11"})
        self.assertIn("widgets:quickshell", queue)
        self.assertNotIn("widgets:eww", queue)

    def test_no_widget_design_adds_nothing(self):
        design = {"chrome_strategy": {"method": "kvantum_only", "implementation_targets": []}}
        queue = _queue_design_elements(["terminal:kitty"], design, {"wm": "hyprland", "session_type": "wayland"})
        self.assertEqual(queue, ["terminal:kitty"])

    def test_existing_widget_element_not_duplicated(self):
        queue = _queue_design_elements(
            ["terminal:kitty", "widgets:quickshell"],
            self._DESIGN_GENERIC,
            {"wm": "hyprland", "session_type": "wayland"},
        )
        self.assertEqual(queue.count("widgets:quickshell"), 1)


if __name__ == "__main__":
    unittest.main()