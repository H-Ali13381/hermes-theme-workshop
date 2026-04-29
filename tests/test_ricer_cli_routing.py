"""Regression tests for ricer CLI routing and workflow element aliases."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
RICER_PY = ROOT / "scripts" / "ricer.py"
SESSION_IO_PY = ROOT / "scripts" / "core" / "session_io.py"


def _load_session_io():
    spec = importlib.util.spec_from_file_location("session_io", SESSION_IO_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


session_io = _load_session_io()

DESIGN = {
    "name": "routing-test",
    "description": "Minimal test design",
    "palette": {
        "background": "#000000",
        "foreground": "#ffffff",
        "primary": "#ff0000",
        "secondary": "#00ff00",
        "accent": "#0000ff",
        "surface": "#111111",
        "muted": "#222222",
        "danger": "#cc0000",
        "success": "#00cc00",
        "warning": "#cccc00",
    },
    "kvantum_theme": "KvDark",
    "plasma_theme": "default",
    "cursor_theme": "default",
    "icon_theme": "Papirus-Dark",
    "gtk_theme": "Adwaita-dark",
    "mood_tags": ["test"],
}


def run_ricer(*args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as tf:
        json.dump(DESIGN, tf)
        design_path = tf.name
    try:
        return subprocess.run(
            [sys.executable, str(RICER_PY), "apply", "--design", design_path, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    finally:
        Path(design_path).unlink(missing_ok=True)


class RicerCliRoutingTests(unittest.TestCase):
    def test_apply_requires_explicit_single_materializer_target(self):
        r = run_ricer("--dry-run")

        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("apply requires --only or --app", r.stderr)
        self.assertEqual("", r.stdout.strip())

    def test_invalid_only_fails_closed_instead_of_applying_all_apps(self):
        r = run_ricer("--only=gtk_theme", "--dry-run")

        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("Unknown materializer", r.stderr)
        self.assertEqual("", r.stdout.strip())

    def test_unknown_app_fails_closed_instead_of_falling_back_to_all_apps(self):
        r = run_ricer("--only=not_a_real_materializer", "--dry-run")

        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("Unknown materializer", r.stderr)
        self.assertEqual("", r.stdout.strip())

    def test_apply_element_maps_workflow_gtk_theme_to_gtk_materializer(self):
        from workflow.nodes.implement.apply import apply_element

        fake_manifest = {"changes": [{"app": "gtk", "action": "dry-run"}]}

        with patch("workflow.nodes.implement.apply.discover_apps", return_value={"gtk": "/usr/bin/gtk3-demo"}), \
             patch("workflow.nodes.implement.apply.materialize", return_value=fake_manifest) as mat:
            result = apply_element("gtk_theme", DESIGN, session_dir="")

        self.assertTrue(result["success"], result)
        called_apps = mat.call_args.kwargs.get("apps") or mat.call_args.args[1]
        self.assertIn("gtk", called_apps)
        self.assertNotIn("gtk_theme", called_apps)

    def test_apply_element_maps_provider_qualified_elements_to_provider(self):
        from workflow.nodes.implement.apply import apply_element

        with patch("workflow.nodes.implement.apply.discover_apps", return_value={"rofi": "/usr/bin/rofi"}), \
             patch("workflow.nodes.implement.apply.materialize", return_value={}) as mat:
            result = apply_element("launcher:rofi", DESIGN, session_dir="")

        self.assertTrue(result["success"], result)
        called_apps = mat.call_args.kwargs.get("apps") or mat.call_args.args[1]
        self.assertIn("rofi", called_apps)
        self.assertNotIn("launcher", called_apps)

    def test_apply_element_passes_shell_prompt_starship_to_ricer(self):
        from workflow.nodes.implement.apply import apply_element

        with patch("workflow.nodes.implement.apply.discover_apps", return_value={"starship": "/usr/bin/starship"}), \
             patch("workflow.nodes.implement.apply.materialize", return_value={}) as mat:
            result = apply_element("shell_prompt:starship", DESIGN, session_dir="")

        self.assertNotEqual(result.get("error", ""), "unsupported element: shell_prompt:starship")
        called_apps = mat.call_args.kwargs.get("apps") or mat.call_args.args[1]
        self.assertIn("starship", called_apps)

    def test_apply_element_passes_lock_screen_kde_to_ricer(self):
        from workflow.nodes.implement.apply import apply_element

        with patch("workflow.nodes.implement.apply.discover_apps", return_value={"kde_lockscreen": True}), \
             patch("workflow.nodes.implement.apply.materialize", return_value={}) as mat:
            result = apply_element("lock_screen:kde", DESIGN, session_dir="")

        self.assertNotEqual(result.get("error", ""), "unsupported element: lock_screen:kde")
        called_apps = mat.call_args.kwargs.get("apps") or mat.call_args.args[1]
        self.assertIn("kde_lockscreen", called_apps)
        self.assertNotIn("kde", called_apps)


class DesignFileLoaderTests(unittest.TestCase):
    """Unit tests for load_design_file — JSON and YAML support."""

    _SAMPLE = {"name": "yaml-test", "palette": {"background": "#000000"}}

    def test_loads_json_design(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
            json.dump(self._SAMPLE, tf)
            path = tf.name
        try:
            result = session_io.load_design_file(path)
            self.assertEqual(result["name"], "yaml-test")
            self.assertEqual(result["palette"]["background"], "#000000")
        finally:
            Path(path).unlink(missing_ok=True)

    def test_loads_yaml_design(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", encoding="utf-8", delete=False) as tf:
            tf.write("name: yaml-test\npalette:\n  background: '#000000'\n")
            path = tf.name
        try:
            result = session_io.load_design_file(path)
            self.assertEqual(result["name"], "yaml-test")
            self.assertEqual(result["palette"]["background"], "#000000")
        finally:
            Path(path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
