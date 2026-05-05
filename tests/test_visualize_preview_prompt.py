"""Regression tests for Step 2.5 AI desktop preview prompting."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from workflow.nodes.visualize import (
    ANALYSIS_SYSTEM_PROMPT,
    PREVIEW_SYSTEM_PROMPT,
    _select_overview_aspect_ratio,
    _build_desktop_preview_prompt,
    _load_pending_preview,
    _pending_preview_path,
    _save_pending_preview,
)


class VisualizeDesktopPreviewPromptTests(unittest.TestCase):
    def test_fal_prompt_targets_full_desktop_ui_not_environment_only(self):
        prompt = _build_desktop_preview_prompt({
            "stance": "Garden+Blade+Ghost",
            "mood": ["emberlit", "gothic", "relicbound"],
            "reference_anchor": "Diablo II campfire meets Burning Crusade war shrine",
            "name_hypothesis": "cindershrine-reliquary",
        }).lower()

        for required in (
            "full linux desktop theme concept preview",
            "entire desktop ui",
            "screenshot-style mockup",
            "ornate window borders",
            "themed terminal window",
            "launcher/menu panel",
            "widget menus",
            "icon style",
            "custom application chrome",
            "thorn-like ornamental borders",
            "representative overview image",
            "edge-to-edge",
            "no cinematic letterbox bars",
            "no black bands above or below",
            "desktop overview",
            "readable ui labels where useful",
            "terminal/menu/panel text affordances",
            "original glyph marks and icon emblems",
            "no copied proprietary logos or trademarks",
        ):
            self.assertIn(required, prompt)

        for forbidden in (
            "no ui chrome",
            "clean professional concept art",
            "stock kde defaults",
            "style guide",
            "generic card layout",
            "no readable text",
            "no logos",
        ):
            self.assertNotIn(forbidden, prompt)
        self.assertIn("not a landscape-only painting", prompt)

    def test_reference_images_are_design_language_not_wallpaper(self):
        prompt = _build_desktop_preview_prompt({
            "reference_anchor": "Diablo II inventory frame, Dark Souls bonfire menu, Classic WoW parchment quest log",
            "name_hypothesis": "emberward-reliquary",
        }).lower()

        self.assertIn("concrete fantasy rpg game-menu references", prompt)
        self.assertIn("reference images as design-language inputs", prompt)
        self.assertIn("not as wallpaper candidates", prompt)
        self.assertIn("do not turn reference art into the wallpaper", prompt)

    def test_fal_generation_uses_nano_banana_with_loose_safety_not_flux(self):
        import os
        from unittest.mock import patch
        from workflow.nodes import visualize as visualize_mod

        captured = {}

        def fake_subscribe(model_id, arguments, with_logs=False):
            captured["model_id"] = model_id
            captured["arguments"] = arguments
            captured["with_logs"] = with_logs
            return {"images": [{"url": "https://example.test/hero.png"}]}

        with patch.dict(os.environ, {}, clear=False), patch.object(visualize_mod.fal_client, "subscribe", side_effect=fake_subscribe):
            url = visualize_mod._generate_style_image({}, "test-key", log=type("L", (), {"info": lambda *a, **k: None, "warning": lambda *a, **k: None})())

        self.assertEqual(url, "https://example.test/hero.png")
        self.assertEqual(captured["model_id"], "fal-ai/nano-banana")
        self.assertEqual(captured["arguments"]["aspect_ratio"], "16:9")
        self.assertEqual(captured["arguments"]["safety_tolerance"], "6")
        self.assertNotIn("guidance_scale", captured["arguments"])
        self.assertNotIn("num_inference_steps", captured["arguments"])

    def test_aspect_ratio_uses_multi_monitor_virtual_bounds(self):
        profile = {"screen_geometries": [
            {"name": "DP-1", "x": 0, "y": 0, "width": 2560, "height": 1440},
            {"name": "HDMI-A-1", "x": 2560, "y": 900, "width": 1536, "height": 864},
        ]}
        self.assertEqual(_select_overview_aspect_ratio(profile), "21:9")

    def test_aspect_ratio_stays_16_9_for_single_monitor(self):
        profile = {"screen_geometries": [{"x": 0, "y": 0, "width": 2560, "height": 1440}]}
        self.assertEqual(_select_overview_aspect_ratio(profile), "16:9")

    def test_prompt_names_target_canvas(self):
        prompt = _build_desktop_preview_prompt({}, aspect_ratio="21:9").lower()
        self.assertIn("target canvas", prompt)
        self.assertIn("multi-monitor", prompt)
        self.assertIn("21:9", prompt)

    def test_multimodal_analysis_requires_element_decomposition_and_tool_plan(self):
        prompt = ANALYSIS_SYSTEM_PROMPT.lower()

        for required in (
            "visual_element_plan",
            "implementation_tool",
            "fallback_tool",
            "validation_probe",
            "validation_checklist",
            "break the generated image into concrete",
            "prefer quickshell for kde/wayland",
        ):
            self.assertIn(required, prompt)

    def test_html_preview_prompt_describes_ai_desktop_image(self):
        prompt = PREVIEW_SYSTEM_PROMPT.lower()

        self.assertIn("ai desktop theme preview", prompt)
        self.assertIn("full-desktop theme concept image", prompt)
        self.assertIn("window borders", prompt)
        self.assertIn("launcher", prompt)
        self.assertIn("panel/widgets", prompt)
        self.assertNotIn("mini ui mockup", prompt)

    def test_pending_preview_cache_preserves_approval_target_across_reentry(self):
        with tempfile.TemporaryDirectory() as td:
            html_path = Path(td) / "visualize.html"
            visual_context = {
                "reference_image_url": "https://example.test/original.png",
                "style_description": "embered menu chrome",
            }

            _save_pending_preview(td, "https://example.test/original.png", html_path, visual_context)
            cached = _load_pending_preview(td)

        self.assertEqual(cached["image_url"], "https://example.test/original.png")
        self.assertEqual(cached["html_path"], str(html_path))
        self.assertEqual(cached["visual_context"], visual_context)

    def test_pending_preview_cache_ignores_malformed_files(self):
        with tempfile.TemporaryDirectory() as td:
            _pending_preview_path(td).write_text("not json", encoding="utf-8")
            cached = _load_pending_preview(td)

        self.assertEqual(cached, {})


if __name__ == "__main__":
    unittest.main()
