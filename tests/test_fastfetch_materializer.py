"""Unit tests for fastfetch materializer compatibility paths."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ricer import materialize_fastfetch  # noqa: E402

_DESIGN = {
    "name": "ghost-blade",
    "palette": {
        "background": "#1a1b26", "foreground": "#c0caf5", "primary": "#7aa2f7",
        "secondary": "#bb9af7", "accent": "#7dcfff", "surface": "#24283b",
        "muted": "#565f89", "danger": "#f7768e", "success": "#9ece6a", "warning": "#e0af68",
    },
    "mood_tags": ["cyber"],
}


class MaterializeFastfetchTests(unittest.TestCase):
    def test_writes_jsonc_and_config_json_symlink(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)

        with patch("materializers.system.HOME", tmp), \
             patch("core.backup.BACKUP_DIR", tmp / ".cache" / "backup"):
            changes = materialize_fastfetch(_DESIGN, backup_ts="ts")

        cfg = tmp / ".config" / "fastfetch" / "config.jsonc"
        compat = tmp / ".config" / "fastfetch" / "config.json"
        self.assertTrue(cfg.exists())
        self.assertTrue(compat.is_symlink())
        self.assertEqual(compat.readlink(), Path("config.jsonc"))
        self.assertTrue([c for c in changes if c.get("action") == "compat-symlink"])

    def test_existing_config_json_is_backed_up_before_symlink(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        compat = tmp / ".config" / "fastfetch" / "config.json"
        compat.parent.mkdir(parents=True)
        compat.write_text('{"old": true}\n', encoding="utf-8")

        with patch("materializers.system.HOME", tmp), \
             patch("core.backup.BACKUP_DIR", tmp / ".cache" / "backup"):
            changes = materialize_fastfetch(_DESIGN, backup_ts="ts")

        symlink = [c for c in changes if c.get("action") == "compat-symlink"][0]
        self.assertTrue(compat.is_symlink())
        self.assertIsNotNone(symlink["backup"])
        self.assertEqual(Path(symlink["backup"]).read_text(encoding="utf-8"), '{"old": true}\n')


if __name__ == "__main__":
    unittest.main()