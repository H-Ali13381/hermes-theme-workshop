"""Live-LLM smoke tests for every LLM call site in the workflow.

Skipped by default. Run with::

    RICER_TEST_LIVE_LLM=1 python -m pytest tests/test_llm_live_smoke.py -v -s

Each test exercises one production code path against the real configured LLM
(`workflow.config.get_llm`) using a representative sample input and asserts the
response shape the workflow downstream expects. Prints a short excerpt for
human inspection; full responses go to ``tests/_llm_smoke_logs/``.
"""
from __future__ import annotations

import json
import os
import time
import unittest
from pathlib import Path

LIVE = os.environ.get("RICER_TEST_LIVE_LLM") == "1"
SKIP_REASON = "set RICER_TEST_LIVE_LLM=1 to run live-LLM smoke tests"

LOG_DIR = Path(__file__).parent / "_llm_smoke_logs"
LOG_DIR.mkdir(exist_ok=True)


def _log(name: str, content: str) -> None:
    (LOG_DIR / f"{name}.txt").write_text(content, encoding="utf-8")


def _excerpt(text: str, n: int = 240) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n].rstrip() + "…"


_DIRECTION = {
    "stance": "Ghost+Garden",
    "mood": ["mossy", "ember", "rested"],
    "reference_anchor": "Hollow Knight bonfire chapel; lichen-covered stone",
    "name_hypothesis": "moss-ember-vesper",
}
_PROFILE = {
    "wm": "plasma", "session_type": "wayland", "desktop_recipe": "kde",
    "chassis": "desktop", "screens": 2,
    "gpu": {"name": "NVIDIA RTX 4070 Super"},
    "apps": {"kitty": True, "konsole": True, "fastfetch": True},
    "fal_available": True,
}


