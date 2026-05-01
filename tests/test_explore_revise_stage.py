"""Tests for the Step 2 REVISE_STAGE — re-entry from plan-feedback backward jump."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from workflow.nodes import explore as explore_mod


class _RecordingLLM:
    def __init__(self, content: str):
        self.content = content
        self.received: list = []

    def invoke(self, messages):
        self.received.append(messages)
        return SimpleNamespace(content=self.content)


def _state_for_revise() -> dict:
    return {
        "device_profile": {
            "wm": "kwin_wayland",
            "chassis": "desktop",
            "screens": 2,
            "gpu": {"name": "AMD"},
            "apps": {"kitty": True, "rofi": True},
            "fal_available": False,
            "current_wallpaper": "",
        },
        "explore_intake": {
            "stage": explore_mod.REVISE_STAGE,
            "brief": "neon ruins, slow synth, ghost in the shell",
            "prior_direction": {
                "stance": "Ghost+Blade",
                "mood": ["dark", "precise", "cold"],
                "reference_anchor": "GitS dystopia",
                "name_hypothesis": "shadow-signal",
            },
            "rejection_feedback": "too cold and clinical, I wanted warmer atmosphere",
        },
        "loop_counts": {},
    }


class ReviseStageTests(unittest.TestCase):
    def test_revise_prompt_includes_brief_prior_direction_and_feedback(self):
        intake = _state_for_revise()["explore_intake"]
        profile = _state_for_revise()["device_profile"]

        prompt = explore_mod._revise_prompt(intake, profile)

        self.assertIn("neon ruins", prompt)
        self.assertIn("Ghost+Blade", prompt)
        self.assertIn("too cold and clinical", prompt)
        self.assertIn("Original brief", prompt)
        self.assertIn("Previously confirmed direction", prompt)
        self.assertIn("rejection feedback", prompt.lower())

    def test_revise_prompt_handles_missing_prior_direction(self):
        intake = {"stage": "revise", "brief": "x", "rejection_feedback": "y", "prior_direction": {}}
        prompt = explore_mod._revise_prompt(intake, {})
        self.assertIn("(none recorded)", prompt)

    def test_revise_stage_calls_llm_and_transitions_to_finalize(self):
        state = _state_for_revise()
        proposal_text = (
            "1. Warm Signal — same architecture, lit by amber.\n"
            "Pick 1, combine, or tweak."
        )
        fake = _RecordingLLM(proposal_text)

        with patch.object(explore_mod, "get_llm", return_value=fake), \
             patch.object(explore_mod, "interrupt", return_value="1"):
            result = explore_mod.explore_node(state)

        # LLM was called with the revise prompt.
        self.assertEqual(len(fake.received), 1)
        sent_human = fake.received[0][1].content
        self.assertIn("neon ruins", sent_human)
        self.assertIn("too cold", sent_human)

        # Stage advanced to finalize and choice was captured.
        intake = result["explore_intake"]
        self.assertEqual(intake["stage"], explore_mod.FINALIZE_STAGE)
        self.assertEqual(intake["choice"], "1")
        self.assertEqual(intake["proposal"], proposal_text)

        # Original brief preserved across the rewind.
        self.assertEqual(intake["brief"], "neon ruins, slow synth, ghost in the shell")
        # Loop counter incremented.
        self.assertEqual(result["loop_counts"]["explore"], 1)

    def test_revise_stage_uses_fallback_when_llm_returns_blank(self):
        state = _state_for_revise()
        fake = _RecordingLLM("   ")

        with patch.object(explore_mod, "get_llm", return_value=fake), \
             patch.object(explore_mod, "interrupt", return_value="1"):
            result = explore_mod.explore_node(state)

        proposal = result["explore_intake"]["proposal"]
        self.assertIn("dialed back", proposal)
        self.assertIn("too cold", proposal)

    def test_fallback_revise_proposal_uses_rejection_feedback(self):
        intake = {"rejection_feedback": "I wanted something warmer"}
        out = explore_mod._fallback_revise_proposal(intake)
        self.assertIn("warmer", out)
        self.assertIn("Pick 1", out)

    def test_revise_stage_constant_distinct_from_other_stages(self):
        # Guard against accidental aliasing.
        stages = {
            explore_mod.BRIEF_STAGE,
            explore_mod.PROPOSE_STAGE,
            explore_mod.FINALIZE_STAGE,
            explore_mod.REVISE_STAGE,
        }
        self.assertEqual(len(stages), 4)


if __name__ == "__main__":
    unittest.main()
