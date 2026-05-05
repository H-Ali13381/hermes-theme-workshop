from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow.nodes.cleanup import kde_finalize


class KdeFinalizeWallpaperTests(unittest.TestCase):
    def test_resolves_nested_chrome_wallpaper_path(self):
        design = {
            "chrome_strategy": {
                "wallpaper_path": "/home/$USER/Pictures/EmberwardReliquary/wall.png",
            }
        }
        self.assertEqual(
            kde_finalize._resolve_wallpaper_path(design),
            "/home/$USER/Pictures/EmberwardReliquary/wall.png",
        )

    def test_resolves_wallpaper_from_implementation_targets(self):
        design = {
            "chrome_strategy": {
                "implementation_targets": [
                    "widgets:eww:/home/$USER/.config/eww/theme/toolbar.yuck",
                    "wallpaper:local_artifact:/home/$USER/Pictures/Theme/theme-wallpaper.png",
                ]
            }
        }
        self.assertEqual(
            kde_finalize._resolve_wallpaper_path(design),
            "/home/$USER/Pictures/Theme/theme-wallpaper.png",
        )

    def test_resolves_wallpaper_directory_from_visual_element_plan(self):
        design = {
            "name": "Iron Chapel Rest Menu",
            "visual_element_plan": [{
                "desktop_element": "wallpaper",
                "implementation_tool": "look_and_feel:kde",
                "config_targets": ["~/.local/share/wallpapers/iron-chapel-rest-menu/"],
            }],
        }
        self.assertEqual(
            kde_finalize._resolve_wallpaper_path(design),
            "~/.local/share/wallpapers/iron-chapel-rest-menu/wallpaper.png",
        )

    def test_resolves_wallpaper_fallback_from_visual_element_plan(self):
        design = {
            "theme_name": "Ash Gate",
            "visual_element_plan": [{
                "desktop_element": "wallpaper",
                "implementation_tool": "look_and_feel:kde",
                "config_targets": ["~/.config/plasma-org.kde.plasma.desktop-appletsrc"],
            }],
        }
        self.assertEqual(
            kde_finalize._resolve_wallpaper_path(design),
            "~/.local/share/wallpapers/ash-gate/wallpaper.png",
        )

    def test_apply_wallpaper_refuses_visualize_image_url_when_local_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            wallpaper = tmp_path / "wallpaper.png"
            state = {
                "device_profile": {"wm": "kde"},
                "design": {"chrome_strategy": {"wallpaper_path": str(wallpaper)}},
                "impl_log": [],
                "visualize_image_url": "https://example.invalid/generated.png",
            }

            reloaded, errors = [], []
            with patch("workflow.nodes.cleanup.kde_finalize.shutil.which", return_value="/usr/bin/plasma-apply-wallpaperimage"), \
                 patch("workflow.nodes.cleanup.kde_finalize._check_plasmashell"), \
                 patch("workflow.nodes.cleanup.kde_finalize._run") as run:
                actions = kde_finalize.finalize_kde(state, reloaded, errors)

            statuses = {(a["action"], a["status"]) for a in actions}
            self.assertNotIn(("wallpaper-download", "ok"), statuses)
            self.assertIn(("wallpaper-apply", "skipped"), statuses)
            self.assertFalse(wallpaper.exists())
            self.assertNotIn("kde-wallpaper", reloaded)
            run.assert_not_called()
            self.assertEqual(
                errors,
                [f"wallpaper artifact missing for {wallpaper}; refusing desktop preview URL as wallpaper"],
            )

    def test_visual_plan_wallpaper_generates_artifact_instead_of_downloading_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            wallpaper = Path(tmp) / "visual-plan-wallpaper.png"
            state = {
                "device_profile": {"wm": "kde"},
                "design": {
                    "palette": {"background": "#050607", "foreground": "#d7c9a7", "accent": "#d78331"},
                    "visual_element_plan": [{
                        "desktop_element": "wallpaper",
                        "implementation_tool": "look_and_feel:kde",
                        "config_targets": [str(wallpaper)],
                    }],
                },
                "impl_log": [],
                "visualize_image_url": "https://example.invalid/desktop-preview.png",
            }
            completed = subprocess.CompletedProcess(["plasma-apply-wallpaperimage", str(wallpaper)], 0, "", "")

            def generate_wallpaper(path, design, actions, errors):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"generated wallpaper" * 80)
                actions.append({
                    "app": "kde_finalize",
                    "action": "wallpaper-generate",
                    "status": "ok",
                    "path": str(path),
                    "reason": "visual_element_plan wallpaper artifact",
                })

            reloaded, errors = [], []
            with patch("workflow.nodes.cleanup.kde_finalize.shutil.which", return_value="/usr/bin/plasma-apply-wallpaperimage"), \
                 patch("workflow.nodes.cleanup.kde_finalize._generate_atmospheric_wallpaper", side_effect=generate_wallpaper), \
                 patch("workflow.nodes.cleanup.kde_finalize._check_plasmashell"), \
                 patch("workflow.nodes.cleanup.kde_finalize._run", return_value=completed):
                actions = kde_finalize.finalize_kde(state, reloaded, errors)

            statuses = {(a["action"], a["status"]) for a in actions}
            self.assertIn(("wallpaper-generate", "ok"), statuses)
            self.assertIn(("wallpaper-apply", "ok"), statuses)
            self.assertNotIn(("wallpaper-download", "ok"), statuses)
            self.assertTrue(wallpaper.exists())
            self.assertGreater(wallpaper.stat().st_size, 1000)
            self.assertEqual(errors, [])

    def test_generated_wallpaper_failure_skips_preview_url_without_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            wallpaper = Path(tmp) / "visual-plan-wallpaper.png"
            state = {
                "device_profile": {"wm": "kde"},
                "design": {
                    "visual_element_plan": [{
                        "desktop_element": "wallpaper",
                        "implementation_tool": "look_and_feel:kde",
                        "config_targets": [str(wallpaper)],
                    }],
                },
                "impl_log": [],
                "visualize_image_url": "https://example.invalid/desktop-preview.png",
            }

            def fail_generate(path, design, actions, errors):
                errors.append(f"wallpaper artifact generation failed for {path}: boom")
                actions.append({
                    "app": "kde_finalize",
                    "action": "wallpaper-generate",
                    "status": "error",
                    "path": str(path),
                    "error": "boom",
                })

            reloaded, errors = [], []
            with patch("workflow.nodes.cleanup.kde_finalize.shutil.which", return_value="/usr/bin/plasma-apply-wallpaperimage"), \
                 patch("workflow.nodes.cleanup.kde_finalize._generate_atmospheric_wallpaper", side_effect=fail_generate), \
                 patch("workflow.nodes.cleanup.kde_finalize._check_plasmashell"), \
                 patch("workflow.nodes.cleanup.kde_finalize._run") as run:
                actions = kde_finalize.finalize_kde(state, reloaded, errors)

            statuses = {(a["action"], a["status"]) for a in actions}
            self.assertIn(("wallpaper-generate", "error"), statuses)
            self.assertIn(("wallpaper-apply", "skipped"), statuses)
            self.assertFalse(wallpaper.exists())
            self.assertNotIn("kde-wallpaper", reloaded)
            run.assert_not_called()
            self.assertEqual(
                errors,
                [
                    f"wallpaper artifact generation failed for {wallpaper}: boom",
                    f"wallpaper artifact missing for {wallpaper}; refusing desktop preview URL as wallpaper",
                ],
            )


if __name__ == "__main__":
    unittest.main()
