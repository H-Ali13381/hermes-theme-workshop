"""Regression tests for Explore → Refine prompt handoff."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

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


class _ScriptedLLM:
    """LLM stub that returns a queued sequence of responses."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0
        self.last_messages = []

    def invoke(self, messages):
        self.last_messages = messages
        self.calls += 1
        if not self._responses:
            return AIMessage(content="")
        return AIMessage(content=self._responses.pop(0))


class RefinePromptHandoffTests(unittest.TestCase):
    def test_refine_seeds_own_prompt_after_explore_messages(self):
        fake = _FakeLLM()

        with patch("workflow.nodes.refine.get_llm", return_value=fake), \
             patch("workflow.nodes.refine.judge_design_creativity", return_value=(True, [])):
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

    def test_refine_seeds_approved_desktop_concept_ui_guidance(self):
        """Approved Step 2.5 visual_context must shape UI/chrome, not palette only."""
        fake = _FakeLLM()

        visual_context = {
            "style_description": "A full desktop RPG menu with emberlit thorn frames.",
            "atmosphere": "campfire glow against black stone",
            "extracted_palette": {"background": "#100c09", "accent": "#d06a2f"},
            "ui_recommendations": (
                "Use ornate thorn window borders, widget menus, a carved launcher, "
                "and a framed terminal rather than stock KDE toolbars."
            ),
            "composition_notes": "A top ritual toolbar replaces the stock panel.",
            "visual_element_plan": [
                {
                    "id": "top_ritual_toolbar",
                    "source_visual_description": "thin thorn-metal strip across the top edge",
                    "desktop_element": "panel/widgets",
                    "implementation_tool": "widgets:quickshell",
                    "fallback_tool": "widgets:eww",
                    "config_targets": ["~/.config/quickshell"],
                    "validation_probe": "KDE panel hidden and Quickshell toolbar visible",
                    "acceptable_deviation": "exact glyph labels may differ",
                }
            ],
            "validation_checklist": ["non-default toolbar replaces or hides stock KDE panel"],
        }

        with patch("workflow.nodes.refine.get_llm", return_value=fake), \
             patch("workflow.nodes.refine.judge_design_creativity", return_value=(True, [])):
            refine_node({
                "messages": [HumanMessage(content="explore chatter")],
                "design": {"stance": "Garden+Blade+Ghost", "name_hypothesis": "cindershrine-reliquary"},
                "visual_context": visual_context,
                "device_profile": {"desktop_recipe": "kde"},
                "loop_counts": {},
                "element_queue": ["terminal:kitty", "gtk_theme"],
            })

        joined = "\n".join(getattr(m, "content", "") for m in fake.messages)
        self.assertIn("AI desktop concept analysis", joined)
        self.assertIn("user-approved full-desktop preview image", joined)
        self.assertIn("ornate thorn window borders", joined)
        self.assertIn("widget menus", joined)
        self.assertIn("preserve the UI/chrome cues", joined)
        self.assertIn("visual_element_plan", joined)
        self.assertIn("widgets:quickshell", joined)
        self.assertIn("validation_checklist", joined)
        self.assertIn("concrete tool/materializer", joined)

    def test_refine_system_prompt_requires_visual_execution_contract(self):
        from workflow.nodes.refine import build_system_prompt

        prompt = build_system_prompt("kde")
        self.assertIn("visual_element_plan", prompt)
        self.assertIn("implementation_tool", prompt)
        self.assertIn("validation_probe", prompt)
        self.assertIn("validation_checklist", prompt)

    def test_refine_preserves_plan_feedback_on_backward_jump(self):
        """Plan dispatch resets refine count to 0; refine must NOT reseed and
        drop the dispatched feedback + revision-seed messages."""
        fake = _FakeLLM()

        # Simulated state right after plan_node dispatched label=refine: the
        # original conversation (system + direction + first design) has been
        # appended with the marked feedback HumanMessage and a revision seed.
        prior_messages = [
            SystemMessage(content="design system prompt"),
            HumanMessage(content="Creative direction established: ..."),
            AIMessage(content=f"<<DESIGN_READY>>\n```json\n{{}}\n```"),
            HumanMessage(content="[PLAN_FEEDBACK] no teal, sharp angular geometry"),
            HumanMessage(content=(
                "The user reviewed the rendered preview and rejected it.\n\n"
                "User feedback:\nno teal, sharp angular geometry\n\n"
                "Please revise the design.json to address this feedback."
            )),
        ]

        with patch("workflow.nodes.refine.get_llm", return_value=fake), \
             patch("workflow.nodes.refine.judge_design_creativity", return_value=(True, [])):
            refine_node({
                "messages": prior_messages,
                "design": {"stance": "Ghost", "name_hypothesis": "shadow-signal"},
                "device_profile": {"desktop_recipe": "kde"},
                "loop_counts": {"refine": 0, "plan": 0},
                "element_queue": [],
            })

        # The LLM must have seen the dispatched feedback, not just system+direction.
        sent = [getattr(m, "content", "") for m in fake.messages]
        joined = "\n".join(sent)
        self.assertIn("no teal, sharp angular geometry", joined)
        self.assertIn("revise the design.json", joined)
        # And the original system prompt is still at the head.
        self.assertTrue(isinstance(fake.messages[0], SystemMessage))

    def test_refine_self_heals_after_malformed_first_response(self):
        """First LLM call lacks the sentinel; the retry pass succeeds without
        falling through to interrupt."""
        good = f"{DESIGN_SENTINEL}\n```json\n{json.dumps(_valid_design())}\n```"
        scripted = _ScriptedLLM(["Here is the design — I'll confirm shortly.", good])

        with patch("workflow.nodes.refine.get_llm", return_value=scripted), \
             patch("workflow.nodes.refine.judge_design_creativity", return_value=(True, [])):
            update = refine_node({
                "messages": [HumanMessage(content="explore chatter")],
                "design": {"stance": "Ghost", "name_hypothesis": "shadow-signal"},
                "device_profile": {"desktop_recipe": "kde"},
                "loop_counts": {},
                "element_queue": ["terminal:kitty", "gtk_theme"],
            })

        self.assertEqual(scripted.calls, 2)
        self.assertEqual(update["current_step"], 3)
        self.assertEqual(update["design"]["name"], "Shadow Signal")
        # Failed retry exchange must not pollute the committed message history.
        committed = update["messages"]
        retry_prompt_leaked = any(
            isinstance(m, HumanMessage) and "previous response failed" in m.content.lower()
            for m in committed
        )
        self.assertFalse(retry_prompt_leaked, "internal retry prompt leaked into state")


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

    def test_eww_target_normalized_to_quickshell_on_wayland_without_required_flag(self):
        design = {
            "widget_layout": [{"name": "clock"}],
            "chrome_strategy": {"method": "eww_frame", "implementation_targets": ["widgets:eww"]},
        }
        queue = _queue_design_elements([], design, {"wm": "hyprland", "session_type": "wayland"})
        self.assertIn("widgets:quickshell", queue)
        self.assertNotIn("widgets:eww", queue)

    def test_eww_required_flag_allows_fallback_override(self):
        design = {
            "widget_layout": [{"name": "clock"}],
            "chrome_strategy": {"method": "eww_frame", "implementation_targets": ["widgets:eww"], "eww_required": True},
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

    def test_visual_element_plan_tools_are_added_to_queue(self):
        design = {
            "visual_element_plan": [
                {
                    "implementation_tool": "widgets:quickshell",
                    "fallback_tool": "widgets:eww",
                    "validation_probe": "top toolbar visible",
                },
                {
                    "implementation_tool": "terminal:kitty",
                    "fallback_tool": "",
                    "validation_probe": "kitty theme loaded",
                },
                {"implementation_tool": "unsupported-freeform-tool"},
            ],
            "chrome_strategy": {"method": "kvantum_only", "implementation_targets": []},
        }
        queue = _queue_design_elements([], design, {"wm": "kde", "session_type": "wayland"})
        self.assertIn("widgets:quickshell", queue)
        self.assertIn("terminal:kitty", queue)
        self.assertNotIn("unsupported-freeform-tool", queue)

    def test_existing_widget_element_not_duplicated(self):
        queue = _queue_design_elements(
            ["terminal:kitty", "widgets:quickshell"],
            self._DESIGN_GENERIC,
            {"wm": "hyprland", "session_type": "wayland"},
        )
        self.assertEqual(queue.count("widgets:quickshell"), 1)


if __name__ == "__main__":
    unittest.main()