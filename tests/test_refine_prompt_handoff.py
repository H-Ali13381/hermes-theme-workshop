"""Regression tests for Explore → Refine prompt handoff."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage

from workflow.config import PALETTE_SLOTS
from workflow.nodes.refine import DESIGN_SENTINEL, refine_node


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
            })

        self.assertIn("complete design_system JSON", fake.messages[0].content)
        self.assertEqual(update["current_step"], 3)
        self.assertEqual(update["design"]["name"], "Shadow Signal")


if __name__ == "__main__":
    unittest.main()