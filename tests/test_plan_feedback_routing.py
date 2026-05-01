"""Tests for the Step 4 plan-feedback classifier and tiered routing."""
from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from langgraph.graph import END

from workflow.nodes import plan as plan_mod
from workflow import routing


class _RecordingLLM:
    """Minimal LangChain-compatible chat model fake."""

    def __init__(self, content: str):
        self.content = content
        self.received: list = []

    def invoke(self, messages):
        self.received.append(messages)
        return SimpleNamespace(content=self.content)


class FeedbackMessageMarkerTests(unittest.TestCase):
    def test_make_and_extract_round_trip(self):
        m = plan_mod._make_feedback_message("palette is too cold")
        self.assertTrue(m.content.startswith(plan_mod.PLAN_FEEDBACK_MARKER))
        feedbacks = plan_mod._get_feedback_messages([m])
        self.assertEqual(feedbacks, ["palette is too cold"])

    def test_get_feedback_messages_ignores_non_marked(self):
        from langchain_core.messages import AIMessage, HumanMessage

        msgs = [
            AIMessage(content="hi"),
            HumanMessage(content="ordinary user reply"),
            plan_mod._make_feedback_message("real feedback"),
        ]
        self.assertEqual(plan_mod._get_feedback_messages(msgs), ["real feedback"])


class FormatFeedbackBlockTests(unittest.TestCase):
    def test_empty_returns_empty_string(self):
        self.assertEqual(plan_mod._format_feedback_block([]), "")

    def test_under_threshold_is_verbatim(self):
        items = ["a", "b", "c"]
        block = plan_mod._format_feedback_block(items)
        for item in items:
            self.assertIn(f"- {item}", block)
        self.assertNotIn("summarized", block.lower())

    def test_above_threshold_summarizes_older_keeps_recent_two(self):
        items = [f"item {i}" for i in range(8)]  # threshold is 6
        with patch.object(plan_mod, "_summarize_feedback", return_value="- summary bullet"):
            block = plan_mod._format_feedback_block(items)
        self.assertIn("Earlier feedback (summarized)", block)
        self.assertIn("- summary bullet", block)
        self.assertIn("Most recent feedback", block)
        self.assertIn("item 6", block)
        self.assertIn("item 7", block)


class ClassifierTests(unittest.TestCase):
    def test_classifier_parses_json_object(self):
        fake = _RecordingLLM('{"label": "refine", "reason": "palette change"}')
        with patch.object(plan_mod, "get_llm", return_value=fake):
            label, reason = plan_mod._classify_feedback("make accent purple")
        self.assertEqual(label, "refine")
        self.assertEqual(reason, "palette change")

    def test_classifier_tolerates_fenced_json(self):
        fake = _RecordingLLM('```json\n{"label":"explore","reason":"vibe shift"}\n```')
        with patch.object(plan_mod, "get_llm", return_value=fake):
            label, _ = plan_mod._classify_feedback("totally different vibe")
        self.assertEqual(label, "explore")

    def test_classifier_returns_ambiguous_on_unparseable_response(self):
        fake = _RecordingLLM("I think maybe refine? not sure.")
        with patch.object(plan_mod, "get_llm", return_value=fake):
            label, _ = plan_mod._classify_feedback("hmm")
        self.assertEqual(label, "ambiguous")

    def test_classifier_returns_ambiguous_on_unknown_label(self):
        fake = _RecordingLLM('{"label": "bikeshed", "reason": "x"}')
        with patch.object(plan_mod, "get_llm", return_value=fake):
            label, _ = plan_mod._classify_feedback("x")
        self.assertEqual(label, "ambiguous")

    def test_classifier_falls_back_to_render_on_exception(self):
        broken = MagicMock()
        broken.invoke.side_effect = RuntimeError("network down")
        with patch.object(plan_mod, "get_llm", return_value=broken):
            label, reason = plan_mod._classify_feedback("anything")
        self.assertEqual(label, "render")
        self.assertIn("classifier error", reason)

    def test_classifier_returns_render_on_empty_input(self):
        # Should not even call the LLM.
        with patch.object(plan_mod, "get_llm", side_effect=AssertionError("should not be called")):
            label, _ = plan_mod._classify_feedback("   ")
        self.assertEqual(label, "render")


class RenderPreviewIncludesFeedbackTests(unittest.TestCase):
    def test_feedback_block_appears_in_llm_prompt(self, ):
        design = {"name": "test-theme", "palette": {"background": "#000"}}
        feedback_block = "- earlier: palette was too dim"

        # Minimal HTML so contract checks pass.
        fake = _RecordingLLM("<!DOCTYPE html><html><body>preview</body></html>" + ("x" * 600))

        with patch.object(plan_mod, "get_llm", return_value=fake):
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / "plan.html"
                plan_mod._render_preview(path, design, feedback_block)

        self.assertEqual(len(fake.received), 1)
        sent_messages = fake.received[0]
        # User message is the second element (system + human).
        human_content = sent_messages[1].content
        self.assertIn("test-theme", human_content)
        self.assertIn("earlier: palette was too dim", human_content)
        self.assertIn("User feedback so far on prior previews", human_content)

    def test_no_feedback_block_omits_section(self):
        design = {"name": "x", "palette": {}}
        fake = _RecordingLLM("<!DOCTYPE html><html><body>" + ("p" * 600) + "</body></html>")
        with patch.object(plan_mod, "get_llm", return_value=fake):
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                plan_mod._render_preview(Path(td) / "plan.html", design, "")
        human_content = fake.received[0][1].content
        self.assertNotIn("User feedback so far", human_content)


