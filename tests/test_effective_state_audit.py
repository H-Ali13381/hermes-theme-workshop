"""Tests for read-only cleanup effective-state auditing."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from workflow.nodes.cleanup.effective_state import audit_effective_state


class EffectiveStateAuditTests(unittest.TestCase):
    def test_non_kde_state_is_empty(self):
        self.assertEqual(audit_effective_state({"device_profile": {"wm": "gnome"}}), {})

    def test_kde_effective_state_reads_active_configs(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / ".config").mkdir(parents=True)
        (tmp / ".config" / "kdeglobals").write_text(
            "[General]\nColorScheme=hermes-moss\ncursorTheme=Bibata\n",
            encoding="utf-8",
        )
        (tmp / ".config" / "kcminputrc").write_text(
            "[Mouse]\ncursorTheme=Bibata\n",
            encoding="utf-8",
        )
        (tmp / ".config" / "plasma-org.kde.plasma.desktop-appletsrc").write_text(
            "[Containments][1][Wallpaper][org.kde.image][General]\nImage=file:///wall.png\n",
            encoding="utf-8",
        )
        (tmp / ".config" / "konsolerc").write_text(
            "[Desktop Entry]\nDefaultProfile=linux-ricing.profile\n",
            encoding="utf-8",
        )
        konsole = tmp / ".local" / "share" / "konsole"
        konsole.mkdir(parents=True)
        (konsole / "linux-ricing.profile").write_text(
            "[Appearance]\nColorScheme=hermes-moss\n",
            encoding="utf-8",
        )
        kitty = tmp / ".config" / "kitty"
        kitty.mkdir(parents=True)
        (kitty / "kitty.conf").write_text("include theme.conf\n", encoding="utf-8")
        (kitty / "theme.conf").write_text("background #0f1514\nforeground #d1dbc8\n", encoding="utf-8")
        ff = tmp / ".config" / "fastfetch"
        ff.mkdir(parents=True)
        (ff / "config.jsonc").write_text("{}\n", encoding="utf-8")
        (ff / "config.json").symlink_to(Path("config.jsonc"))

        def fake_run(cmd, **_kwargs):
            result = MagicMock()
            result.returncode = 0 if cmd[-1] in {"plasmashell", "kwin_wayland"} else 1
            result.stdout = "111\n" if result.returncode == 0 else ""
            return result

        with patch("workflow.nodes.cleanup.effective_state.Path.home", return_value=tmp), \
             patch("workflow.nodes.cleanup.effective_state.subprocess.run", side_effect=fake_run):
            result = audit_effective_state({"device_profile": {"wm": "kde"}})

        self.assertEqual(result["kde"]["colorscheme"], "hermes-moss")
        self.assertEqual(result["kde"]["cursor_kcminputrc"], "Bibata")
        self.assertEqual(result["konsole"]["default_profile"], "linux-ricing.profile")
        self.assertEqual(result["konsole"]["colorscheme"], "hermes-moss")
        self.assertEqual(result["kitty"]["effective_palette"]["background"], "#0f1514")
        self.assertTrue(result["fastfetch"]["compat_ok"])
        self.assertTrue(result["processes"]["plasmashell"]["running"])
        self.assertTrue(result["processes"]["kwin_wayland"]["running"])
        self.assertFalse(result["processes"]["kwin_x11"]["running"])


if __name__ == "__main__":
    unittest.main()