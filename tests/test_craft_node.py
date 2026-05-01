"""tests/test_craft_node.py — Unit tests for the craft_node pipeline."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── path bootstrap ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from workflow.nodes.craft.frameworks import (
    CRAFT_PROVIDERS, is_craft_element, framework_for, get_reference, config_dir,
)
from workflow.nodes.craft.research import _scan_system, _read_syntax, _summarize_design
from workflow.nodes.craft.codegen import _parse_file_objects
from workflow.validators import is_craft_element as validators_is_craft


# ── frameworks.py ─────────────────────────────────────────────────────────────

class TestIsCraftElement(unittest.TestCase):
    def test_widgets_eww_is_craft(self):
        self.assertTrue(is_craft_element("widgets:eww"))

    def test_widgets_ags_is_craft(self):
        self.assertTrue(is_craft_element("widgets:ags"))

    def test_widgets_quickshell_is_craft(self):
        self.assertTrue(is_craft_element("widgets:quickshell"))

    def test_widgets_conky_is_craft(self):
        self.assertTrue(is_craft_element("widgets:conky"))

    def test_bar_waybar_is_craft(self):
        self.assertTrue(is_craft_element("bar:waybar"))

    def test_terminal_kitty_not_craft(self):
        self.assertFalse(is_craft_element("terminal:kitty"))

    def test_gtk_theme_not_craft(self):
        self.assertFalse(is_craft_element("gtk_theme"))

    def test_window_decorations_kde_not_craft(self):
        self.assertFalse(is_craft_element("window_decorations:kde"))

    def test_no_colon_not_craft(self):
        self.assertFalse(is_craft_element("eww"))

    def test_validators_proxy_matches(self):
        """validators.is_craft_element should delegate to frameworks.is_craft_element."""
        self.assertTrue(validators_is_craft("widgets:eww"))
        self.assertFalse(validators_is_craft("terminal:kitty"))


class TestFrameworkFor(unittest.TestCase):
    def test_eww(self):
        self.assertEqual(framework_for("widgets:eww"), "eww")

    def test_no_colon(self):
        self.assertIsNone(framework_for("eww"))


class TestGetReference(unittest.TestCase):
    def test_eww_has_syntax(self):
        ref = get_reference("eww")
        self.assertIn("defwidget", ref["syntax_hint"])
        self.assertIn("defwindow", ref["example"])

    def test_unknown_returns_stub(self):
        ref = get_reference("unknown_fw")
        self.assertEqual(ref["syntax_hint"], "")
        self.assertEqual(ref["key_files"], [])


class TestConfigDir(unittest.TestCase):
    def test_eww_returns_path(self):
        p = config_dir("eww")
        self.assertIsNotNone(p)
        self.assertIn("eww", str(p))

    def test_unknown_returns_none(self):
        self.assertIsNone(config_dir("unknown_fw"))


# ── research.py ───────────────────────────────────────────────────────────────

class TestScanSystem(unittest.TestCase):
    def test_missing_dir_returns_note(self):
        result = _scan_system("nonexistent_framework_xyz")
        self.assertIn("existing_files", result)
        self.assertEqual(result["existing_files"], {})

    def test_scans_real_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Patch config_dir to return tmp
            with patch("workflow.nodes.craft.research.config_dir", return_value=Path(tmp)):
                (Path(tmp) / "test.yuck").write_text("(defwidget test [])")
                result = _scan_system("eww")
        self.assertIn("test.yuck", result["existing_files"])


class TestReadSyntax(unittest.TestCase):
    def test_eww_syntax(self):
        result = _read_syntax("eww")
        self.assertIn("defwidget", result["syntax_hint"])
        self.assertNotEqual(result["example"], "")

    def test_unknown_framework(self):
        result = _read_syntax("mystery")
        self.assertEqual(result["syntax_hint"], "")


class TestSummarizeDesign(unittest.TestCase):
    _DESIGN = {
        "name": "cosmic-void",
        "description": "Dark space theme",
        "mood_tags": ["dark", "minimal"],
        "palette": {"base": "#1e1e2e", "accent": "#89b4fa"},
        "originality_strategy": {"vision_alignment": "space", "non_default_moves": ["a", "b", "c"]},
    }

    def test_extracts_palette(self):
        result = _summarize_design("widgets:eww", self._DESIGN)
        self.assertEqual(result["palette"]["base"], "#1e1e2e")

    def test_extracts_originality(self):
        result = _summarize_design("widgets:eww", self._DESIGN)
        self.assertIn("originality_strategy", result)

    def test_element_preserved(self):
        result = _summarize_design("widgets:eww", self._DESIGN)
        self.assertEqual(result["element"], "widgets:eww")


# ── codegen.py ────────────────────────────────────────────────────────────────

class TestParseFileObjects(unittest.TestCase):
    def test_valid_json_array(self):
        raw = '[{"path": "eww.yuck", "content": "(defwidget bar [])"}]'
        result = _parse_file_objects(raw)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "eww.yuck")

    def test_json_embedded_in_prose(self):
        raw = 'Here are the files:\n[{"path": "a.yuck", "content": "x"}, {"path": "b.scss", "content": "y"}]'
        result = _parse_file_objects(raw)
        self.assertEqual(len(result), 2)

    def test_missing_path_filtered(self):
        raw = '[{"content": "orphan"}, {"path": "ok.yuck", "content": "good"}]'
        result = _parse_file_objects(raw)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "ok.yuck")

    def test_invalid_json_returns_empty(self):
        result = _parse_file_objects("this is not json")
        self.assertEqual(result, [])


# ── craft_node integration ─────────────────────────────────────────────────────

class TestCraftNodeWriteAndScore(unittest.TestCase):
    """Test the write + score path without calling the real LLM."""

    _DESIGN = {
        "name": "test-theme",
        "palette": {"base": "#1e1e2e", "accent": "#89b4fa"},
        "mood_tags": ["dark"],
    }

    def _run_craft(self, files, session_dir):
        from workflow.nodes.craft import craft_node
        state = {
            "element_queue": ["widgets:eww"],
            "design": self._DESIGN,
            "session_dir": session_dir,
            "impl_retry_counts": {},
        }
        with patch("workflow.nodes.craft.gather_research", return_value={}), \
             patch("workflow.nodes.craft.generate_files", return_value=files):
            return craft_node(state)

    def test_writes_files_and_pops_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = [{"path": "eww.yuck", "content": "(defwidget bar [] (label :text \"#1e1e2e\"))"}]
            # interrupt is called when score < threshold; mock it to return "accept"
            with patch("workflow.nodes.craft.config_dir", return_value=Path(tmp)), \
                 patch("workflow.nodes.craft.get_reference", return_value={"config_dir": tmp, "key_files": []}), \
                 patch("workflow.nodes.craft.interrupt", return_value="accept"):
                result = self._run_craft(files, "")
        self.assertIn("craft_log", result)
        self.assertEqual(result["element_queue"], [])

    def test_empty_files_skips_element(self):
        result = self._run_craft([], "")
        log = result.get("craft_log", [])
        self.assertTrue(any("SKIP" in str(r.get("verdict", "")) for r in log))


# ── routing ───────────────────────────────────────────────────────────────────

class TestCraftRouting(unittest.TestCase):
    def test_after_implement_routes_to_craft(self):
        from workflow.routing import after_implement
        state = {"element_queue": ["widgets:eww"]}
        self.assertEqual(after_implement(state), "craft")

    def test_after_implement_routes_to_implement(self):
        from workflow.routing import after_implement
        state = {"element_queue": ["terminal:kitty"]}
        self.assertEqual(after_implement(state), "implement")

    def test_after_implement_routes_to_cleanup_when_done(self):
        from workflow.routing import after_implement
        state = {"element_queue": []}
        self.assertEqual(after_implement(state), "cleanup")

    def test_after_craft_routes_to_cleanup_when_done(self):
        from workflow.routing import after_craft
        state = {"element_queue": []}
        self.assertEqual(after_craft(state), "cleanup")

    def test_after_craft_routes_to_implement_for_normal_element(self):
        from workflow.routing import after_craft
        state = {"element_queue": ["gtk_theme"]}
        self.assertEqual(after_craft(state), "implement")

    def test_after_craft_routes_to_craft_for_craft_element(self):
        from workflow.routing import after_craft
        state = {"element_queue": ["widgets:conky"]}
        self.assertEqual(after_craft(state), "craft")


if __name__ == "__main__":
    unittest.main()
