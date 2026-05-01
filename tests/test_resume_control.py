"""Tests for noninteractive workflow resume/status helpers."""
from __future__ import annotations

import unittest
from types import SimpleNamespace

from workflow.run import _normalize_resume_answer, _session_status


class ResumeControlTests(unittest.TestCase):
    def test_normalize_resume_answer_rejects_empty(self):
        with self.assertRaises(ValueError):
            _normalize_resume_answer("   ")

    def test_session_status_extracts_pending_interrupts(self):
        interrupt = SimpleNamespace(value={
            "step": 6,
            "type": "score_gate",
            "element": "terminal:kitty",
            "score": 7,
            "message": "retry?",
        })
        state = SimpleNamespace(
            next=("implement",),
            values={"current_step": 6, "element_queue": ["terminal:kitty"], "secret": "omit"},
            tasks=[SimpleNamespace(interrupts=[interrupt])],
        )

        status = _session_status(state)

        self.assertEqual(status["next"], ["implement"])
        self.assertEqual(status["values"]["current_step"], 6)
        self.assertNotIn("secret", status["values"])
        self.assertEqual(status["pending_messages"][0]["type"], "score_gate")
        self.assertEqual(status["pending_messages"][0]["element"], "terminal:kitty")


if __name__ == "__main__":
    unittest.main()