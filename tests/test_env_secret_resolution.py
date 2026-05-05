"""Regression tests for workflow secret resolution."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow.config import _parse_env_assignments, resolve_env_secret


class EnvSecretResolutionTests(unittest.TestCase):
    def test_parse_export_assignment_after_interactive_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc = Path(tmp) / ".bashrc"
            rc.write_text(
                "# If not running interactively, don't do anything\n"
                "[[ $- != *i* ]] && return\n"
                "export FAL_KEY=\"abc:def\"\n",
                encoding="utf-8",
            )

            self.assertEqual(_parse_env_assignments(rc)["FAL_KEY"], "abc:def")

    def test_resolve_fal_key_from_bashrc_when_env_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".bashrc").write_text(
                "[[ $- != *i* ]] && return\n"
                "export FAL_KEY='from-bashrc'\n",
                encoding="utf-8",
            )

            with patch.dict(os.environ, {}, clear=True), \
                 patch("workflow.config.Path.home", return_value=home):
                self.assertEqual(resolve_env_secret("FAL_KEY"), "from-bashrc")
                self.assertEqual(os.environ.get("FAL_KEY"), "from-bashrc")

    def test_live_env_takes_priority_over_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".bashrc").write_text("export FAL_KEY=file-value\n", encoding="utf-8")

            with patch.dict(os.environ, {"FAL_KEY": "live-value"}, clear=True), \
                 patch("workflow.config.Path.home", return_value=home):
                self.assertEqual(resolve_env_secret("FAL_KEY"), "live-value")


if __name__ == "__main__":
    unittest.main()
