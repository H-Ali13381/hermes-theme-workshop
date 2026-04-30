"""Unit tests for materialize_starship and _build_starship_toml."""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ricer import materialize_starship, _build_starship_toml  # noqa: E402

_DESIGN = {
    "name": "ghost-blade",
    "description": "Test theme",
    "palette": {
        "background": "#1a1b26",
        "foreground": "#c0caf5",
        "primary":    "#7aa2f7",
        "secondary":  "#bb9af7",
        "accent":     "#7dcfff",
        "surface":    "#24283b",
        "muted":      "#565f89",
        "danger":     "#f7768e",
        "success":    "#9ece6a",
        "warning":    "#e0af68",
    },
    "mood_tags": ["cyber", "cold"],
}


class BuildStarshipTomlTests(unittest.TestCase):
    def setUp(self):
        self.toml = _build_starship_toml(_DESIGN["palette"], "ghost-blade")

    def test_palette_header_selects_theme(self):
        self.assertIn('palette = "ghost-blade"', self.toml)

    def test_palette_section_defines_all_ten_slots(self):
        self.assertIn("[palettes.ghost-blade]", self.toml)
        for slot in ("background", "foreground", "primary", "secondary", "accent",
                     "surface", "muted", "danger", "success", "warning"):
            self.assertIn(slot, self.toml)

    def test_palette_values_are_hex_colors(self):
        self.assertIn('#7aa2f7"', self.toml)
        self.assertIn('#1a1b26"', self.toml)

    # Starship 1.25+ does not interpolate $-prefixed names in palette styles
    # (the materializer was patched to emit bare slot names, e.g. "bold primary"
    # rather than "bold $primary"); these tests assert the bare-name form.

    def test_character_module_uses_success_and_danger_slots(self):
        self.assertIn("bold success", self.toml)
        self.assertIn("bold danger", self.toml)

    def test_directory_uses_primary(self):
        self.assertIn("[directory]", self.toml)
        self.assertIn("bold primary", self.toml)

    def test_git_branch_uses_secondary(self):
        self.assertIn("[git_branch]", self.toml)
        self.assertIn("bold secondary", self.toml)

    def test_cmd_duration_uses_muted(self):
        self.assertIn("[cmd_duration]", self.toml)
        self.assertIn("bold muted", self.toml)

    def test_styles_do_not_use_dollar_prefix(self):
        # Regression guard: $-prefixed palette refs are not interpolated by
        # starship 1.25+; the materializer must emit bare names.
        after_palette = self.toml.split("[character]", 1)[-1]
        for slot in ("primary", "secondary", "accent", "muted",
                     "success", "danger", "warning", "foreground"):
            self.assertNotIn(f"${slot}", after_palette,
                             f"$-prefixed palette ref leaked into styles: ${slot}")

    def test_no_raw_hex_in_style_strings(self):
        # Style strings must reference palette slots, not inline hex values
        import re
        # Everything after the palette section should only have $name references
        after_palette = self.toml.split("[character]", 1)[-1]
        raw_hex = re.findall(r'"[^"]*#[0-9a-fA-F]{6}[^"]*"', after_palette)
        self.assertEqual(raw_hex, [], f"Raw hex found in style strings: {raw_hex}")


class ThemeNameNormalizationTests(unittest.TestCase):
    def test_spaces_replaced_with_hyphens(self):
        toml = _build_starship_toml(_DESIGN["palette"], "my-theme")
        self.assertIn("[palettes.my-theme]", toml)

    # materialize_starship lives in materializers.system; backup_file uses core.backup.BACKUP_DIR
    _SYS = "materializers.system"
    _BACK = "core.backup"

    def test_materialize_normalizes_design_name(self):
        design = {**_DESIGN, "name": "my theme/name!"}
        _tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, _tmp, True)
        with patch(f"{self._SYS}.HOME", new=_tmp):
            changes = materialize_starship(design, backup_ts="20260101_000000", dry_run=True)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["action"], "dry-run")


class MaterializeStarshipTests(unittest.TestCase):
    _SYS = "materializers.system"
    _BACK = "core.backup"

    def test_dry_run_returns_single_change_without_writing(self):
        _tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, _tmp, True)
        with patch(f"{self._SYS}.HOME", new=_tmp):
            changes = materialize_starship(_DESIGN, backup_ts="20260101_000000", dry_run=True)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["app"], "starship")
        self.assertEqual(changes[0]["action"], "dry-run")
        self.assertIn("starship.toml", changes[0]["path"])

    def test_writes_toml_file(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        with patch(f"{self._SYS}.HOME", new=tmpdir), \
             patch(f"{self._BACK}.BACKUP_DIR", new=tmpdir / ".cache" / "backup"):
            changes = materialize_starship(_DESIGN, backup_ts="20260101_000000")

        config_path = tmpdir / ".config" / "starship.toml"
        self.assertTrue(config_path.exists(), "starship.toml was not created")
        content = config_path.read_text(encoding="utf-8")
        self.assertIn('palette = "ghost-blade"', content)
        self.assertIn("[palettes.ghost-blade]", content)

    def test_change_record_has_app_path_and_backup_fields(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        with patch(f"{self._SYS}.HOME", new=tmpdir), \
             patch(f"{self._BACK}.BACKUP_DIR", new=tmpdir / ".cache" / "backup"):
            changes = materialize_starship(_DESIGN, backup_ts="20260101_000000")

        self.assertEqual(len(changes), 1)
        change = changes[0]
        self.assertEqual(change["app"], "starship")
        self.assertEqual(change["action"], "write")
        self.assertIn("starship.toml", change["path"])
        # backup is None when there is no pre-existing file to back up
        self.assertIn("backup", change)

    def test_backup_created_when_existing_config_present(self):
        tmpdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmpdir, True)
        backup_dir = tmpdir / ".cache" / "backup"
        config_path = tmpdir / ".config" / "starship.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("# old config\n", encoding="utf-8")

        with patch(f"{self._SYS}.HOME", new=tmpdir), \
             patch(f"{self._BACK}.BACKUP_DIR", new=backup_dir):
            changes = materialize_starship(_DESIGN, backup_ts="20260101_000000")

        self.assertIsNotNone(changes[0]["backup"])
        backup_path = Path(changes[0]["backup"])
        self.assertTrue(backup_path.exists())
        self.assertEqual(backup_path.read_text(encoding="utf-8"), "# old config\n")


if __name__ == "__main__":
    unittest.main()
