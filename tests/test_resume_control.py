"""Tests for noninteractive workflow resume/status helpers."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from workflow.run import _normalize_resume_answer, _require_pending_interrupt, _run_once, _session_status


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

    def test_require_pending_interrupt_rejects_stray_answer(self):
        state = SimpleNamespace(next=("implement",), tasks=[])

        with self.assertRaisesRegex(ValueError, "no pending interrupt"):
            _require_pending_interrupt(state, "skip")

    def test_require_pending_interrupt_allows_score_gate_answer(self):
        interrupt = SimpleNamespace(value={"type": "score_gate", "message": "skip?"})
        state = SimpleNamespace(next=("implement",), tasks=[SimpleNamespace(interrupts=[interrupt])])

        _require_pending_interrupt(state, "skip")

    def test_run_once_does_not_stream_when_no_interrupt(self):
        state = SimpleNamespace(next=("implement",), values={"element_queue": ["terminal:kitty"]}, tasks=[])
        graph = MagicMock()
        graph.get_state.return_value = state

        with self.assertRaises(SystemExit) as cm:
            _run_once(graph, {"configurable": {"thread_id": "t"}}, "skip", as_json=True)

        self.assertEqual(cm.exception.code, 2)
        graph.stream.assert_not_called()

    def test_session_status_compacts_design_and_device_profile(self):
        """Status output should trim design/device_profile to summary fields only."""
        state = SimpleNamespace(
            next=("implement",),
            values={
                "current_step": 6,
                "session_dir": "/tmp/rice",
                "design": {"name": "moonlit", "palette": {"base": "#000"}, "mood_tags": ["dark"]},
                "device_profile": {"wm": "plasma", "session_type": "x11", "kernel": "6.1", "cpu": "x"},
                "element_queue": ["a", "b", "c", "d", "e", "f", "g"],
                "errors": ["x", "y"],
            },
            tasks=[],
        )

        status = _session_status(state)
        values = status["values"]

        self.assertEqual(values["design_name"], "moonlit")
        self.assertNotIn("design", values)
        self.assertEqual(values["device_profile"], {"wm": "plasma", "session_type": "x11"})
        self.assertEqual(values["queue_head"], ["a", "b", "c", "d", "e"])
        self.assertEqual(values["queue_len"], 7)
        self.assertEqual(values["errors_count"], 2)
        self.assertNotIn("element_queue", values)


if __name__ == "__main__":
    unittest.main()