"""Tests for implementation spec structured output and apply element."""
from __future__ import annotations

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
    def setUp(self):
        _FakeLLM.requested_schema = None
        _FakeLLM.structured_response = None

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


class ApplyElementTests(unittest.TestCase):
    """apply_element delegates to materialize() directly — no subprocess involved."""

    _FAKE_APPS   = {"gtk": "/usr/bin/gtk-query-settings"}
    _FAKE_MANIFEST = {"timestamp": "20260101_000000", "changes": []}

    def _patch_ricer(self, *, manifest=None, raises=None):
        """Return a context manager that patches discover_apps + materialize."""
        fake_apps     = self._FAKE_APPS
        fake_manifest = manifest if manifest is not None else self._FAKE_MANIFEST

        def _materialize(design, apps=None, wallpaper=None, dry_run=False):
            if raises:
                raise raises
            return fake_manifest

        return (
            patch("workflow.nodes.implement.apply.discover_apps", return_value=fake_apps),
            patch("workflow.nodes.implement.apply.materialize", side_effect=_materialize),
        )

    def test_success_returns_manifest(self):
        patches = self._patch_ricer()
        with patches[0], patches[1]:
            result = apply_element("gtk_theme", {"name": "test"}, "/tmp")

        self.assertTrue(result["success"])
        self.assertEqual(result["manifest"], self._FAKE_MANIFEST)

    def test_materializer_exception_returns_structured_failure(self):
        patches = self._patch_ricer(raises=RuntimeError("disk full"))
        with patches[0], patches[1]:
            result = apply_element("gtk_theme", {"name": "test"}, "/tmp")

        self.assertFalse(result["success"])
        self.assertIn("disk full", result["error"])

    def test_unsupported_element_returns_failure(self):
        patches = self._patch_ricer()
        with patches[0], patches[1]:
            result = apply_element("unknown_widget", {}, "/tmp")

        self.assertFalse(result["success"])
        self.assertIn("unsupported element", result["error"])

    def test_materializer_not_detected_returns_failure(self):
        # discover_apps returns nothing — materializer absent on this system.
        with patch("workflow.nodes.implement.apply.discover_apps", return_value={}), \
             patch("workflow.nodes.implement.apply.materialize") as mock_mat:
            result = apply_element("gtk_theme", {}, "/tmp")

        mock_mat.assert_not_called()
        self.assertFalse(result["success"])
        self.assertIn("not detected", result["error"])


if __name__ == "__main__":
    unittest.main()
