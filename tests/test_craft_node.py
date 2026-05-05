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
    _load_reference_templates, _load_reference_docs,
)
from workflow.nodes.craft.research import _scan_system, _read_syntax, _summarize_design
from workflow.nodes.craft.codegen import (
    _parse_file_objects, _format_reference_templates, _format_reference_docs, _build_prompt, evaluate_files, generate_files,
)
from workflow.nodes.craft import _score
from workflow.validators import is_craft_element as validators_is_craft


# ── frameworks.py ─────────────────────────────────────────────────────────────

class TestIsCraftElement(unittest.TestCase):
    def test_widgets_eww_is_craft(self):
        self.assertTrue(is_craft_element("widgets:eww"))

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
        self.assertEqual(ref["reference_templates"], [])

    def test_eww_includes_reference_templates(self):
        ref = get_reference("eww")
        names = [t["name"] for t in ref.get("reference_templates", [])]
        self.assertIn("eww/_reference/bar.yuck", names)
        self.assertIn("eww/_reference/bar.scss", names)
        for tmpl in ref["reference_templates"]:
            self.assertTrue(tmpl["content"].strip(), f"empty content for {tmpl['name']}")
            self.assertTrue(tmpl["language"], f"missing language for {tmpl['name']}")

    def test_quickshell_includes_reference_templates(self):
        ref = get_reference("quickshell")
        names = [t["name"] for t in ref.get("reference_templates", [])]
        self.assertIn("quickshell/bar.qml", names)
        self.assertIn("quickshell/floating-widget.qml", names)
        for tmpl in ref["reference_templates"]:
            self.assertEqual(tmpl["language"], "qml")
            self.assertIn("PanelWindow", tmpl["content"])

    def test_quickshell_includes_v030_type_docs_source_of_truth(self):
        ref = get_reference("quickshell")
        docs = {doc["name"]: doc for doc in ref.get("reference_docs", [])}
        self.assertIn("quickshell-v0.3.0-types/index.json", docs)
        self.assertIn("quickshell-v0.3.0-types/summary.md", docs)
        index = docs["quickshell-v0.3.0-types/index.json"]["content"]
        self.assertEqual(index["version"], "v0.3.0")
        self.assertGreaterEqual(index["type_count"], 140)
        rels = {f"{entry['module']}/{entry['name']}" for entry in index["types"]}
        self.assertIn("Quickshell/PanelWindow", rels)
        self.assertIn("Quickshell.Io/Process", rels)
        panel = next(entry for entry in index["types"] if entry["module"] == "Quickshell" and entry["name"] == "PanelWindow")
        self.assertIn("exclusionMode", {prop["name"] for prop in panel["properties"]})
        self.assertIn("PanelWindow", docs["quickshell-v0.3.0-types/summary.md"]["content"])

    def test_conky_no_reference_templates(self):
        ref = get_reference("conky")
        self.assertEqual(ref.get("reference_templates", []), [])


