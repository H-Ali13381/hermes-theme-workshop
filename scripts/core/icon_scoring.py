"""core/icon_scoring.py — SVG colour sampling, palette scoring, and Breeze recolouring.

Extracted from scripts/icon_theme_gen.py to keep that file within the
300-line budget.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

# Breeze CSS class → design palette key mapping.
_BREEZE_CLASS_TO_PALETTE: dict[str, str] = {
    "ColorScheme-Accent":        "primary",
    "ColorScheme-Highlight":     "primary",
    "ColorScheme-PositiveText":  "success",
    "ColorScheme-NegativeText":  "danger",
    "ColorScheme-NeutralText":   "warning",
}

_CSS_COLOR_RE  = re.compile(r"color\s*:\s*(#[0-9a-fA-F]{3,6})", re.IGNORECASE)
_ATTR_COLOR_RE = re.compile(
    r'(?:fill|stroke|stop-color)\s*[=:]\s*"?(#[0-9a-fA-F]{3,6})"?', re.IGNORECASE
)
_CSS_CLASS_BLOCK_RE = re.compile(
    r"\.(ColorScheme-\w+)\s*\{([^}]*)\}", re.DOTALL
)


from core.colors import hex_to_rgb_tuple as _hex_to_rgb


# ---------------------------------------------------------------------------
# Colour math
# ---------------------------------------------------------------------------

def _color_distance(a: str, b: str) -> float:
    """Euclidean RGB distance normalised to [0, 1] (max = sqrt(3·255²) ≈ 441.7)."""
    r1, g1, b1 = _hex_to_rgb(a)
    r2, g2, b2 = _hex_to_rgb(b)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5 / 441.67


# ---------------------------------------------------------------------------
# SVG colour sampling
# ---------------------------------------------------------------------------

def sample_svg_colors(theme_path: Path, max_files: int = 40) -> list[str]:
    """Return a deduplicated list of hex colours found in up to *max_files* SVGs.

    Looks in priority order: apps/48, apps/22, then the whole tree.
    Skips pure black (#000000) and pure white (#ffffff).
    """
    SKIP = {"#000000", "#ffffff", "#000", "#fff"}
    colors: set[str] = set()

    def _iter_svgs() -> Iterator[Path]:
        for sub in ("apps/48", "apps/22"):
            yield from (theme_path / sub).glob("*.svg") if (theme_path / sub).exists() else []
        yield from theme_path.rglob("*.svg")

    count = 0
    for svg in _iter_svgs():
        if count >= max_files:
            break
        try:
            text = svg.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        colors.update(m.group(1).lower() for m in _CSS_COLOR_RE.finditer(text))
        colors.update(m.group(1).lower() for m in _ATTR_COLOR_RE.finditer(text))
        count += 1

    return [c for c in colors if c not in SKIP]


# ---------------------------------------------------------------------------
# Palette scoring
# ---------------------------------------------------------------------------

def score_theme_against_palette(theme_path: Path, palette: dict) -> float:
    """Return a match score in [0.0, 1.0] — lower means better colour match."""
    theme_colors = sample_svg_colors(theme_path)
    if not theme_colors:
        return 1.0

    palette_colors = [v for v in palette.values() if isinstance(v, str) and v.startswith("#")]
    if not palette_colors:
        return 1.0

    total = 0.0
    for pc in palette_colors:
        total += min(_color_distance(pc, tc) for tc in theme_colors)
    return total / len(palette_colors)


# ---------------------------------------------------------------------------
# SVG recolouring (Breeze ColorScheme CSS classes)
# ---------------------------------------------------------------------------

def recolor_svg(svg_text: str, palette: dict) -> str:
    """Replace Breeze ColorScheme CSS class colour values with palette colours."""
    def _replace(m: re.Match) -> str:
        cls = m.group(1)
        block = m.group(2)
        palette_key = _BREEZE_CLASS_TO_PALETTE.get(cls)
        if not palette_key:
            return m.group(0)
        new_color = palette.get(palette_key, "")
        if not new_color:
            return m.group(0)
        new_block = re.sub(
            r"(color\s*:\s*)#[0-9a-fA-F]{3,6}",
            rf"\g<1>{new_color}",
            block,
        )
        return f".{cls} {{{new_block}}}"

    return _CSS_CLASS_BLOCK_RE.sub(_replace, svg_text)


def _recolor_size_dir(src: Path, dst: Path, palette: dict) -> int:
    """Copy SVGs from *src* to *dst*, recolouring each one.  Returns file count."""
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for svg in src.glob("*.svg"):
        try:
            original = svg.read_text(encoding="utf-8", errors="replace")
            recolored = recolor_svg(original, palette)
            (dst / svg.name).write_text(recolored, encoding="utf-8")
            count += 1
        except OSError:
            continue
    return count
