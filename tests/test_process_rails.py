"""Workflow-level tests that process rails stay machine-enforced."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from workflow.nodes.cleanup import cleanup_node


class ProcessRailsTests(unittest.TestCase):
    def test_kde_cleanup_always_returns_finalization_audit_and_capabilities(self):
        state = {
            "device_profile": {"wm": "kde", "desktop_recipe": "kde"},
            "design": {"name": "moss"},
            "impl_log": [{"element": "window_decorations:kde", "spec": {"targets": []}}],
        }

        with patch("workflow.nodes.cleanup.finalize_kde", return_value=[{"action": "colorscheme-reapply"}]) as fin, \
             patch("workflow.nodes.cleanup.audit_effective_state", return_value={"desktop": "kde"}) as eff, \
             patch("workflow.nodes.cleanup.probe_capabilities", return_value={"desktop": "kde"}) as cap, \
             patch("workflow.nodes.cleanup.capture_visual_artifacts", return_value=[{"type": "screenshot"}]) as vis:
            result = cleanup_node(state)

        fin.assert_called_once()
        eff.assert_called_once()
        cap.assert_called_once()
        vis.assert_called_once()
        self.assertEqual(result["current_step"], 7)
        self.assertEqual(result["cleanup_actions"], [{"action": "colorscheme-reapply"}])
        self.assertEqual(result["effective_state"], {"desktop": "kde"})
        self.assertEqual(result["capability_report"], {"desktop": "kde"})
        self.assertEqual(result["visual_artifacts"], [{"type": "screenshot"}])

    def test_cleanup_does_not_emit_empty_errors_list(self):
        state = {"device_profile": {"wm": "gnome"}, "impl_log": []}
        with patch("workflow.nodes.cleanup.finalize_kde", return_value=[]), \
             patch("workflow.nodes.cleanup.audit_effective_state", return_value={}), \
             patch("workflow.nodes.cleanup.probe_capabilities", return_value={}), \
             patch("workflow.nodes.cleanup.capture_visual_artifacts", return_value=[]):
            result = cleanup_node(state)

        self.assertNotIn("errors", result)


if __name__ == "__main__":
    unittest.main()