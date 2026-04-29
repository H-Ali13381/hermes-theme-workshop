"""core/palette_engine.py — Image quantisation, swatch classification and slot assignment.

Extracted from scripts/palette_extractor.py to keep that file within the
300-line budget.  Depends only on core.palette_primitives and stdlib.
"""
from __future__ import annotations

import colorsys

from core.palette_primitives import (
    _hex_to_rgb, _rgb_to_hex, _rgb_to_hls, _hex_to_hls,
    _yiq_luma, _rotate_hue, _adjust_lightness, _blend_hex,
)


# --- Pillow loading + quantization ---

def _load_and_normalize(image_path: str, max_side: int = 400):
    """Open image, composite any alpha channel over neutral gray, downsample."""
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError(
            "palette_extractor requires Pillow. Install with: pip install pillow"
        ) from e

    with Image.open(image_path) as _raw:
        if _raw.mode in ("RGBA", "LA") or (_raw.mode == "P" and "transparency" in _raw.info):
            rgba = _raw.convert("RGBA")
            bg = Image.new("RGBA", rgba.size, (128, 128, 128, 255))
            img = Image.alpha_composite(bg, rgba).convert("RGB")
        else:
            img = _raw.convert("RGB")

    img.thumbnail((max_side, max_side))
    return img


def _quantize_swatches(img, n: int = 12) -> list[tuple[tuple[int, int, int], int]]:
    """Quantize image to ≤ n swatches. Returns [(rgb, pixel_count), ...] sorted
    by (-count, hex) for determinism."""
    from PIL import Image

    try:
        pal_img = img.quantize(colors=n, method=Image.Quantize.MAXCOVERAGE, kmeans=0)
    except (ValueError, OSError):
        pal_img = img.quantize(colors=n, method=Image.Quantize.MEDIANCUT, kmeans=0)

    raw_palette = pal_img.getpalette() or []
    color_counts = pal_img.getcolors(maxcolors=n * 4) or []

    swatches = []
    for count, idx in color_counts:
        base = idx * 3
        if base + 2 >= len(raw_palette):
            continue
        rgb = (raw_palette[base], raw_palette[base + 1], raw_palette[base + 2])
        swatches.append((rgb, count))

    swatches.sort(key=lambda x: (-x[1], _rgb_to_hex(*x[0])))
    return swatches


# --- Classification ---

_SAT_THRESHOLD = 0.4
_LIGHT_LOW = 0.25
_LIGHT_HIGH = 0.75

_CATEGORIES = (
    "Vibrant", "LightVibrant", "DarkVibrant",
    "Muted", "LightMuted", "DarkMuted",
)


def _classify_swatch(rgb: tuple[int, int, int]) -> str:
    h, l, s = _rgb_to_hls(rgb)
    if s > _SAT_THRESHOLD:
        if l >= _LIGHT_HIGH:
            return "LightVibrant"
        if l <= _LIGHT_LOW:
            return "DarkVibrant"
        return "Vibrant"
    if l >= _LIGHT_HIGH:
        return "LightMuted"
    if l <= _LIGHT_LOW:
        return "DarkMuted"
    return "Muted"


# --- Slot assignment helpers ---

def _hue_degrees(rgb: tuple[int, int, int]) -> float:
    return _rgb_to_hls(rgb)[0] * 360


