"""Tests for implementation spec structured output and apply element."""
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from workflow.nodes.implement.apply import apply_element
from workflow.nodes.implement.spec import ElementSpec, write_spec


class _FakeStructuredLLM:
    def __init__(self, response):
        self.response = response

    def invoke(self, messages):
        self.messages = messages
        return self.response


class _FakeLLM:
    requested_schema = None
    structured_response = None

    def with_structured_output(self, schema):
        type(self).requested_schema = schema
        return _FakeStructuredLLM(type(self).structured_response)


class ImplementSpecTests(unittest.TestCase):
    def test_element_spec_defaults_optional_fields(self):
        spec = ElementSpec(targets=["~/.config/kitty/theme.conf"], palette_keys=["background"])

        self.assertEqual(spec.font, "N/A")
        self.assertEqual(spec.radii, "N/A")
        self.assertEqual(spec.notes, "")

    def test_write_spec_uses_langchain_structured_output(self):
        _FakeLLM.structured_response = ElementSpec(
            targets=["~/.config/kitty/theme.conf"],
            palette_keys=["background", "foreground"],
            font="JetBrainsMono 12",
            radii="8",
            notes="Reload kitty",
        )
        _FakeLLM.requested_schema = None

        with patch("workflow.nodes.implement.spec.get_llm", return_value=_FakeLLM()):
            result = write_spec("terminal:kitty", {"name": "test"})

        self.assertIs(_FakeLLM.requested_schema, ElementSpec)
        self.assertEqual(result["targets"], ["~/.config/kitty/theme.conf"])
        self.assertEqual(result["palette_keys"], ["background", "foreground"])
        self.assertEqual(result["font"], "JetBrainsMono 12")
        self.assertEqual(result["radii"], "8")
        self.assertEqual(result["notes"], "Reload kitty")

    def test_write_spec_accepts_structured_output_dict(self):
        _FakeLLM.structured_response = {
            "targets": ["~/.config/rofi/config.rasi"],
            "palette_keys": ["primary"],
            "font": "N/A",
            "radii": "4",
            "notes": "Reload rofi",
        }

        with patch("workflow.nodes.implement.spec.get_llm", return_value=_FakeLLM()):
            result = write_spec("launcher:rofi", {"name": "test"})

        self.assertEqual(result["targets"], ["~/.config/rofi/config.rasi"])
        self.assertEqual(result["palette_keys"], ["primary"])
        self.assertEqual(result["notes"], "Reload rofi")

    def test_write_spec_returns_safe_fallback_on_structured_output_error(self):
        class FailingLLM:
            def with_structured_output(self, schema):
                raise RuntimeError("structured output unavailable")

        with patch("workflow.nodes.implement.spec.get_llm", return_value=FailingLLM()):
            result = write_spec("terminal:kitty", {"name": "test"})

        self.assertEqual(result["targets"], [])
        self.assertEqual(result["palette_keys"], [])
        self.assertEqual(result["font"], "N/A")
        self.assertEqual(result["radii"], "N/A")
        self.assertIn("structured output unavailable", result["notes"])


class ApplyElementTimeoutTests(unittest.TestCase):
    def test_timeout_returns_structured_failure(self):
        with patch("workflow.nodes.implement.apply.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd=[], timeout=60)):
            result = apply_element("gtk_theme", {}, "/tmp")

        self.assertFalse(result["success"])
        self.assertIn("timed out", result["error"])


if __name__ == "__main__":
    unittest.main()
