"""Tests for scripts/palette_extractor.py.

Covers: determinism, slot completeness, background/foreground contrast,
slot uniqueness, and semantic-hue assignment for danger/success/warning.

Fixtures are synthesized in-memory (no committed binaries). They target the
three failure modes the extractor's fallback cascade must handle:

- `vibrant`     — colorful image that covers all 6 ricemood buckets.
- `monochrome`  — greyscale gradient, no vivid swatches (exercises fallbacks
  for primary / accent / semantic-hue slots).
- `dark_scenic` — 95% dark pixels + one bright accent cluster (exercises
  MAXCOVERAGE accent-capture vs. MEDIANCUT frequency-bias).
"""

from __future__ import annotations

import colorsys
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "palette_extractor.py"


def load_module():
    spec = importlib.util.spec_from_file_location("palette_extractor", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hex_to_hls(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def hex_to_yiq_luma(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000


def hue_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ---------------------------------------------------------------------------
# Fixture generation — synthesize test images in a tmpdir
# ---------------------------------------------------------------------------

def make_vibrant(path: Path, size: int = 256) -> None:
    """Image covering all 6 ricemood buckets: dark-desat background, mid-vibrant,
    light-vibrant, dark-vibrant stripes plus light-muted and muted bands."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (size, size), (18, 20, 22))          # DarkMuted
    draw = ImageDraw.Draw(img)
    bands = [
        ((40, 180, 220), (0, 0, size, size // 6)),              # LightVibrant (cyan-ish)
        ((220, 60, 70), (0, size // 6, size, 2 * size // 6)),   # Vibrant (red)
        ((120, 35, 150), (0, 2 * size // 6, size, 3 * size // 6)),  # DarkVibrant (deep purple)
        ((200, 200, 210), (0, 3 * size // 6, size, 4 * size // 6)), # LightMuted
        ((120, 120, 125), (0, 4 * size // 6, size, 5 * size // 6)), # Muted
        # Bottom sixth retains DarkMuted bg
    ]
    for color, rect in bands:
        draw.rectangle(rect, fill=color)
    img.save(path)


def make_monochrome(path: Path, size: int = 256) -> None:
    """Grey gradient — no vivid swatches; forces fallback cascade to kick in."""
    from PIL import Image

    img = Image.new("RGB", (size, size))
    pixels = img.load()
    for y in range(size):
        v = int(20 + (y / size) * 215)  # 20 → 235
        for x in range(size):
            pixels[x, y] = (v, v, v)
    img.save(path)


def make_dark_scenic(path: Path, size: int = 256) -> None:
    """Near-black with one small bright emerald accent — tests that MAXCOVERAGE
    captures narrow accent clusters that pure frequency counting would miss."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (size, size), (8, 9, 14))  # deep navy-black
    draw = ImageDraw.Draw(img)
    # 5% of image area: one bright emerald splash
    s = size // 5
    draw.rectangle((size - s - 8, size - s - 8, size - 8, size - 8),
                   fill=(60, 210, 140))
    img.save(path)


class PaletteExtractorTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("Pillow not installed; palette extractor tests require it")

        cls.mod = load_module()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.fixtures = Path(cls.tmp.name)
        cls.vibrant_path = cls.fixtures / "vibrant.png"
        cls.monochrome_path = cls.fixtures / "monochrome.png"
        cls.dark_scenic_path = cls.fixtures / "dark_scenic.png"
        make_vibrant(cls.vibrant_path)
        make_monochrome(cls.monochrome_path)
        make_dark_scenic(cls.dark_scenic_path)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _all_fixtures(self):
        return [self.vibrant_path, self.monochrome_path, self.dark_scenic_path]

    # --- determinism ---

    def test_determinism_same_input_same_output(self):
        for path in self._all_fixtures():
            a = self.mod.extract_palette(str(path))
            b = self.mod.extract_palette(str(path))
            self.assertEqual(a, b, f"non-deterministic output for {path.name}")

    # --- completeness ---

    def test_all_ten_slots_present_and_valid_hex(self):
        required = {
            "background", "foreground", "primary", "secondary", "accent",
            "surface", "muted", "danger", "success", "warning",
        }
        for path in self._all_fixtures():
            with self.subTest(image=path.name):
                design = self.mod.extract_palette(str(path))
                palette = design["palette"]
                self.assertEqual(set(palette.keys()), required)
                for slot, value in palette.items():
                    self.assertRegex(
                        value, r"^#[0-9a-f]{6}$",
                        f"{path.name}: slot {slot!r} is not a valid hex ({value!r})",
                    )

    # --- contrast invariant ---

    def test_background_foreground_contrast(self):
        """YIQ luma delta ≥ 128 between background and foreground (~AA contrast)."""
        for path in self._all_fixtures():
            with self.subTest(image=path.name):
                palette = self.mod.extract_palette(str(path))["palette"]
                delta = abs(
                    hex_to_yiq_luma(palette["background"])
                    - hex_to_yiq_luma(palette["foreground"])
                )
                self.assertGreaterEqual(
                    delta, 128,
                    f"{path.name}: bg/fg contrast too low (Δ={delta:.1f})",
                )

    # --- uniqueness ---

    def test_slot_uniqueness(self):
        """No two slots share a hex value (avoids ANSI / widget collisions)."""
        for path in self._all_fixtures():
            with self.subTest(image=path.name):
                palette = self.mod.extract_palette(str(path))["palette"]
                values = [v.lower() for v in palette.values()]
                self.assertEqual(
                    len(values), len(set(values)),
                    f"{path.name}: duplicate hex values in palette: {palette}",
                )

    # --- semantic hue slots ---

    def test_semantic_hue_slots_are_in_role_range(self):
        """danger near red, success near green, warning near amber — within 60°."""
        for path in self._all_fixtures():
            with self.subTest(image=path.name):
                palette = self.mod.extract_palette(str(path))["palette"]
                danger_hue = hex_to_hls(palette["danger"])[0] * 360
                success_hue = hex_to_hls(palette["success"])[0] * 360
                warning_hue = hex_to_hls(palette["warning"])[0] * 360

                self.assertLessEqual(
                    hue_distance(danger_hue, 0), 60,
                    f"{path.name}: danger hue {danger_hue:.0f}° not near red"
                )
                self.assertLessEqual(
                    hue_distance(success_hue, 120), 60,
                    f"{path.name}: success hue {success_hue:.0f}° not near green"
                )
                self.assertLessEqual(
                    hue_distance(warning_hue, 45), 60,
                    f"{path.name}: warning hue {warning_hue:.0f}° not near amber"
                )

    # --- classification internals ---

    def test_classify_swatch_thresholds(self):
        """Sanity-check classify against the documented thresholds."""
        classify = self.mod._classify_swatch
        self.assertEqual(classify((220, 30, 30)), "Vibrant")            # high S, mid L
        self.assertEqual(classify((230, 225, 220)), "LightMuted")       # low S, very high L
        self.assertEqual(classify((15, 15, 15)), "DarkMuted")           # low S, very low L
        self.assertEqual(classify((120, 115, 118)), "Muted")            # low S, mid L
        self.assertEqual(classify((100, 15, 15)), "DarkVibrant")        # high S, low L
        self.assertEqual(classify((255, 200, 200)), "LightVibrant")     # high S, high L

    def test_dark_scenic_captures_accent(self):
        """MAXCOVERAGE should surface the small emerald cluster in the
        dark_scenic fixture — accent or success should be green-ish."""
        palette = self.mod.extract_palette(str(self.dark_scenic_path))["palette"]
        green_hues = []
        for slot in ("accent", "primary", "success", "secondary"):
            hue = hex_to_hls(palette[slot])[0] * 360
            if hue_distance(hue, 140) < 40:  # loose green band
                green_hues.append((slot, hue))
        self.assertTrue(
            green_hues,
            f"dark_scenic: expected a green-ish slot from the emerald accent, got {palette}",
        )


class SelectIconThemeTests(unittest.TestCase):
    """select_icon_theme: picks from installed themes, never returns nonexistent names."""

    module = load_module()

    def _fake_dir(self, themes: dict[str, list[str]]) -> Path:
        """Build a tmp icon dir. themes maps name → list of category subdirs under 48x48/."""
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        for name, cats in themes.items():
            sub = d / name
            size_dir = sub / "48x48"
            size_dir.mkdir(parents=True)
            (sub / "index.theme").write_text(f"[Icon Theme]\nName={name}\n", encoding="utf-8")
            for cat in cats:
                (size_dir / cat).mkdir()
        return d

    def test_no_themes_returns_hicolor(self):
        d = Path(self._fake_dir({}))
        result = self.module.select_icon_theme({"background": "#1e1e2e"}, search_dirs=[d])
        self.assertEqual(result, "hicolor")

    def test_prefers_papirus_dark_for_dark_palette(self):
        d = self._fake_dir({
            "Papirus": ["apps", "places"],
            "Papirus-Dark": ["apps", "places"],
            "breeze": ["apps", "places"],
        })
        result = self.module.select_icon_theme({"background": "#1e1e2e"}, search_dirs=[d])
        self.assertEqual(result, "Papirus-Dark")

    def test_prefers_papirus_for_light_palette(self):
        d = self._fake_dir({
            "Papirus": ["apps", "places"],
            "Papirus-Dark": ["apps", "places"],
        })
        result = self.module.select_icon_theme({"background": "#eff1f5"}, search_dirs=[d])
        self.assertEqual(result, "Papirus")

    def test_cursor_only_themes_excluded(self):
        d = self._fake_dir({
            "catppuccin-cursors": ["cursors"],   # cursor-only, no apps/places
            "breeze": ["apps", "places"],
        })
        result = self.module.select_icon_theme({"background": "#1e1e2e"}, search_dirs=[d])
        self.assertEqual(result, "breeze")

    def test_falls_back_to_installed_when_no_pref_matches(self):
        d = self._fake_dir({
            "my-custom-dark-theme": ["apps"],
        })
        result = self.module.select_icon_theme({"background": "#1e1e2e"}, search_dirs=[d])
        self.assertEqual(result, "my-custom-dark-theme")

    def test_skips_hicolor_locolor_default(self):
        d = self._fake_dir({
            "hicolor": ["apps"],
            "locolor": ["apps"],
            "default": ["apps"],
            "Adwaita": ["apps", "places"],
        })
        result = self.module.select_icon_theme({"background": "#1e1e2e"}, search_dirs=[d])
        self.assertEqual(result, "Adwaita")

    def test_installed_icon_themes_filters_cursor_only(self):
        d = self._fake_dir({
            "my-cursors": ["cursors"],
            "Papirus-Dark": ["apps", "places"],
        })
        themes = self.module._installed_icon_themes(search_dirs=[d])
        self.assertIn("Papirus-Dark", themes)
        self.assertNotIn("my-cursors", themes)


if __name__ == "__main__":
    unittest.main()