def _hue_distance(a: float, b: float) -> float:
    """Circular distance between two hue angles (0-360)."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def _find_hue_match(
    swatches: list[tuple[tuple[int, int, int], int]],
    target_hue: float,
    tolerance_deg: float,
    min_saturation: float = 0.3,
) -> tuple[int, int, int] | None:
    candidates = []
    for rgb, count in swatches:
        _, _, s = _rgb_to_hls(rgb)
        if s < min_saturation:
            continue
        dist = _hue_distance(_hue_degrees(rgb), target_hue)
        if dist <= tolerance_deg:
            candidates.append((dist, -s, _rgb_to_hex(*rgb), rgb))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][3]


def _assign_slots(
    swatches: list[tuple[tuple[int, int, int], int]],
) -> dict[str, str]:
    """Map 6 ricemood buckets → 10 semantic slots with documented fallbacks."""
    buckets: dict[str, list] = {c: [] for c in _CATEGORIES}
    for rgb, count in swatches:
        buckets[_classify_swatch(rgb)].append((rgb, count))

    def darkest(bucket):
        return _pick_extreme(bucket, lambda rgb: -_rgb_to_hls(rgb)[1])

    def lightest(bucket):
        return _pick_extreme(bucket, lambda rgb: _rgb_to_hls(rgb)[1])

    def most_chromatic(bucket):
        return _pick_extreme(bucket, lambda rgb: _rgb_to_hls(rgb)[2])

    bg_rgb = darkest(buckets["DarkMuted"])
    if bg_rgb:
        background = _rgb_to_hex(*bg_rgb)
    else:
        dv = darkest(buckets["DarkVibrant"])
        background = _adjust_lightness(_rgb_to_hex(*dv), 0.6) if dv else "#0a0a0a"

    fg_rgb = lightest(buckets["LightMuted"])
    if fg_rgb:
        foreground = _rgb_to_hex(*fg_rgb)
    else:
        lv = lightest(buckets["LightVibrant"])
        if lv:
            foreground = _rgb_to_hex(*lv)
        else:
            foreground = "#f0f0f0" if _yiq_luma(background) < 128 else "#101010"

    pr_rgb = most_chromatic(buckets["Vibrant"])
    if not pr_rgb:
        pr_rgb = most_chromatic(buckets["LightVibrant"])
    if not pr_rgb:
        pr_rgb = most_chromatic(buckets["DarkVibrant"])
    primary = _rgb_to_hex(*pr_rgb) if pr_rgb else _rotate_hue(foreground, 210)

    sec_rgb = most_chromatic(buckets["DarkVibrant"])
    if sec_rgb:
        secondary = _rgb_to_hex(*sec_rgb)
    elif buckets["Vibrant"]:
        v = most_chromatic(buckets["Vibrant"])
        secondary = _adjust_lightness(_rgb_to_hex(*v), 0.6)
    else:
        secondary = _adjust_lightness(primary, 0.65)

    primary_h = _hue_degrees(_hex_to_rgb(primary))
    accent = None
    lv_sorted = sorted(buckets["LightVibrant"], key=lambda s: (-_rgb_to_hls(s[0])[2], _rgb_to_hex(*s[0])))
    for rgb, _ in lv_sorted:
        if _hue_distance(_hue_degrees(rgb), primary_h) >= 30:
            accent = _rgb_to_hex(*rgb)
            break
    if accent is None and lv_sorted:
        accent = _rotate_hue(_rgb_to_hex(*lv_sorted[0][0]), 20)
    if accent is None:
        accent = _rotate_hue(primary, 30)

    sf_rgb = most_chromatic(buckets["Muted"])
    surface = _rgb_to_hex(*sf_rgb) if sf_rgb else _blend_hex(background, "#808080", 0.20)

    dm = darkest(buckets["DarkMuted"])
    if dm:
        muted = _adjust_lightness(_rgb_to_hex(*dm), 1.3)
        if muted.lower() == _rgb_to_hex(*dm).lower():
            muted = _blend_hex(_rgb_to_hex(*dm), "#808080", 0.25)
    else:
        muted = _blend_hex(background, "#808080", 0.12)

    all_saturated = [(rgb, c) for rgb, c in swatches if _rgb_to_hls(rgb)[2] >= 0.45]
    primary_l = _rgb_to_hls(_hex_to_rgb(primary))[1]

    def semantic(target_hue: float, tolerance: float, synth_hex: str) -> str:
        match = _find_hue_match(all_saturated, target_hue, tolerance)
        if match and _rgb_to_hls(match)[1] >= 0.25:
            return _rgb_to_hex(*match)
        synth_h, _, synth_s = _hex_to_hls(synth_hex)
        nr, ng, nb = colorsys.hls_to_rgb(synth_h, max(primary_l, 0.35), synth_s)
        return _rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))

    danger  = semantic(0.0,   25, "#cc3344")
    success = semantic(120.0, 30, "#3a9b5c")
    warning = semantic(45.0,  25, "#d4a012")

    return {
        "background": background, "foreground": foreground,
        "primary": primary, "secondary": secondary, "accent": accent,
        "surface": surface, "muted": muted,
        "danger": danger, "success": success, "warning": warning,
    }



def _pick_extreme(bucket: list, key) -> tuple[int, int, int] | None:
    """Pick the swatch in bucket maximizing `key`. Deterministic tiebreak via hex."""
    if not bucket:
        return None
    ranked = sorted(bucket, key=lambda s: (-key(s[0]), _rgb_to_hex(*s[0])))
    return ranked[0][0]