class TestLoadReferenceTemplates(unittest.TestCase):
    def test_missing_file_skipped(self):
        result = _load_reference_templates(["does/not/exist.txt"])
        self.assertEqual(result, [])

    def test_loads_real_quickshell_bar(self):
        result = _load_reference_templates(["quickshell/bar.qml"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["language"], "qml")
        self.assertIn("PanelWindow", result[0]["content"])

    def test_mixed_existing_and_missing(self):
        result = _load_reference_templates(["quickshell/bar.qml", "does/not/exist.qml"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "quickshell/bar.qml")


class TestLoadReferenceDocs(unittest.TestCase):
    def test_missing_doc_skipped(self):
        result = _load_reference_docs(["does/not/exist.json"])
        self.assertEqual(result, [])

    def test_loads_quickshell_type_index(self):
        result = _load_reference_docs(["quickshell-v0.3.0-types/index.json"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["language"], "json")
        self.assertEqual(result[0]["content"]["version"], "v0.3.0")


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
        self.assertEqual(result["reference_templates"], [])
        self.assertEqual(result["reference_docs"], [])

    def test_eww_surfaces_reference_templates(self):
        result = _read_syntax("eww")
        names = [t["name"] for t in result["reference_templates"]]
        self.assertIn("eww/_reference/bar.yuck", names)

    def test_quickshell_surfaces_reference_templates(self):
        result = _read_syntax("quickshell")
        names = [t["name"] for t in result["reference_templates"]]
        self.assertIn("quickshell/bar.qml", names)

    def test_quickshell_surfaces_reference_docs(self):
        result = _read_syntax("quickshell")
        names = [doc["name"] for doc in result["reference_docs"]]
        self.assertIn("quickshell-v0.3.0-types/index.json", names)
        self.assertIn("quickshell-v0.3.0-types/summary.md", names)


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

class TestFormatReferenceTemplates(unittest.TestCase):
    def test_empty_returns_empty_string(self):
        self.assertEqual(_format_reference_templates([]), "")

    def test_renders_named_blocks(self):
        templates = [
            {"name": "a.qml", "language": "qml", "content": "PanelWindow {}"},
            {"name": "b.scss", "language": "scss", "content": ".bar { color: red; }"},
        ]
        out = _format_reference_templates(templates)
        self.assertIn("REFERENCE TEMPLATES", out)
        self.assertIn("--- a.qml ---", out)
        self.assertIn("```qml", out)
        self.assertIn("PanelWindow {}", out)
        self.assertIn("--- b.scss ---", out)
        self.assertIn("```scss", out)

    def test_skips_empty_content(self):
        out = _format_reference_templates([
            {"name": "x.qml", "language": "qml", "content": ""},
        ])
        self.assertNotIn("--- x.qml ---", out)


class TestFormatReferenceDocs(unittest.TestCase):
    def test_empty_returns_empty_string(self):
        self.assertEqual(_format_reference_docs([]), "")

    def test_renders_quickshell_docs_snapshot_compactly(self):
        docs = _load_reference_docs(["quickshell-v0.3.0-types/index.json"])
        out = _format_reference_docs(docs)
        self.assertIn("FRAMEWORK SOURCE-OF-TRUTH DOCS", out)
        self.assertIn("Quickshell docs snapshot v0.3.0", out)
        self.assertIn("Quickshell/PanelWindow", out)
        self.assertIn("Quickshell.Io/Process", out)
        self.assertIn("exclusionMode", out)


class TestBuildPromptInjectsTemplates(unittest.TestCase):
    _DESIGN_INTENT = {
        "theme_name": "t", "description": "d", "mood_tags": ["dark"],
        "palette": {"base": "#000"},
    }

    def test_quickshell_prompt_contains_reference_templates(self):
        research = {
            "syntax": _read_syntax("quickshell"),
            "system": {"existing_files": {}},
            "design_intent": self._DESIGN_INTENT,
        }
        prompt = _build_prompt("widgets:quickshell", research)
        self.assertIn("REFERENCE TEMPLATES", prompt)
        self.assertIn("quickshell/bar.qml", prompt)
        self.assertIn("PanelWindow", prompt)
        self.assertIn("FRAMEWORK SOURCE-OF-TRUTH DOCS", prompt)
        self.assertIn("Quickshell docs snapshot v0.3.0", prompt)
        self.assertIn("Quickshell.Io/Process", prompt)

    def test_eww_prompt_contains_reference_templates(self):
        research = {
            "syntax": _read_syntax("eww"),
            "system": {"existing_files": {}},
            "design_intent": self._DESIGN_INTENT,
        }
        prompt = _build_prompt("widgets:eww", research)
        self.assertIn("REFERENCE TEMPLATES", prompt)
        self.assertIn("eww/_reference/bar.yuck", prompt)
        self.assertIn("defwidget", prompt)

    def test_kde_eww_prompt_warns_against_hyprctl(self):
        research = {
            "syntax": _read_syntax("eww"),
            "system": {"existing_files": {}},
            "design_intent": self._DESIGN_INTENT,
            "device_profile": {"wm": "kde", "desktop_recipe": "kde", "session_type": "wayland"},
        }
        prompt = _build_prompt("widgets:eww", research)
        self.assertIn("WM/session: kde / wayland", prompt)
        self.assertIn("Do NOT use hyprctl unless the audited WM is Hyprland", prompt)

    def test_eww_prompt_warns_against_calc_geometry_and_shell_dollar_fields(self):
        research = {
            "syntax": _read_syntax("eww"),
            "system": {"existing_files": {}},
            "design_intent": self._DESIGN_INTENT,
        }
        prompt = _build_prompt("widgets:eww", research)
        self.assertIn("never use CSS calc() in :geometry", prompt)
        self.assertIn("avoid awk positional fields like $1/$2/$3", prompt)
        self.assertIn("progress/scale :value must always be numeric", prompt)

    def test_quickshell_prompt_contains_texture_assets_when_provided(self):
        research = {
            "syntax": _read_syntax("quickshell"),
            "system": {"existing_files": {}},
            "design_intent": self._DESIGN_INTENT,
            "texture_assets": {"assets": [{"path": "assets/t/panel_ornate_9slice.png", "slice_px": 28}]},
        }
        prompt = _build_prompt("widgets:quickshell", research)
        self.assertIn("GENERATED ORNATE TEXTURE ASSETS", prompt)
        self.assertIn("assets/t/panel_ornate_9slice.png", prompt)
        self.assertIn("do not invent paths", prompt)

    def test_unknown_framework_prompt_omits_block(self):
        research = {
            "syntax": _read_syntax("mystery"),
            "system": {"existing_files": {}},
            "design_intent": self._DESIGN_INTENT,
        }
        prompt = _build_prompt("widgets:mystery", research)
        self.assertNotIn("REFERENCE TEMPLATES", prompt)


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


class TestEvaluateFiles(unittest.TestCase):
    """Deterministic post-generation gate inside ``generate_files``."""

    _RESEARCH = {
        "syntax": {"key_files": ["eww.yuck", "eww.scss"]},
    }
    _DESIGN = {
        "palette": {
            "background": "#161311", "foreground": "#e8d8b8", "accent": "#c4793a",
        },
    }

    def _ok_files(self) -> list[dict]:
        return [
            {"path": "eww.yuck",
             "content": "(defwindow bar [] (box :class \"x\" :style \"background: #161311;\"))"},
            {"path": "eww.scss",
             "content": "* { background-color: #c4793a; color: #e8d8b8; padding: 4px; }"},
        ]

    def test_accepts_valid_file_set(self):
        ok, reasons = evaluate_files(self._ok_files(), self._RESEARCH, self._DESIGN)
        self.assertTrue(ok, msg=f"unexpected reasons: {reasons}")
        self.assertEqual(reasons, [])

    def test_accepts_palette_in_stylesheet_only(self):
        files = [
            {"path": "eww.yuck",
             "content": "(defwindow bar [] (box :class \"x\" (label :text \"Bonfire Hollow menu\")))"},
            {"path": "eww.scss",
             "content": "* { background-color: #161311; color: #e8d8b8; border-color: #c4793a; padding: 4px; }"},
        ]
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertTrue(ok, msg=f"unexpected reasons: {reasons}")

    def test_rejects_empty(self):
        ok, reasons = evaluate_files([], self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertIn("no files produced", reasons)

    def test_flags_missing_required_files(self):
        files = [self._ok_files()[0]]   # only eww.yuck, missing eww.scss
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("missing required files" in r and "eww.scss" in r for r in reasons))

    def test_flags_missing_palette(self):
        files = [
            {"path": "eww.yuck", "content": "(defwindow bar [] (label :text \"hello world goes here\"))"},
            {"path": "eww.scss", "content": "* { background: #ffffff; color: #000000; padding: 4px; }"},
        ]
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("palette hex values" in r for r in reasons))

    def test_flags_unsafe_path(self):
        files = self._ok_files() + [
            {"path": "../../etc/evil.conf",
             "content": "background: #161311; this is some sufficiently long content for size check"},
        ]
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("unsafe path" in r for r in reasons))

    def test_flags_short_content(self):
        files = [
            {"path": "eww.yuck", "content": "tiny #161311"},
            {"path": "eww.scss", "content": "* { background: #c4793a; padding: 4px; min-width: 1px; }"},
        ]
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("too short" in r for r in reasons))

    def test_skips_palette_check_when_palette_empty(self):
        ok, reasons = evaluate_files(self._ok_files(), self._RESEARCH, {"palette": {}})
        self.assertTrue(ok, msg=f"unexpected reasons: {reasons}")

    def test_rejects_eww_calc_geometry(self):
        files = [
            {"path": "eww.yuck",
             "content": "(defwindow bar [] :geometry (geometry :width \"calc(100% - 48px)\" :height \"42px\") (box :class \"x\"))"},
            {"path": "eww.scss",
             "content": "* { background-color: #161311; color: #e8d8b8; border-color: #c4793a; padding: 4px; }"},
        ]
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("calc()" in r for r in reasons), msg=reasons)

    def test_rejects_eww_shell_dollar_fields(self):
        files = [
            {"path": "eww.yuck",
             "content": "(defpoll mem :interval \"5s\" \"sh -c 'free | awk \\\"/Mem:/ {print $3/$2}\\\"'\")\n(defwindow bar [] (box :class \"x\"))"},
            {"path": "eww.scss",
             "content": "* { background-color: #161311; color: #e8d8b8; border-color: #c4793a; padding: 4px; }"},
        ]
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("$ variables" in r for r in reasons), msg=reasons)

    def test_rejects_quickshell_iconimage_unknown_type(self):
        research = {"syntax": {"key_files": ["shell.qml"]}}
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { IconImage { source: '#161311' } }",
        }]
        ok, reasons = evaluate_files(files, research, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("IconImage" in r for r in reasons), msg=reasons)

    def test_rejects_quickshell_token_config_when_plan_promises_many_widgets(self):
        research = {"syntax": {"key_files": ["shell.qml"]}}
        design = {
            "palette": self._DESIGN["palette"],
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "notifications", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { PanelWindow { color: '#161311'; implicitHeight: 28; Text { text: 'bar'; color: '#e8d8b8' } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertFalse(ok)
        self.assertTrue(any("promised widget/panel surfaces" in r for r in reasons), msg=reasons)

    def test_rejects_quickshell_floatingwindow_for_promised_widget_chrome(self):
        research = {"syntax": {"key_files": ["shell.qml"]}}
        design = {
            "palette": self._DESIGN["palette"],
            "visual_element_plan": [
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "notifications", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { PanelWindow { Text { text: 'REST launcher #161311 #e8d8b8' } } PanelWindow { Text { text: 'INVENTORY menu #c4793a' } } FloatingWindow { visible: true; Text { text: 'EMBER log #8a4f2a' } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertFalse(ok)
        self.assertTrue(any("FloatingWindow" in r and "decorated app windows" in r for r in reasons), msg=reasons)

    def test_accepts_quickshell_multi_surface_rpg_widget_config(self):
        research = {"syntax": {"key_files": ["shell.qml"]}}
        design = {
            "palette": self._DESIGN["palette"],
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { PanelWindow { Text { text: 'REST launcher #161311 #e8d8b8' } } PanelWindow { Text { text: 'INVENTORY menu #c4793a' } } PanelWindow { anchors { right: true; top: true }; margins { top: 48; right: 18 }; exclusionMode: ExclusionMode.Ignore; Text { text: 'EMBER log #8a4f2a' } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertTrue(ok, msg=reasons)

    def test_rejects_ornate_quickshell_without_tiled_borderimage(self):
        research = {"syntax": {"key_files": ["shell.qml"]}}
        design = {
            "palette": self._DESIGN["palette"],
            "description": "bonfire blackiron Diablo RPG menu with ornate thorn carved borders",
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { PanelWindow { Rectangle { border.color: '#c4793a'; Text { text: 'REST launcher #161311 #e8d8b8' } } } PanelWindow { Rectangle { border.color: '#c4793a'; Text { text: 'INVENTORY menu #c4793a' } } } PanelWindow { Rectangle { border.color: '#c4793a'; Text { text: 'EMBER log #8a4f2a' } } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertFalse(ok)
        self.assertTrue(any("BorderImage" in r and "plain Rectangle border" in r for r in reasons), msg=reasons)

    def test_accepts_ornate_quickshell_with_tiled_borderimage_and_declared_assets(self):
        research = {
            "syntax": {"key_files": ["shell.qml"]},
            "texture_assets": {"assets": [{"path": "assets/bonfire-blackiron/panel_ornate_9slice.png", "slice_px": 18}]},
        }
        design = {
            "palette": self._DESIGN["palette"],
            "description": "bonfire blackiron ornate relic inventory frame chrome",
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { component SootTexture: Image { source: 'assets/bonfire-blackiron/panel_ornate_9slice.png'; fillMode: Image.Tile } component Frame: BorderImage { source: 'assets/bonfire-blackiron/panel_ornate_9slice.png'; border.left: 18; border.right: 18; horizontalTileMode: BorderImage.Repeat } component ItemSlot: Item {} component ResourceOrb: Item {} component BeltSocket: Item {} PanelWindow { Frame {} SootTexture { anchors.fill: parent } ResourceOrb {} Text { text: 'REST launcher EMBER #161311 #e8d8b8' } } PanelWindow { Frame {} GridLayout { columns: 4; ItemSlot {} } Text { text: 'INVENTORY menu relic belt quickslot #c4793a' } } PanelWindow { Frame {} BeltSocket {} Text { text: 'GEAR ALTAR equipment ITEM DETAIL Damage durability #8a4f2a' } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertTrue(ok, msg=reasons)

    def test_rejects_ornate_quickshell_with_flat_rectangle_interiors(self):
        research = {
            "syntax": {"key_files": ["shell.qml"]},
            "texture_assets": {"assets": [{"path": "assets/bonfire-blackiron/panel_ornate_9slice.png", "slice_px": 18}]},
        }
        design = {
            "palette": self._DESIGN["palette"],
            "description": "bonfire blackiron ornate relic inventory frame chrome",
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { component Frame: BorderImage { source: 'assets/bonfire-blackiron/panel_ornate_9slice.png'; border.left: 18; border.right: 18; horizontalTileMode: BorderImage.Repeat } component ItemSlot: Item {} component ResourceOrb: Item {} component BeltSocket: Item {} PanelWindow { Frame {} Rectangle { anchors.fill: parent; color: '#303030' } ResourceOrb {} Text { text: 'REST EMBER launcher #161311 #e8d8b8' } } PanelWindow { Frame {} GridLayout { columns: 4; ItemSlot {} } Text { text: 'INVENTORY relic belt quickslot #c4793a' } } PanelWindow { Frame {} BeltSocket {} Text { text: 'GEAR ALTAR equipment ITEM DETAIL Damage durability #8a4f2a' } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertFalse(ok)
        self.assertTrue(any("flat Rectangle fills" in r for r in reasons), msg=reasons)

    def test_rejects_ornate_quickshell_with_undeclared_borderimage_asset(self):
        research = {
            "syntax": {"key_files": ["shell.qml"]},
            "texture_assets": {"assets": [{"path": "assets/bonfire-blackiron/panel_ornate_9slice.png", "slice_px": 18}]},
        }
        design = {
            "palette": self._DESIGN["palette"],
            "description": "bonfire blackiron ornate relic inventory frame chrome",
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { component Frame: BorderImage { source: 'assets/made-up/panel.png'; border.left: 18; border.right: 18; horizontalTileMode: BorderImage.Repeat } PanelWindow { Frame {} Text { text: 'REST launcher #161311 #e8d8b8' } } PanelWindow { Frame {} Text { text: 'INVENTORY menu #c4793a' } } PanelWindow { Frame {} Text { text: 'EMBER log #8a4f2a' } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertFalse(ok)
        self.assertTrue(any("undeclared BorderImage texture assets" in r for r in reasons), msg=reasons)

    def test_rejects_ornate_quickshell_borderimage_without_texture_metadata(self):
        research = {"syntax": {"key_files": ["shell.qml"]}}
        design = {
            "palette": self._DESIGN["palette"],
            "description": "bonfire blackiron ornate relic inventory frame chrome",
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
            ],
        }
        files = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { component Frame: BorderImage { source: 'assets/bonfire-blackiron/panel_ornate_9slice.png'; border.left: 18; border.right: 18; horizontalTileMode: BorderImage.Repeat } PanelWindow { Frame {} Text { text: 'REST launcher #161311 #e8d8b8' } } PanelWindow { Frame {} Text { text: 'INVENTORY menu #c4793a' } } PanelWindow { Frame {} Text { text: 'EMBER log #8a4f2a' } } }",
        }]
        ok, reasons = evaluate_files(files, research, design)
        self.assertFalse(ok)
        self.assertTrue(any("texture_assets metadata" in r for r in reasons), msg=reasons)

    def test_rejects_eww_raw_variable_progress_value(self):
        files = [
            {"path": "eww.yuck",
             "content": "(defpoll mem :interval \"5s\" \"python3 -c 'print(42)'\")\n(defwindow bar [] (progress :class \"meter\" :value mem))"},
            {"path": "eww.scss",
             "content": "* { background-color: #161311; color: #e8d8b8; border-color: #c4793a; padding: 4px; }"},
        ]
        ok, reasons = evaluate_files(files, self._RESEARCH, self._DESIGN)
        self.assertFalse(ok)
        self.assertTrue(any("progress/scale" in r for r in reasons), msg=reasons)


class TestGenerateFilesTextureAssets(unittest.TestCase):
    def test_generate_files_prepares_texture_assets_for_ornate_quickshell(self):
        design = {
            "name": "bonfire-blackiron",
            "description": "ornate Diablo blackiron RPG menu chrome",
            "palette": {"base": "#161311", "fg": "#e8d8b8", "accent": "#c4793a"},
            "visual_element_plan": [
                {"desktop_element": "panel/widgets", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "launcher", "implementation_tool": "widgets:quickshell"},
                {"desktop_element": "widgets", "implementation_tool": "widgets:quickshell"},
            ],
        }
        accepted = [{
            "path": "shell.qml",
            "content": "import Quickshell\nimport QtQuick\nShellRoot { component SootTexture: Image { source: 'assets/bonfire-blackiron/panel_ornate_9slice.png'; fillMode: Image.Tile } component Frame: BorderImage { source: 'assets/bonfire-blackiron/panel_ornate_9slice.png'; border.left: 28; border.right: 28; horizontalTileMode: BorderImage.Repeat } component ItemSlot: Item {} component ResourceOrb: Item {} component BeltSocket: Item {} PanelWindow { Frame {} SootTexture { anchors.fill: parent } ResourceOrb {} Text { text: 'REST launcher EMBER #161311 #e8d8b8' } } PanelWindow { Frame {} GridLayout { columns: 4; ItemSlot {} } Text { text: 'INVENTORY menu relic belt quickslot #c4793a' } } PanelWindow { Frame {} BeltSocket {} Text { text: 'GEAR ALTAR equipment ITEM DETAIL Damage durability #c4793a' } } }",
        }]
        research = {"syntax": {"key_files": ["shell.qml"]}, "system": {"existing_files": {}}}
        with patch("workflow.nodes.craft.codegen.prepare_texture_assets", return_value={"assets": [{"path": "assets/bonfire-blackiron/panel_ornate_9slice.png", "slice_px": 28}]} ) as prep, \
             patch("workflow.nodes.craft.codegen._structured_invoke", return_value=accepted), \
             patch("workflow.nodes.craft.codegen._text_invoke", return_value=[]):
            files = generate_files("widgets:quickshell", design, research)
        prep.assert_called_once()
        self.assertEqual(files, accepted)
        self.assertIn("texture_assets", research)


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

    def test_score_accepts_eww_palette_in_scss_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            yuck = Path(tmp) / "eww.yuck"
            scss = Path(tmp) / "eww.scss"
            yuck.write_text("(defwindow menu [] (box :class \"relic\" (label :text \"Bonfire Hollow\")))", encoding="utf-8")
            scss.write_text(".relic { background: #1e1e2e; color: #89b4fa; padding: 8px; }", encoding="utf-8")
            score = _score([str(yuck), str(scss)], self._DESIGN, ["eww.yuck", "eww.scss"])
        self.assertGreaterEqual(score, 8)

    def test_valid_split_eww_files_do_not_interrupt(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = [
                {"path": "eww.yuck",
                 "content": "(defwindow menu [] (box :class \"relic\" (label :text \"Bonfire Hollow menu\")))"},
                {"path": "eww.scss",
                 "content": ".relic { background: #1e1e2e; color: #89b4fa; padding: 8px; }"},
            ]
            research = {"syntax": {"key_files": ["eww.yuck", "eww.scss"]}, "system": {"existing_files": {}}}
            with patch("workflow.nodes.craft.config_dir", return_value=Path(tmp)), \
                 patch("workflow.nodes.craft.gather_research", return_value=research), \
                 patch("workflow.nodes.craft.generate_files", return_value=files), \
                 patch("workflow.nodes.craft.interrupt") as interrupt_mock:
                from workflow.nodes.craft import craft_node
                result = craft_node({
                    "element_queue": ["widgets:eww"],
                    "design": self._DESIGN,
                    "session_dir": "",
                    "impl_retry_counts": {},
                })
        interrupt_mock.assert_not_called()
        self.assertEqual(result["element_queue"], [])
        self.assertGreaterEqual(result["craft_log"][0]["score"], 8)

    def test_craft_copies_generated_texture_assets_for_quickshell(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as session:
            session_path = Path(session)
            asset = session_path / "generated" / "quickshell" / "assets" / "bonfire" / "panel_ornate_9slice.png"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"fakepng")
            files = [{"path": "shell.qml", "content": "import Quickshell\nShellRoot { PanelWindow { Text { text: '#1e1e2e #89b4fa' } } }"}]
            research = {
                "syntax": {"key_files": ["shell.qml"]},
                "system": {"existing_files": {}},
                "texture_assets": {"root": str(session_path / "generated" / "quickshell"), "assets": [{"path": "assets/bonfire/panel_ornate_9slice.png"}]},
            }
            with patch("workflow.nodes.craft.config_dir", return_value=Path(tmp)), \
                 patch("workflow.nodes.craft.get_reference", return_value={"config_dir": tmp, "key_files": ["shell.qml"]}), \
                 patch("workflow.nodes.craft.gather_research", return_value=research), \
                 patch("workflow.nodes.craft.generate_files", return_value=files), \
                 patch("workflow.nodes.craft.interrupt", return_value="accept"):
                from workflow.nodes.craft import craft_node
                result = craft_node({
                    "element_queue": ["widgets:quickshell"],
                    "design": self._DESIGN,
                    "session_dir": str(session_path),
                    "impl_retry_counts": {},
                })
            copied = Path(tmp) / "assets" / "bonfire" / "panel_ornate_9slice.png"
            self.assertTrue(copied.exists())
            self.assertIn(str(copied), result["craft_log"][0]["written"])

    def test_empty_files_first_attempt_retries(self):
        """First codegen failure re-queues the element instead of silent SKIP."""
        result = self._run_craft([], "")
        # Element should be re-queued for retry (not popped) and counted.
        self.assertEqual(result.get("element_queue"), ["widgets:eww"])
        self.assertEqual(result.get("impl_retry_counts", {}).get("widgets:eww"), 1)
        # No craft_log entry yet — this is a failed attempt, not a final verdict.
        self.assertNotIn("craft_log", result)

    def test_empty_files_skips_after_max_retries(self):
        """After MAX_IMPLEMENT_RETRIES failed attempts, element is SKIPped."""
        from workflow.config import MAX_IMPLEMENT_RETRIES
        from workflow.nodes.craft import craft_node
        state = {
            "element_queue": ["widgets:eww"],
            "design": self._DESIGN,
            "session_dir": "",
            "impl_retry_counts": {"widgets:eww": MAX_IMPLEMENT_RETRIES - 1},
        }
        with patch("workflow.nodes.craft.gather_research", return_value={}), \
             patch("workflow.nodes.craft.generate_files", return_value=[]):
            result = craft_node(state)
        log = result.get("craft_log", [])
        self.assertTrue(any("SKIP" in str(r.get("verdict", "")) for r in log))
        self.assertEqual(result.get("element_queue"), [])
        self.assertNotIn("widgets:eww", result.get("impl_retry_counts", {}))

    def test_redundant_eww_fallback_skipped_after_quickshell_crafted_on_kde_wayland(self):
        from workflow.nodes.craft import craft_node
        design = {
            **self._DESIGN,
            "chrome_strategy": {"implementation_targets": ["widgets:quickshell"]},
        }
        state = {
            "element_queue": ["widgets:eww"],
            "design": design,
            "device_profile": {"wm": "kde", "session_type": "wayland"},
            "session_dir": "",
            "impl_retry_counts": {"widgets:eww": 2},
            "craft_log": [{"element": "widgets:quickshell", "verdict": "crafted", "score": 10}],
        }
        with patch("workflow.nodes.craft.gather_research") as research, \
             patch("workflow.nodes.craft.generate_files") as codegen:
            result = craft_node(state)
        research.assert_not_called()
        codegen.assert_not_called()
        self.assertEqual(result.get("element_queue"), [])
        self.assertNotIn("widgets:eww", result.get("impl_retry_counts", {}))
        self.assertIn("redundant fallback", result["craft_log"][0]["verdict"])

    def test_eww_required_not_skipped_even_when_quickshell_exists(self):
        from workflow.nodes.craft import craft_node
        design = {
            **self._DESIGN,
            "chrome_strategy": {"implementation_targets": ["widgets:quickshell"], "eww_required": True},
        }
        state = {
            "element_queue": ["widgets:eww"],
            "design": design,
            "device_profile": {"wm": "kde", "session_type": "wayland"},
            "session_dir": "",
            "impl_retry_counts": {},
            "craft_log": [{"element": "widgets:quickshell", "verdict": "crafted", "score": 10}],
        }
        with patch("workflow.nodes.craft.gather_research", return_value={}), \
             patch("workflow.nodes.craft.generate_files", return_value=[]):
            result = craft_node(state)
        self.assertEqual(result.get("element_queue"), ["widgets:eww"])
        self.assertEqual(result.get("impl_retry_counts", {}).get("widgets:eww"), 1)


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
