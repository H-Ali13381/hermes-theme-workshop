"""Tests for screenshot artifact capture."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from workflow.nodes.cleanup.visual_artifacts import _screenshot_command, capture_visual_artifacts


class VisualArtifactsTests(unittest.TestCase):
    def test_kde_prefers_spectacle_before_grim(self):
        with patch("workflow.nodes.cleanup.visual_artifacts.shutil.which", return_value="/usr/bin/tool"):
            cmd = _screenshot_command("kde", Path("out.png"))

        self.assertEqual(cmd[:4], ["spectacle", "--background", "--fullscreen", "-o"])

    def test_non_kde_uses_grim_when_available(self):
        def fake_which(name):
            return "/usr/bin/grim" if name == "grim" else None

        with patch("workflow.nodes.cleanup.visual_artifacts.shutil.which", side_effect=fake_which):
            cmd = _screenshot_command("hyprland", Path("out.png"))

        self.assertEqual(cmd, ["grim", "out.png"])

    def test_capture_writes_artifact_record_when_command_succeeds(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)

        def fake_run(cmd, **_kwargs):
            Path(cmd[-1]).write_text("png", encoding="utf-8")
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""
            return result

        with patch("workflow.nodes.cleanup.visual_artifacts.shutil.which", return_value="/usr/bin/spectacle"), \
             patch("workflow.nodes.cleanup.visual_artifacts.subprocess.run", side_effect=fake_run):
            artifacts = capture_visual_artifacts({"session_dir": str(tmp), "device_profile": {"wm": "kde"}})

        self.assertEqual(artifacts[0]["status"], "ok")
        self.assertTrue(Path(artifacts[0]["path"]).exists())


if __name__ == "__main__":
    unittest.main()