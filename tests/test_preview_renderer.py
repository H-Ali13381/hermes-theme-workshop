"""Tests for deterministic SVG preview rendering."""
from __future__ import annotations

import re
import unittest

from workflow.nodes.preview_renderer import render_preview_html, _radius_scale


def _design(**overrides):
    data = {
        "name": "ember-tome",
        "description": "A final inn bonfire UI rebuilt as bronze RPG chrome.",
        "palette": {
            "background": "#141210", "foreground": "#dcc6a8", "primary": "#c97b45",
            "secondary": "#8a7d6e", "accent": "#e89f58", "surface": "#1c1814",
            "muted": "#5e5248", "danger": "#b84a4a", "success": "#7d8c6e", "warning": "#c9a03e",
        },
        "originality_strategy": {
            "non_default_moves": [
                "tome-spine dock with bronze bands",
                "ornamental terminal frame",
                "ember-lit launcher menu rows",
            ]
        },
        "chrome_strategy": {"method": "eww_frame + kvantum", "implementation_targets": ["widgets:eww"]},
        "widget_layout": [{"name": "ember-gauge", "visual_concept": "bonfire warmth meter"}],
        "mood_tags": ["ember", "bronze", "rested"],
    }
    data.update(overrides)
    return data


def _all_rx_values(html: str) -> list[int]:
    """Return all rx=N values found in the rendered SVG."""
    return [int(v) for v in re.findall(r"rx='(\d+)'", html)]


class PreviewRendererTests(unittest.TestCase):
    def test_renderer_returns_non_empty_html_with_embedded_svg(self):
        rendered = render_preview_html(_design())

        self.assertGreater(len(rendered), 500)
        self.assertTrue(rendered.startswith("<!DOCTYPE html>"))
        self.assertIn('data-preview-engine="svg-v2"', rendered)
        self.assertIn("<svg", rendered)
        self.assertIn("data-frame-style=", rendered)

    def test_renderer_uses_palette_and_theme_content(self):
        rendered = render_preview_html(_design())

        self.assertIn("#e89f58", rendered)
        self.assertIn("Ember Tome", rendered)
        self.assertIn("tome-spine dock", rendered)
        self.assertTrue("ember-gauge" in rendered or "Ember Gauge" in rendered)

    def test_renderer_infers_tome_codex_style_for_tome_briefs(self):
        rendered = render_preview_html(_design())

        self.assertIn('data-preview-style="tome_codex"', rendered)
        self.assertIn("EMBER CODEX", rendered)

    def test_renderer_embeds_feedback_without_llm_prompting(self):
        rendered = render_preview_html(_design(), "make the borders more ornate")

        self.assertIn("Revision notes shaping this render", rendered)
        self.assertIn("make the borders more ornate", rendered)

    def test_renderer_output_is_valid_html(self):
        rendered = render_preview_html(_design())
        lower = rendered.lower()
        self.assertIn("<html", lower)
        self.assertIn("<body", lower)

    # --- CSS variable / card-radius tests ----------------------------------

    def test_palette_exposed_as_css_variables(self):
        rendered = render_preview_html(_design())
        # All palette slots must appear as --slot: #hex in :root
        for slot in ("background", "foreground", "primary", "accent", "surface",
                     "muted", "danger", "success", "warning", "secondary"):
            self.assertIn(f"--{slot}:", rendered)

    def test_rounded_corners_on_by_default(self):
        rendered = render_preview_html(_design())
        self.assertIn('data-rounded="true"', rendered)
        # At least one non-zero rx in the SVG
        rx_vals = _all_rx_values(rendered)
        self.assertTrue(any(v > 0 for v in rx_vals), f"Expected some rx > 0, got {rx_vals}")

    # --- chrome_strategy.rounded_corners=false tests -----------------------

    def test_sharp_geometry_when_rounded_corners_false(self):
        design = _design(chrome_strategy={
            "method": "kvantum",
            "rounded_corners": False,
            "implementation_targets": [],
        })
        rendered = render_preview_html(design)
        self.assertIn('data-rounded="false"', rendered)
        rx_vals = _all_rx_values(rendered)
        self.assertTrue(all(v == 0 for v in rx_vals), f"Expected all rx=0 for sharp design, got {rx_vals}")

    def test_sharp_geometry_when_rounded_corners_false_string(self):
        design = _design(chrome_strategy={"method": "kvantum", "rounded_corners": "false"})
        rendered = render_preview_html(design)
        self.assertIn('data-rounded="false"', rendered)
        rx_vals = _all_rx_values(rendered)
        self.assertTrue(all(v == 0 for v in rx_vals))

    def test_sharp_geometry_when_rounded_corners_dict_disabled(self):
        design = _design(chrome_strategy={"method": "kvantum", "rounded_corners": {"enabled": False}})
        rendered = render_preview_html(design)
        self.assertIn('data-rounded="false"', rendered)

    def test_explicit_radius_hint_used(self):
        design = _design(chrome_strategy={
            "method": "kvantum",
            "rounded_corners": {"enabled": True, "radius_px": 16},
            "implementation_targets": [],
        })
        r = _radius_scale(design)
        self.assertTrue(r["enabled"])
        self.assertEqual(r["frame"], 16)

    # --- _radius_scale unit tests ------------------------------------------

    def test_radius_scale_default_when_no_chrome_strategy(self):
        r = _radius_scale({})
        self.assertTrue(r["enabled"])
        self.assertGreater(r["frame"], 0)

    def test_radius_scale_off_for_false(self):
        r = _radius_scale({"chrome_strategy": {"rounded_corners": False}})
        self.assertFalse(r["enabled"])
        self.assertEqual(r["frame"], 0)
        self.assertEqual(r["panel"], 0)
        self.assertEqual(r["row"], 0)
        self.assertEqual(r["widget"], 0)

    def test_radius_scale_off_for_string_false(self):
        for val in ("false", "none", "no", "off", "disabled"):
            with self.subTest(val=val):
                r = _radius_scale({"chrome_strategy": {"rounded_corners": val}})
                self.assertFalse(r["enabled"], msg=f"Expected disabled for {val!r}")


if __name__ == "__main__":
    unittest.main()