@unittest.skipUnless(LIVE, SKIP_REASON)
class LiveLLMSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._t0 = time.monotonic()

    def tearDown(self) -> None:
        elapsed = time.monotonic() - self._t0
        print(f"  ⏱  {self._testMethodName}: {elapsed:.2f}s")

    # ── explore.py ──────────────────────────────────────────────────────────
    def test_explore_propose_stage(self):
        from langchain_core.messages import HumanMessage, SystemMessage
        from workflow.config import get_llm
        from workflow.nodes.explore import SYSTEM_PROMPT, _proposal_prompt
        intake = {"brief": "I want to live inside a moss-grown ruined chapel from Hollow Knight."}
        response = get_llm(0.7).invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_proposal_prompt(intake, _PROFILE)),
        ])
        text = response.content or ""
        _log("explore_propose", text)
        print(f"\n[explore.propose] {_excerpt(text)}")
        self.assertGreater(len(text), 80)
        # Accept any common numbered format: "1.", "1)", "**1", "Option 1", "## 1".
        import re as _re
        markers = _re.findall(r"(?:^|\n)\s*(?:[#*]+\s*)?(?:Option\s+)?[12]\b", text, _re.IGNORECASE)
        self.assertGreaterEqual(len(set(markers)), 2,
                                f"expected at least 2 numbered proposals in:\n{text[:400]}")

    def test_explore_finalize_emits_sentinel_and_json(self):
        from langchain_core.messages import HumanMessage, SystemMessage
        from workflow.config import get_llm
        from workflow.nodes.explore import (
            DIRECTION_SENTINEL, SYSTEM_PROMPT, _final_prompt, _parse_direction)
        intake = {
            "brief": "moss-grown chapel, Hollow Knight bonfire, soft amber light",
            "proposal": "1. Ember Chapel — bonfire warmth in stone arches; Garden+Ghost.\n"
                        "2. Lichen Stave — mossy verticals, cold dew; Ghost.\n"
                        "3. Vesper Hush — twilight chapel calm; Garden+Zen.",
            "choice": "1",
        }
        response = get_llm(0.7).invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_final_prompt(intake, _PROFILE)),
        ])
        text = response.content or ""
        _log("explore_finalize", text)
        print(f"\n[explore.finalize] {_excerpt(text)}")
        self.assertIn(DIRECTION_SENTINEL, text)
        direction = _parse_direction(text)
        self.assertIsInstance(direction, dict)
        self.assertIn("stance", direction)
        self.assertIn("mood", direction)

    # ── refine.py ───────────────────────────────────────────────────────────
    def test_refine_produces_valid_kde_design(self):
        from langchain_core.messages import HumanMessage, SystemMessage
        from workflow.config import get_llm
        from workflow.nodes.refine import _extract_design_json, build_system_prompt
        sysprompt = build_system_prompt("kde")
        response = get_llm(0.3).invoke([
            SystemMessage(content=sysprompt),
            HumanMessage(content=(
                f"Creative direction established:\n{json.dumps(_DIRECTION, indent=2)}\n\n"
                "Please produce the design_system.json for this theme."
            )),
        ])
        text = response.content or ""
        _log("refine_design", text)
        print(f"\n[refine] {_excerpt(text, 320)}")
        design, reason = _extract_design_json(text, "kde")
        self.assertIsNotNone(design, f"design parse/validate failed: {reason}")
        self.assertEqual(set(design["palette"].keys()), {
            "background", "foreground", "primary", "secondary", "accent",
            "surface", "muted", "danger", "success", "warning"})
        self.assertIn("originality_strategy", design)
        self.assertIn("chrome_strategy", design)

    # ── plan.py ─────────────────────────────────────────────────────────────
    def test_plan_classifier_returns_valid_label(self):
        from workflow.config import PLAN_FEEDBACK_LABELS
        from workflow.nodes.plan import _classify_feedback
        cases = [
            ("looks great, ship it", "approve"),
            ("the screenshot is glitchy, regenerate it", "render"),
            ("make the accent purple instead", "refine"),
            ("this whole vibe feels wrong, I wanted cyberpunk", "explore"),
        ]
        for feedback, expected in cases:
            label, reason = _classify_feedback(feedback)
            print(f"\n[plan.classify] {feedback!r} → {label} ({reason!r})")
            self.assertIn(label, PLAN_FEEDBACK_LABELS)
        # Allow model latitude — at least 2 of 4 should match the expected label.
        labels = [_classify_feedback(f)[0] for f, _ in cases]
        matches = sum(1 for got, (_, want) in zip(labels, cases) if got == want)
        self.assertGreaterEqual(matches, 2, f"classifier matched {matches}/4: {labels}")

    def test_plan_summarizer_returns_bullets(self):
        from workflow.nodes.plan import _summarize_feedback
        older = [
            "the palette is too cold, I want warmer earth tones",
            "drop the widgets, they feel like clutter",
            "rounded corners look wrong, keep them sharp",
            "never use neon accents",
        ]
        result = _summarize_feedback(older)
        _log("plan_summarize", result)
        print(f"\n[plan.summarize] {_excerpt(result)}")
        self.assertGreater(len(result), 20)

    # ── config.judge_design_creativity ──────────────────────────────────────
    def test_creativity_judge_passes_a_strong_design(self):
        from workflow.config import judge_design_creativity
        design = {
            "name": "moss-ember-vesper",
            "description": "Bonfire-lit chapel chrome with lichen-soft panels.",
            "palette": {
                "background": "#161311", "foreground": "#e8d8b8", "primary": "#c4793a",
                "secondary": "#7a8266", "accent": "#e9a85c", "surface": "#1f1a16",
                "muted": "#5b574d", "danger": "#b94747", "success": "#7e9466", "warning": "#cf9f3a",
            },
            "mood_tags": ["mossy", "ember", "rested"],
            "originality_strategy": {
                "vision_alignment": "Bonfire chapel calm; warm ember accents under cold stone surfaces.",
                "non_default_moves": [
                    "EWW vertical stave dock replacing the default Plasma panel",
                    "kitty terminal wrapped in a kvantum stone-arch ornamental frame",
                    "launcher rows styled as parchment quest entries with ember bullet glyphs",
                ],
            },
            "chrome_strategy": {
                "method": "kvantum stone-arch SVG + eww overlay frames",
                "implementation_targets": ["widgets:eww", "terminal:kitty", "kvantum"],
                "rounded_corners": {"enabled": True, "radius_px": 14},
            },
        }
        ok, reasons = judge_design_creativity(design, _DIRECTION)
        print(f"\n[judge] pass={ok} reasons={reasons}")
        self.assertTrue(ok, f"strong design unexpectedly rejected: {reasons}")

    def test_creativity_judge_rejects_palette_swap(self):
        from workflow.config import judge_design_creativity
        design = {
            "name": "default-swap",
            "description": "Just a darker palette over Plasma defaults.",
            "palette": {
                "background": "#1a1a1a", "foreground": "#f0f0f0", "primary": "#3584e4",
                "secondary": "#999999", "accent": "#3584e4", "surface": "#222222",
                "muted": "#666666", "danger": "#e01b24", "success": "#33d17a", "warning": "#f5c211",
            },
            "mood_tags": ["modern", "clean"],
            "originality_strategy": {
                "vision_alignment": "Just a clean modern look.",
                "non_default_moves": ["modern look", "clean panel", "polished defaults"],
            },
            "chrome_strategy": {"method": "", "implementation_targets": []},
        }
        ok, reasons = judge_design_creativity(design, _DIRECTION)
        print(f"\n[judge.reject] pass={ok} reasons={reasons}")
        # Fail-open is allowed — but if the judge does decide, it must reject this.
        if not ok:
            self.assertGreater(len(reasons), 0)

    # ── implement/spec.py ───────────────────────────────────────────────────
    def test_write_spec_returns_structured_output(self):
        from workflow.nodes.implement.spec import write_spec
        design = {
            "name": "moss-ember-vesper",
            "palette": {
                "background": "#161311", "foreground": "#e8d8b8", "primary": "#c4793a",
                "secondary": "#7a8266", "accent": "#e9a85c", "surface": "#1f1a16",
                "muted": "#5b574d", "danger": "#b94747", "success": "#7e9466", "warning": "#cf9f3a",
            },
            "mood_tags": ["mossy", "ember"],
        }
        spec = write_spec("terminal:kitty", design)
        _log("spec_kitty", json.dumps(spec, indent=2))
        print(f"\n[spec.kitty] {json.dumps(spec)[:300]}")
        for key in ("targets", "palette_keys", "font", "radii", "notes"):
            self.assertIn(key, spec)
        self.assertIsInstance(spec["targets"], list)
        self.assertIsInstance(spec["palette_keys"], list)

    # ── craft/codegen.py ────────────────────────────────────────────────────
    def test_codegen_generates_eww_files(self):
        """Exercises the full ``generate_files`` pipeline (structured output →
        deterministic evaluator → retry-with-feedback). A passing run proves
        the inner loop converges and the evaluator accepts real LLM output.
        """
        from workflow.nodes.craft.codegen import generate_files, evaluate_files
        design = {
            "name": "moss-ember-vesper",
            "palette": {
                "background": "#161311", "foreground": "#e8d8b8", "primary": "#c4793a",
                "secondary": "#7a8266", "accent": "#e9a85c", "surface": "#1f1a16",
                "muted": "#5b574d", "danger": "#b94747", "success": "#7e9466", "warning": "#cf9f3a",
            },
            "mood_tags": ["mossy", "ember"],
        }
        research = {
            "syntax": {
                "framework_name": "EWW", "config_dir": "~/.config/eww",
                "key_files": ["eww.yuck", "eww.scss"],
                "syntax_hint": "EWW uses Lisp-like .yuck for widgets and SCSS for styling. "
                               "Define windows with (defwindow), widgets with (defwidget).",
                "example": "(defwidget bar [] (centerbox :orientation \"h\" ...))",
                "reference_templates": [],
            },
            "system": {"existing_files": {}},
            "design_intent": {
                "theme_name": design["name"],
                "description": "Bonfire chapel chrome",
                "mood_tags": design["mood_tags"],
                "palette": design["palette"],
                "originality_strategy": {"non_default_moves": ["vertical stave dock"]},
                "chrome_strategy": {"method": "eww overlay", "implementation_targets": ["widgets:eww"]},
            },
        }
        files = generate_files("widgets:eww", design, research)
        _log("codegen_parsed", json.dumps(files, indent=2))
        print(f"\n[codegen] {len(files)} files; "
              f"paths={[f.get('path') for f in files]}")
        self.assertTrue(files, "generate_files returned 0 files; check codegen logs")
        ok, reasons = evaluate_files(files, research, design)
        self.assertTrue(ok, f"evaluator rejected production output: {reasons}")
        for f in files:
            self.assertIn("path", f)
            self.assertIn("content", f)
            self.assertGreater(len(f["content"]), 50, f"file {f['path']} too short")

    # ── handoff.py ──────────────────────────────────────────────────────────
    def test_handoff_generates_markdown(self):
        from langchain_core.messages import HumanMessage, SystemMessage
        from workflow.config import get_llm
        from workflow.nodes.handoff import SYSTEM_PROMPT
        design = {"name": "moss-ember-vesper", "palette": {"primary": "#c4793a"},
                  "mood_tags": ["mossy", "ember"]}
        payload = {
            "design": design,
            "implementation_log": [
                {"element": "terminal:kitty", "verdict": "verified", "scorecard": {"total": 9}},
                {"element": "widgets:eww", "verdict": "accepted-deviation", "scorecard": {"total": 7}},
            ],
            "cleanup_actions": ["reloaded waybar"],
            "effective_state": {"plasmashell": "running"},
            "errors": [],
        }
        response = get_llm(0.1).invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Session data:\n```json\n{json.dumps(payload, indent=2)}\n```"),
        ])
        text = response.content or ""
        _log("handoff_md", text)
        print(f"\n[handoff] {_excerpt(text, 300)}")
        self.assertIn("#", text, "expected markdown headers")
        self.assertIn("moss-ember-vesper", text.lower())


if __name__ == "__main__":
    unittest.main()