class DispatchFeedbackTests(unittest.TestCase):
    def _common_args(self, label: str, **overrides):
        import tempfile
        td = tempfile.mkdtemp()
        html_path = Path(td) / "plan.html"
        html_path.write_text("<html></html>", encoding="utf-8")
        args = dict(
            label=label,
            reason="test",
            feedback_text="palette is too cold",
            html_path=html_path,
            session_dir="",
            loop_counts={"plan": 4, "refine": 7, "explore": 9},
            explore_intake={"stage": "finalize", "brief": "neon ruins"},
            prior_design={"stance": "Ghost+Blade", "name_hypothesis": "shadow-signal"},
        )
        args.update(overrides)
        return args

    def test_approve_sets_route_and_keeps_html(self):
        args = self._common_args("approve")
        with patch.object(plan_mod, "append_step"):
            result = plan_mod._dispatch_feedback(**args)
        self.assertEqual(result["plan_feedback_route"], "approve")
        self.assertEqual(result["plan_html_path"], str(args["html_path"]))
        self.assertEqual(result["current_step"], 4)
        self.assertTrue(args["html_path"].exists())

    def test_render_clears_html_and_emits_marked_message(self):
        args = self._common_args("render")
        result = plan_mod._dispatch_feedback(**args)
        self.assertEqual(result["plan_feedback_route"], "render")
        self.assertEqual(result["plan_html_path"], "")
        self.assertFalse(args["html_path"].exists())
        marked = result["messages"][0]
        self.assertTrue(marked.content.startswith(plan_mod.PLAN_FEEDBACK_MARKER))

    def test_refine_resets_plan_and_refine_counters(self):
        args = self._common_args("refine")
        result = plan_mod._dispatch_feedback(**args)
        self.assertEqual(result["plan_feedback_route"], "refine")
        self.assertEqual(result["loop_counts"]["plan"], 0)
        self.assertEqual(result["loop_counts"]["refine"], 0)
        # Explore counter is untouched.
        self.assertEqual(result["loop_counts"]["explore"], 9)
        # Two messages: marked feedback + refine seed instruction.
        self.assertEqual(len(result["messages"]), 2)
        seed = result["messages"][1].content
        self.assertIn("revise the design.json", seed)
        self.assertIn("<<DESIGN_READY>>", seed)
        self.assertIn("palette is too cold", seed)

    def test_explore_resets_all_counters_and_seeds_revise_intake(self):
        args = self._common_args("explore")
        result = plan_mod._dispatch_feedback(**args)
        self.assertEqual(result["plan_feedback_route"], "explore")
        self.assertEqual(result["loop_counts"]["plan"], 0)
        self.assertEqual(result["loop_counts"]["refine"], 0)
        self.assertEqual(result["loop_counts"]["explore"], 0)
        intake = result["explore_intake"]
        self.assertEqual(intake["stage"], "revise")
        self.assertEqual(intake["prior_direction"]["stance"], "Ghost+Blade")
        self.assertEqual(intake["rejection_feedback"], "palette is too cold")
        # Original brief is preserved.
        self.assertEqual(intake["brief"], "neon ruins")


class AfterPlanRoutingTests(unittest.TestCase):
    def test_signal_approve_routes_to_baseline(self):
        state = {"plan_feedback_route": "approve", "loop_counts": {"plan": 1}}
        self.assertEqual(routing.after_plan(state), "baseline")

    def test_signal_refine_routes_to_refine(self):
        state = {"plan_feedback_route": "refine", "loop_counts": {"plan": 1}}
        self.assertEqual(routing.after_plan(state), "refine")

    def test_signal_explore_routes_to_explore(self):
        state = {"plan_feedback_route": "explore", "loop_counts": {"plan": 1}}
        self.assertEqual(routing.after_plan(state), "explore")

    def test_signal_render_routes_to_plan(self):
        state = {"plan_feedback_route": "render", "loop_counts": {"plan": 1}}
        self.assertEqual(routing.after_plan(state), "plan")

    def test_no_signal_with_valid_html_routes_to_baseline(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "plan.html"
            path.write_text("x" * 600, encoding="utf-8")
            state = {"plan_html_path": str(path), "loop_counts": {"plan": 1}}
            self.assertEqual(routing.after_plan(state), "baseline")

    def test_no_signal_no_html_routes_back_to_plan(self):
        state = {"plan_html_path": "", "loop_counts": {"plan": 1}}
        self.assertEqual(routing.after_plan(state), "plan")

    def test_loop_limit_aborts_to_end(self):
        from workflow.config import MAX_LOOP_ITERATIONS

        state = {"plan_feedback_route": "refine", "loop_counts": {"plan": MAX_LOOP_ITERATIONS}}
        self.assertEqual(routing.after_plan(state), END)


if __name__ == "__main__":
    unittest.main()
