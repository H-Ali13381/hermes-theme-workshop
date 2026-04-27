"""Tests for install package resolver timeout handling."""
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, call, patch

from workflow.nodes.install.resolver import install_packages


class InstallResolverTimeoutTests(unittest.TestCase):
    def test_pacman_timeout_appends_to_errors(self):
        errors = []
        with patch("workflow.nodes.install.resolver.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd=[], timeout=300)) as mock_run:
            install_packages(["some-pkg"], errors)

        self.assertIn("some-pkg", errors)
        mock_run.assert_called_once()

    def test_yay_timeout_appends_to_errors(self):
        errors = []
        pacman_fail = MagicMock()
        pacman_fail.returncode = 1

        def side_effect(*args, **kwargs):
            cmd = args[0]
            if "pacman" in cmd:
                return pacman_fail
            raise subprocess.TimeoutExpired(cmd=[], timeout=300)

        with patch("workflow.nodes.install.resolver.subprocess.run", side_effect=side_effect):
            install_packages(["aur-pkg"], errors)

        self.assertIn("aur-pkg", errors)

    def test_both_fail_appends_to_errors(self):
        errors = []
        fail = MagicMock()
        fail.returncode = 1

        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=fail):
            install_packages(["missing-pkg"], errors)

        self.assertIn("missing-pkg", errors)

    def test_successful_install_no_errors(self):
        errors = []
        ok = MagicMock()
        ok.returncode = 0

        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=ok):
            install_packages(["good-pkg"], errors)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
