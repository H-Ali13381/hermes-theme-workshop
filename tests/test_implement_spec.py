"""Tests for implementation spec structured output and apply element."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow.nodes.implement.apply import apply_element
from workflow.nodes.implement.score import score_element
from workflow.nodes.implement.spec import ElementSpec, write_spec
from workflow.nodes.implement.verify import verify_element


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

    def test_write_spec_falls_back_to_json_text_when_structured_output_unavailable(self):
        class TextOnlyLLM:
            def invoke(self, messages):
                self.messages = messages
                return type("Msg", (), {"content": '''```json
{
  "targets": ["~/.config/kitty/kitty.conf", "~/.config/kitty/theme.conf"],
  "palette_keys": ["background", "foreground", "primary"],
  "font": "JetBrains Mono 12",
  "radii": "6px",
  "notes": "Include the generated theme file from kitty.conf; restart kitty windows."
}
```'''})()

        llm = TextOnlyLLM()
        with patch("workflow.nodes.implement.spec.get_llm", return_value=llm):
            result = write_spec("terminal:kitty", {"name": "test"})

        self.assertEqual(result["targets"], ["~/.config/kitty/kitty.conf", "~/.config/kitty/theme.conf"])
        self.assertEqual(result["palette_keys"], ["background", "foreground", "primary"])
        self.assertEqual(result["font"], "JetBrains Mono 12")
        self.assertEqual(result["radii"], "6px")
        self.assertIn("restart kitty", result["notes"])
        self.assertIn("Return ONLY JSON", llm.messages[0].content)

    def test_write_spec_returns_safe_fallback_when_both_structured_and_text_fail(self):
        class FailingLLM:
            def with_structured_output(self, schema):
                raise RuntimeError("structured output unavailable")

            def invoke(self, messages):
                raise RuntimeError("text invoke unavailable")

        with patch("workflow.nodes.implement.spec.get_llm", return_value=FailingLLM()):
            result = write_spec("terminal:kitty", {"name": "test"})

        self.assertEqual(result["targets"], [])
        self.assertEqual(result["palette_keys"], [])
        self.assertEqual(result["font"], "N/A")
        self.assertEqual(result["radii"], "N/A")
        self.assertIn("structured output unavailable", result["notes"])
        self.assertIn("text invoke unavailable", result["notes"])

    def test_lock_screen_kde_prompt_matches_materializer_limitations(self):
        from workflow.nodes.implement.spec import _messages

        messages = _messages("lock_screen:kde", {"name": "bonfire-blackiron", "palette": {}}, structured=False)
        system = messages[0].content

        self.assertIn('For element "lock_screen:kde"', system)
        self.assertIn("~/.config/kscreenlockerrc", system)
        self.assertIn("does NOT generate a custom Plasma look-and-feel package", system)
        self.assertIn("palette_keys must be []", system)


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


class VerifyElementTests(unittest.TestCase):
    def test_palette_match_is_across_written_file_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            first = home / ".config" / "example" / "one.conf"
            second = home / ".config" / "example" / "two.conf"
            first.parent.mkdir(parents=True)
            first.write_text("background #111513\nforeground #d6c8aa\n", encoding="utf-8")
            second.write_text("accent #f0a33a\nprimary #d06f22\n", encoding="utf-8")
            spec = {"targets": [str(first), str(second)], "palette_keys": ["background", "foreground", "accent", "primary"]}
            design = {"palette": {"background": "#111513", "foreground": "#d6c8aa", "accent": "#f0a33a", "primary": "#d06f22"}}

            verify = verify_element("example", spec, design)
            score = score_element("example", spec, design, verify)

            self.assertTrue(verify["palette_match"])
            self.assertGreaterEqual(score["total"], 8)

    def test_palette_match_accepts_kde_rgb_triplets(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            colors = home / ".local" / "share" / "color-schemes" / "hermes-bonfire.colors"
            colors.parent.mkdir(parents=True)
            colors.write_text("BackgroundNormal=17,21,19\nForegroundNormal=214,200,170\nDecorationFocus=208,111,34\n", encoding="utf-8")
            spec = {"targets": [str(colors)], "palette_keys": ["background", "foreground", "primary"]}
            design = {"name": "bonfire", "palette": {"background": "#111513", "foreground": "#d6c8aa", "primary": "#d06f22"}}

            with patch("workflow.nodes.implement.verify.Path.home", return_value=home), \
                 patch("workflow.nodes.implement.verify.subprocess.run", side_effect=FileNotFoundError):
                verify = verify_element("window_decorations:kde", spec, design)
                score = score_element("window_decorations:kde", spec, design, verify)

            self.assertTrue(verify["palette_match"])
            self.assertGreaterEqual(score["total"], 8)

    def test_unresolved_missing_targets_keep_score_below_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            actual = home / ".config" / "example" / "actual.conf"
            missing = home / ".config" / "example" / "missing.conf"
            actual.parent.mkdir(parents=True)
            actual.write_text("background #111513\nforeground #d6c8aa\n", encoding="utf-8")
            spec = {"targets": [str(actual), str(missing)], "palette_keys": ["background", "foreground"]}
            design = {"palette": {"background": "#111513", "foreground": "#d6c8aa"}}

            verify = verify_element("example", spec, design)
            score = score_element("example", spec, design, verify)

            self.assertEqual(verify["files_missing"], [str(missing)])
            self.assertLess(score["total"], 8)

    def test_directory_targets_do_not_break_palette_or_syntax_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            theme_dir = home / ".local" / "share" / "plasma" / "desktoptheme" / "BonfireBlackiron"
            colors = theme_dir / "colors"
            widgets = theme_dir / "widgets"
            widgets.mkdir(parents=True)
            colors.write_text("#111513 #d6c8aa #d06f22 #f0a33a\n", encoding="utf-8")
            spec = {"targets": [str(theme_dir), str(colors), str(widgets)], "palette_keys": ["background", "foreground", "primary", "accent"]}
            design = {"palette": {"background": "#111513", "foreground": "#d6c8aa", "primary": "#d06f22", "accent": "#f0a33a"}}

            verify = verify_element("plasma_theme", spec, design)
            score = score_element("plasma_theme", spec, design, verify)

            self.assertTrue(verify["palette_match"])
            self.assertGreaterEqual(score["total"], 8)

    def test_kitty_theme_conf_resolves_stale_theme_named_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            actual = home / ".config" / "kitty" / "theme.conf"
            actual.parent.mkdir(parents=True)
            actual.write_text("background #111513\nforeground #d6c8aa\ncolor1 #d06f22\n", encoding="utf-8")
            stale = home / ".config" / "kitty" / "bonfire-blackiron.conf"
            spec = {"targets": [str(stale)], "palette_keys": ["background", "foreground", "primary"]}
            design = {"palette": {"background": "#111513", "foreground": "#d6c8aa", "primary": "#d06f22"}}

            with patch("workflow.nodes.implement.verify.Path.home", return_value=home):
                verify = verify_element("terminal:kitty", spec, design)
                score = score_element("terminal:kitty", spec, design, verify)

            self.assertEqual(verify["files_missing"], [])
            self.assertIn(str(actual), verify["files_written"])
            self.assertGreaterEqual(score["total"], 8)

    def test_rofi_hermes_theme_resolves_stale_theme_named_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            actual = home / ".config" / "rofi" / "hermes-theme.rasi"
            actual.parent.mkdir(parents=True)
            actual.write_text("* { background: #111513; foreground: #d6c8aa; accent: #f0a33a; }", encoding="utf-8")
            stale = home / ".config" / "rofi" / "themes" / "bonfire-blackiron.rasi"
            spec = {"targets": [str(stale)], "palette_keys": ["background", "foreground", "accent"]}
            design = {"palette": {"background": "#111513", "foreground": "#d6c8aa", "accent": "#f0a33a"}}

            with patch("workflow.nodes.implement.verify.Path.home", return_value=home):
                verify = verify_element("launcher:rofi", spec, design)
                score = score_element("launcher:rofi", spec, design, verify)

            self.assertEqual(verify["files_missing"], [])
            self.assertIn(str(actual), verify["files_written"])
            self.assertGreaterEqual(score["total"], 8)

    def test_icon_theme_generated_name_resolves_stale_design_theme_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            actual = home / ".local" / "share" / "icons" / "bonfire-blackiron-icons" / "index.theme"
            glyph = home / ".local" / "share" / "icons" / "bonfire-blackiron-icons" / "actions" / "22" / "system-run.svg"
            glyph.parent.mkdir(parents=True)
            actual.write_text("[Icon Theme]\nName=bonfire-blackiron-icons\n", encoding="utf-8")
            glyph.write_text("<svg><path fill='#d6c8aa'/><path fill='#f0a33a'/></svg>", encoding="utf-8")
            stale = home / ".local" / "share" / "icons" / "bonfire-blackiron" / "index.theme"
            spec = {"targets": [str(stale)], "palette_keys": ["foreground", "accent"]}
            design = {"name": "bonfire-blackiron", "icon_theme": "bonfire-blackiron", "palette": {"foreground": "#d6c8aa", "accent": "#f0a33a"}}

            with patch("workflow.nodes.implement.verify.Path.home", return_value=home):
                verify = verify_element("icon_theme", spec, design)
                score = score_element("icon_theme", spec, design, verify)

            self.assertEqual(verify["files_missing"], [])
            self.assertIn(str(actual), verify["files_written"])
            self.assertGreaterEqual(score["total"], 8)

    def test_kde_colorscheme_uses_hermes_filename_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            actual = Path(tmp) / ".local" / "share" / "color-schemes" / "hermes-mossgrown-throne.colors"
            actual.parent.mkdir(parents=True)
            actual.write_text("[General]\nName=hermes-mossgrown-throne\nColor=26,27,38\n", encoding="utf-8")
            stale = Path(tmp) / ".local" / "share" / "color-schemes" / "MossgrownThrone.colors"
            spec = {"targets": [str(stale)], "palette_keys": ["background"]}
            design = {"name": "mossgrown-throne", "palette": {"background": "#1a1b26"}}

            with patch.dict(os.environ, {"HOME": tmp}), \
                 patch("workflow.nodes.implement.verify.subprocess.run", side_effect=FileNotFoundError):
                verify = verify_element("window_decorations:kde", spec, design)
                score = score_element("window_decorations:kde", spec, design, verify)

            self.assertEqual(verify["files_missing"], [])
            self.assertIn(str(actual), verify["files_written"])
            self.assertIn("resolved_missing_targets", verify)
            self.assertGreaterEqual(score["total"], 8)

    def test_kde_colorscheme_active_mismatch_scores_below_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            actual = home / ".local" / "share" / "color-schemes" / "hermes-moss.colors"
            actual.parent.mkdir(parents=True)
            actual.write_text("[General]\nName=hermes-moss\nColor=26,27,38\n", encoding="utf-8")
            kdeglobals = home / ".config" / "kdeglobals"
            kdeglobals.parent.mkdir(parents=True)
            kdeglobals.write_text("[General]\nColorScheme=BreezeClassic\n", encoding="utf-8")
            spec = {"targets": [str(actual)], "palette_keys": ["background"]}
            design = {"name": "moss", "palette": {"background": "#1a1b26"}}

            with patch.dict(os.environ, {"HOME": tmp}), \
                 patch("workflow.nodes.implement.verify.subprocess.run", side_effect=FileNotFoundError):
                verify = verify_element("window_decorations:kde", spec, design)
                score = score_element("window_decorations:kde", spec, design, verify)

            self.assertEqual(verify["active_colorscheme"], "BreezeClassic")
            self.assertFalse(verify["active_match"])
            self.assertLess(score["total"], 8)
    def test_fastfetch_uses_default_config_fallback_when_spec_names_theme_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            actual = home / ".config" / "fastfetch" / "config.jsonc"
            actual.parent.mkdir(parents=True)
            actual.write_text(
                '{"display":{"color":{"title":"#f06a1a","keys":"#ff9a32","separator":"#cc8833"}},'
                '"modules":[{"keyColor":"#62d3d6"},{"keyColor":"#3a7a3a"},{"keyColor":"#cc3333"}]}',
                encoding="utf-8",
            )
            stale = home / ".config" / "fastfetch" / "emberward-reliquary.jsonc"
            spec = {
                "targets": [str(stale)],
                "palette_keys": ["primary", "secondary", "accent", "danger", "success", "warning"],
            }
            design = {
                "name": "emberward-reliquary",
                "palette": {
                    "primary": "#f06a1a",
                    "secondary": "#62d3d6",
                    "accent": "#ff9a32",
                    "danger": "#cc3333",
                    "success": "#3a7a3a",
                    "warning": "#cc8833",
                },
            }

            with patch("workflow.nodes.implement.verify.Path.home", return_value=home):
                verify = verify_element("fastfetch", spec, design)
                score = score_element("fastfetch", spec, design, verify)

            self.assertIn(str(actual), verify["files_written"])
            self.assertGreaterEqual(score["total"], 8)


if __name__ == "__main__":
    unittest.main()
