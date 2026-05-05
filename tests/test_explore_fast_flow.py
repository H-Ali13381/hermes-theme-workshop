"""Tests for the fast Step 2 creative intake UX."""
from __future__ import annotations

import unittest

from workflow.nodes.explore import (
    DIRECTION_SENTINEL,
    _brief_prompt,
    _fallback_direction,
    _final_prompt,
    _parse_direction,
    _proposal_prompt,
)


class ExploreFastFlowTests(unittest.TestCase):
    def test_brief_prompt_is_direct_and_compact(self):
        prompt = _brief_prompt()
        lowered = prompt.lower()

        self.assertIn("place", lowered)
        self.assertIn("mood", lowered)
        self.assertIn("subtle", lowered)
        self.assertLessEqual(len(prompt.splitlines()), 6)
        for banned in ("agent", "workflow", "orchestrator", "designer asks"):
            self.assertNotIn(banned, lowered)

    def test_proposal_prompt_forces_three_numbered_options(self):
        prompt = _proposal_prompt(
            {"brief": "Control, Cyberpunk, Elden Ring; dark and readable"},
            {"wm": "kde", "apps": {"kitty": True}},
        )

        self.assertIn("exactly 3", prompt)
        self.assertIn("Pick 1, 2, 3", prompt)
        self.assertIn("Control, Cyberpunk, Elden Ring", prompt)

    def test_final_prompt_requires_sentinel_json(self):
        prompt = _final_prompt(
            {"brief": "Control", "proposal": "1. Brutalist red", "choice": "1"},
            {},
        )

        self.assertIn(DIRECTION_SENTINEL, prompt)
        self.assertIn("Do not ask another question", prompt)
        self.assertIn("User choice:\n1", prompt)

    def test_direction_parser_and_fallback_keep_routing_valid(self):
        parsed = _parse_direction(
            "Confirmed\n"
            f"{DIRECTION_SENTINEL}\n"
            '{"stance":"Ghost","mood":["dark"],'
            '"reference_anchor":"Control","name_hypothesis":"oldest-house"}'
        )
        fallback = _fallback_direction({"brief": "Control", "choice": "1"})

        self.assertEqual(parsed["name_hypothesis"], "oldest-house")
        self.assertTrue(fallback["stance"])
        self.assertTrue(fallback["name_hypothesis"])


if __name__ == "__main__":
    unittest.main()
