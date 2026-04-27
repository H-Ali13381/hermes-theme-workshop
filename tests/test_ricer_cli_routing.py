"""Regression tests for ricer CLI routing and workflow element aliases."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
RICER_PY = ROOT / "scripts" / "ricer.py"

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
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
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

        fake_stdout = json.dumps({"changes": [{"app": "gtk", "action": "dry-run"}]})

        with patch("workflow.nodes.implement.apply.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = fake_stdout
            run.return_value.stderr = ""

            result = apply_element("gtk_theme", DESIGN, session_dir="")

        self.assertTrue(result["success"], result)
        cmd = run.call_args.args[0]
        self.assertIn("--only=gtk", cmd)
        self.assertNotIn("--only=gtk_theme", cmd)

    def test_apply_element_maps_provider_qualified_elements_to_provider(self):
        from workflow.nodes.implement.apply import apply_element

        with patch("workflow.nodes.implement.apply.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "{}"
            run.return_value.stderr = ""

            result = apply_element("launcher:rofi", DESIGN, session_dir="")

        self.assertTrue(result["success"], result)
        cmd = run.call_args.args[0]
        self.assertIn("--only=rofi", cmd)
        self.assertNotIn("--only=launcher", cmd)
        self.assertFalse(any(arg.startswith("--app=") for arg in cmd))

    def test_apply_element_passes_shell_prompt_starship_to_ricer(self):
        from workflow.nodes.implement.apply import apply_element

        with patch("workflow.nodes.implement.apply.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "{}"
            run.return_value.stderr = ""

            result = apply_element("shell_prompt:starship", DESIGN, session_dir="")

        self.assertNotEqual(result.get("error", ""), "unsupported element: shell_prompt:starship")
        cmd = run.call_args.args[0]
        self.assertIn("--only=starship", cmd)

    def test_apply_element_passes_lock_screen_kde_to_ricer(self):
        from workflow.nodes.implement.apply import apply_element

        with patch("workflow.nodes.implement.apply.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "{}"
            run.return_value.stderr = ""

            result = apply_element("lock_screen:kde", DESIGN, session_dir="")

        self.assertNotEqual(result.get("error", ""), "unsupported element: lock_screen:kde")
        cmd = run.call_args.args[0]
        self.assertIn("--only=kde", cmd)


if __name__ == "__main__":
    unittest.main()
