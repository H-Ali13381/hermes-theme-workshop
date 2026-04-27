"""Tests for install/resolver.py — package resolution and sudo escalation."""
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch


class InstallPackagesTests(unittest.TestCase):
    def _ok(self):
        m = MagicMock()
        m.returncode = 0
        return m

    def _fail(self):
        m = MagicMock()
        m.returncode = 1
        return m

    def test_with_password_passes_stdin_to_sudo_S(self):
        from workflow.nodes.install.resolver import install_packages

        errors = []
        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=self._ok()) as mock_run:
            install_packages(["some-pkg"], errors, sudo_password="secret")

        self.assertEqual(errors, [])
        call_args = mock_run.call_args
        cmd = call_args.args[0]
        self.assertIn("-S", cmd)
        self.assertIn("-p", cmd)
        self.assertIn("-k", cmd)
        self.assertIn("pacman", cmd)
        self.assertEqual(call_args.kwargs.get("input"), "secret\n")

    def test_without_password_falls_through_to_sudo_n(self):
        from workflow.nodes.install.resolver import install_packages

        errors = []
        calls = []

        def side_effect(cmd, **kwargs):
            calls.append(cmd)
            m = MagicMock()
            m.returncode = 0
            return m

        with patch("workflow.nodes.install.resolver.subprocess.run", side_effect=side_effect):
            install_packages(["some-pkg"], errors, sudo_password="")

        self.assertEqual(errors, [])
        # The call should use sudo -n, not sudo -S (stdin password)
        self.assertTrue(any("-n" in cmd for cmd in calls))
        # No call should have both 'sudo' and '-S' adjacent (the stdin password flag)
        for cmd in calls:
            if "sudo" in cmd:
                sudo_idx = cmd.index("sudo")
                # sudo -S would appear right after 'sudo'; -n should be there instead
                if sudo_idx + 1 < len(cmd):
                    self.assertNotEqual(cmd[sudo_idx + 1], "-S")

    def test_pacman_failure_falls_through_to_yay(self):
        from workflow.nodes.install.resolver import install_packages

        errors = []

        def side_effect(cmd, **kwargs):
            m = MagicMock()
            m.returncode = 1 if "pacman" in cmd else 0
            return m

        with patch("workflow.nodes.install.resolver.subprocess.run", side_effect=side_effect):
            install_packages(["aur-pkg"], errors, sudo_password="")

        self.assertEqual(errors, [])

    def test_all_fail_appends_to_errors(self):
        from workflow.nodes.install.resolver import install_packages

        errors = []
        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=self._fail()):
            install_packages(["missing-pkg"], errors, sudo_password="")

        self.assertIn("missing-pkg", errors)

    def test_pacman_timeout_appends_to_errors(self):
        from workflow.nodes.install.resolver import install_packages

        errors = []
        with patch("workflow.nodes.install.resolver.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd=[], timeout=300)):
            install_packages(["slow-pkg"], errors, sudo_password="secret")

        self.assertIn("slow-pkg", errors)

    def test_yay_timeout_appends_to_errors(self):
        from workflow.nodes.install.resolver import install_packages

        errors = []

        def side_effect(cmd, **kwargs):
            if "pacman" in cmd:
                m = MagicMock()
                m.returncode = 1
                return m
            raise subprocess.TimeoutExpired(cmd=[], timeout=300)

        with patch("workflow.nodes.install.resolver.subprocess.run", side_effect=side_effect):
            install_packages(["aur-pkg"], errors, sudo_password="")

        self.assertIn("aur-pkg", errors)

    def test_multiple_packages_each_attempted(self):
        from workflow.nodes.install.resolver import install_packages

        errors = []
        ok = MagicMock()
        ok.returncode = 0

        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=ok) as mock_run:
            install_packages(["pkg-a", "pkg-b", "pkg-c"], errors, sudo_password="")

        self.assertEqual(errors, [])
        self.assertGreaterEqual(mock_run.call_count, 3)


class CanSudoNoninteractiveTests(unittest.TestCase):
    def test_returns_true_when_sudo_n_succeeds(self):
        from workflow.nodes.install.resolver import can_sudo_noninteractive

        ok = MagicMock()
        ok.returncode = 0
        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=ok):
            self.assertTrue(can_sudo_noninteractive())

    def test_returns_false_when_sudo_n_fails(self):
        from workflow.nodes.install.resolver import can_sudo_noninteractive

        fail = MagicMock()
        fail.returncode = 1
        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=fail):
            self.assertFalse(can_sudo_noninteractive())


class VerifyInstalledTests(unittest.TestCase):
    def test_returns_empty_when_all_installed(self):
        from workflow.nodes.install.resolver import verify_installed

        ok = MagicMock()
        ok.returncode = 0
        with patch("workflow.nodes.install.resolver.subprocess.run", return_value=ok):
            missing = verify_installed(["pkg-a", "pkg-b"])

        self.assertEqual(missing, [])

    def test_returns_missing_packages(self):
        from workflow.nodes.install.resolver import verify_installed

        def side_effect(cmd, **kwargs):
            m = MagicMock()
            m.returncode = 1 if "pkg-b" in cmd else 0
            return m

        with patch("workflow.nodes.install.resolver.subprocess.run", side_effect=side_effect):
            missing = verify_installed(["pkg-a", "pkg-b"])

        self.assertEqual(missing, ["pkg-b"])


if __name__ == "__main__":
    unittest.main()
