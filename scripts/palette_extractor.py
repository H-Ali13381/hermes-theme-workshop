#!/usr/bin/env python3
"""
palette_extractor — image → 10-slot semantic palette for linux-ricing.

Pipeline:
  1. Load + alpha-composite over neutral gray (#808080)
  2. Thumbnail to 400x400 max
  3. Quantize via Pillow MAXCOVERAGE (fallback MEDIANCUT) into 12 swatches
  4. Classify each swatch into one of 6 ricemood buckets (Vibrant / LightVibrant /
     DarkVibrant / Muted / LightMuted / DarkMuted) using HLS thresholds
  5. Assign the 10 semantic slots (background, foreground, primary, secondary,
     accent, surface, muted, danger, success, warning) with a documented fallback
     cascade when a bucket is empty. Semantic hue slots (danger/success/warning)
     require saturation ≥ 0.45 AND lightness ≥ 0.25 to prevent dark muted swatches
     from passing hue-proximity tests.
  6. Validate: contrast (YIQ Δ ≥ 128 between background/foreground) + slot uniqueness
  7. Infer 2-3 mood tags from aggregate palette properties

Deterministic: same input image produces the same output. Tie-breaking sorts
swatches by (-pixel_count, hex_string).

This module is pure-Python with a single optional dependency (Pillow). If Pillow
is missing, `extract_palette()` raises a clear RuntimeError.
"""

from __future__ import annotations

import colorsys
from pathlib import Path


# --- Color primitives (duplicated from ricer.py to keep extractor standalone) ---

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _rgb_to_hls(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    r, g, b = rgb
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def _hex_to_hls(hex_color: str) -> tuple[float, float, float]:
    return _rgb_to_hls(_hex_to_rgb(hex_color))


def _yiq_luma(hex_color: str) -> float:
    r, g, b = _hex_to_rgb(hex_color)
    return (r * 299 + g * 587 + b * 114) / 1000


def _rotate_hue(hex_color: str, degrees: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360.0) % 1.0
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return _rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


def _adjust_lightness(hex_color: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = max(0.0, min(1.0, l * factor))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return _rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


def _blend_hex(a: str, b: str, t: float = 0.5) -> str:
    """Linear RGB blend. t=0 → a, t=1 → b."""
    ra, ga, ba = _hex_to_rgb(a)
    rb, gb, bb = _hex_to_rgb(b)
    return _rgb_to_hex(
        int(ra + (rb - ra) * t),
        int(ga + (gb - ga) * t),
        int(ba + (bb - ba) * t),
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

    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (128, 128, 128, 255))
        img = Image.alpha_composite(bg, rgba).convert("RGB")
    else:
        img = img.convert("RGB")

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

# Thresholds match ricer-wallpaper/SKILL.md ricemood classifier.
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


# --- Slot assignment ---

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
    """Pick the swatch whose hue is nearest target (in degrees), tie-broken by
    highest saturation then hex string. Returns None if nothing within tolerance
    has enough saturation."""
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


def _pick_extreme(bucket: list, key) -> tuple[int, int, int] | None:
    """Pick the swatch in bucket maximizing `key`. Deterministic tiebreak via hex."""
    if not bucket:
        return None
    ranked = sorted(bucket, key=lambda s: (-key(s[0]), _rgb_to_hex(*s[0])))
    return ranked[0][0]


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

    # background: darkest DarkMuted → darkened DarkVibrant → #0a0a0a
    bg_rgb = darkest(buckets["DarkMuted"])
    if bg_rgb:
        background = _rgb_to_hex(*bg_rgb)
    else:
        dv = darkest(buckets["DarkVibrant"])
        background = _adjust_lightness(_rgb_to_hex(*dv), 0.6) if dv else "#0a0a0a"

    # foreground: lightest LightMuted → LightVibrant → yiq-contrast
    fg_rgb = lightest(buckets["LightMuted"])
    if fg_rgb:
        foreground = _rgb_to_hex(*fg_rgb)
    else:
        lv = lightest(buckets["LightVibrant"])
        if lv:
            foreground = _rgb_to_hex(*lv)
        else:
            foreground = "#f0f0f0" if _yiq_luma(background) < 128 else "#101010"

    # primary: most chromatic Vibrant → LightVibrant → DarkVibrant → desaturated fg
    pr_rgb = most_chromatic(buckets["Vibrant"])
    if not pr_rgb:
        pr_rgb = most_chromatic(buckets["LightVibrant"])
    if not pr_rgb:
        pr_rgb = most_chromatic(buckets["DarkVibrant"])
    if pr_rgb:
        primary = _rgb_to_hex(*pr_rgb)
    else:
        primary = _rotate_hue(foreground, 210)  # cool-blue fallback, readable

    # secondary: DarkVibrant → Vibrant darkened 40% → primary darkened
    sec_rgb = most_chromatic(buckets["DarkVibrant"])
    if sec_rgb:
        secondary = _rgb_to_hex(*sec_rgb)
    elif buckets["Vibrant"]:
        v = most_chromatic(buckets["Vibrant"])
        secondary = _adjust_lightness(_rgb_to_hex(*v), 0.6)
    else:
        secondary = _adjust_lightness(primary, 0.65)

    # accent: LightVibrant with hue ≠ primary (>=30° apart) → rotate primary 30°
    primary_h = _hue_degrees(_hex_to_rgb(primary))
    accent = None
    lv_sorted = sorted(
        buckets["LightVibrant"],
        key=lambda s: (-_rgb_to_hls(s[0])[2], _rgb_to_hex(*s[0])),
    )
    for rgb, _ in lv_sorted:
        if _hue_distance(_hue_degrees(rgb), primary_h) >= 30:
            accent = _rgb_to_hex(*rgb)
            break
    if accent is None and lv_sorted:
        accent = _rotate_hue(_rgb_to_hex(*lv_sorted[0][0]), 20)
    if accent is None:
        accent = _rotate_hue(primary, 30)

    # surface: Muted → blend background toward neutral gray (robust on pure black)
    sf_rgb = most_chromatic(buckets["Muted"])
    if sf_rgb:
        surface = _rgb_to_hex(*sf_rgb)
    else:
        surface = _blend_hex(background, "#808080", 0.20)

    # muted: DarkMuted lightened 30% → blend background toward gray
    dm = darkest(buckets["DarkMuted"])
    if dm:
        muted = _adjust_lightness(_rgb_to_hex(*dm), 1.3)
        # If multiplicative lightening was a no-op (pure black), blend instead
        if muted.lower() == _rgb_to_hex(*dm).lower():
            muted = _blend_hex(_rgb_to_hex(*dm), "#808080", 0.25)
    else:
        muted = _blend_hex(background, "#808080", 0.12)

    # Semantic hue slots: find swatch nearest target hue with decent saturation;
    # else synthesize at standard hue + primary's lightness.
    # Saturation threshold deliberately higher than general classification (0.45 vs 0.3)
    # so only genuinely vivid swatches qualify — muted/muddy swatches correctly fall
    # through to the synthesized fallback.
    all_saturated = [(rgb, c) for rgb, c in swatches if _rgb_to_hls(rgb)[2] >= 0.45]
    primary_l = _rgb_to_hls(_hex_to_rgb(primary))[1]

    def semantic(target_hue: float, tolerance: float, synth_hex: str) -> str:
        match = _find_hue_match(all_saturated, target_hue, tolerance)
        # Reject matches that are too dark to read as semantic colors (lum < 0.25)
        # e.g. a dark brown at hue 20° should not become "danger red"
        if match and _rgb_to_hls(match)[1] >= 0.25:
            return _rgb_to_hex(*match)
        # Synthesize at primary's lightness for visual weight consistency
        synth_h, _, synth_s = _hex_to_hls(synth_hex)
        nr, ng, nb = colorsys.hls_to_rgb(synth_h, max(primary_l, 0.35), synth_s)
        return _rgb_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))

    danger = semantic(0.0, 25, "#cc3344")      # red (hue 0) — tight tolerance: 25° avoids orange/brown
    success = semantic(120.0, 30, "#3a9b5c")   # green (hue 120)
    warning = semantic(45.0, 25, "#d4a012")    # amber (hue 45) — tight: avoids red-orange and yellow-green

    return {
        "background": background,
        "foreground": foreground,
        "primary": primary,
        "secondary": secondary,
        "accent": accent,
        "surface": surface,
        "muted": muted,
        "danger": danger,
        "success": success,
        "warning": warning,
    }


# --- Validation ---

_MIN_YIQ_CONTRAST = 128


def _validate_palette(p: dict[str, str]) -> dict[str, str]:
    """Enforce background/foreground contrast and slot uniqueness. Mutates a copy."""
    out = dict(p)

    # Contrast: lighten/darken foreground until it meets minimum YIQ delta.
    bg_y = _yiq_luma(out["background"])
    for _ in range(20):
        if abs(_yiq_luma(out["foreground"]) - bg_y) >= _MIN_YIQ_CONTRAST:
            break
        # Push foreground away from background
        out["foreground"] = _adjust_lightness(
            out["foreground"], 1.15 if bg_y < 128 else 0.85
        )
    else:
        # Saturation pinned; fall back to black/white
        out["foreground"] = "#f0f0f0" if bg_y < 128 else "#101010"

    # Uniqueness: perturb duplicates deterministically.
    seen: dict[str, str] = {}
    slot_order = [
        "background", "foreground", "primary", "secondary", "accent",
        "surface", "muted", "danger", "success", "warning",
    ]
    for slot in slot_order:
        hex_val = out[slot].lower()
        if hex_val not in seen:
            seen[hex_val] = slot
            out[slot] = hex_val
            continue
        # Duplicate: rotate hue by 20° and adjust lightness by 15%
        adjusted = _adjust_lightness(_rotate_hue(hex_val, 20), 1.15)
        tries = 0
        while adjusted.lower() in seen and tries < 6:
            adjusted = _adjust_lightness(_rotate_hue(adjusted, 20), 1.15)
            tries += 1
        if adjusted.lower() in seen:
            # Multiplicative/rotate stuck (pure black/white). Blend toward primary
            # (or neutral gray as last resort) to escape the zero-lightness trap.
            mix_target = out.get("primary", "#808080")
            if mix_target.lower() == hex_val.lower():
                mix_target = "#808080"
            adjusted = _blend_hex(hex_val, mix_target, 0.4)
            escape = 0
            while adjusted.lower() in seen and escape < 8:
                adjusted = _blend_hex(adjusted, "#808080", 0.2)
                escape += 1
        out[slot] = adjusted.lower()
        seen[adjusted.lower()] = slot

    return out


# --- Mood tags ---

def _infer_mood_tags(palette: dict[str, str]) -> list[str]:
    tags = []

    # Lightness tag from background/surface/muted mean
    dark_slots = [palette["background"], palette["surface"], palette["muted"]]
    mean_l = sum(_hex_to_hls(h)[1] for h in dark_slots) / len(dark_slots)
    tags.append("dark" if mean_l < 0.4 else "light")

    # Saturation tag from primary/secondary/accent mean
    vivid_slots = [palette["primary"], palette["secondary"], palette["accent"]]
    mean_s = sum(_hex_to_hls(h)[2] for h in vivid_slots) / len(vivid_slots)
    tags.append("vibrant" if mean_s > 0.5 else "muted")

    # Hue tag from primary
    ph = _hex_to_hls(palette["primary"])[0] * 360
    if ph < 60 or ph >= 330:
        tags.append("warm")
    elif ph < 90:
        tags.append("amber")
    elif ph < 180:
        tags.append("cool")
    elif ph < 270:
        tags.append("blue")
    else:
        tags.append("violet")

    return tags


# --- Icon theme selection ---

_ICON_SEARCH_DIRS = [
    Path("/usr/share/icons"),
    Path.home() / ".local/share/icons",
]
_ICON_SKIP = {"hicolor", "locolor", "default"}

# Ranked preferences: first installed name wins.
_DARK_ICON_PREFS = [
    "Papirus-Dark", "Tela-dark", "tela-dark", "tela-circle-dark",
    "Numix-Circle", "breeze-dark", "Adwaita-dark",
    "Papirus", "breeze", "Adwaita", "AdwaitaLegacy", "oxygen",
]
_LIGHT_ICON_PREFS = [
    "Papirus", "Papirus-Light", "Tela", "tela", "tela-circle",
    "Breeze_Light", "breeze", "Adwaita", "AdwaitaLegacy", "oxygen",
    "Papirus-Dark", "breeze-dark",
]


def _has_app_icons(theme_dir: Path) -> bool:
    """True if the theme contains application/place icons (not cursor-only)."""
    app_cats = {"apps", "places", "applications"}
    for level1 in theme_dir.iterdir():
        if not level1.is_dir():
            continue
        for level2 in level1.iterdir():
            if level2.is_dir() and level2.name in app_cats:
                return True
    return False


def _installed_icon_themes(search_dirs=None) -> list[str]:
    """Return names of installed icon themes that include application icons.

    Filters out cursor-only themes (no apps/ or places/ at depth ≤ 2) and
    infrastructure themes (hicolor, locolor, default).
    """
    dirs = search_dirs if search_dirs is not None else _ICON_SEARCH_DIRS
    seen: set[str] = set()
    themes: list[str] = []
    for d in dirs:
        d = Path(d)
        if not d.exists():
            continue
        for sub in sorted(d.iterdir()):
            if not sub.is_dir() or sub.name in seen or sub.name in _ICON_SKIP:
                continue
            if not (sub / "index.theme").exists():
                continue
            if not _has_app_icons(sub):
                continue
            seen.add(sub.name)
            themes.append(sub.name)
    return themes


def select_icon_theme(palette: dict, search_dirs=None) -> str:
    """Pick the best installed icon theme for the given palette.

    Walks a ranked preference list (dark-first for dark palettes, light-first
    for light palettes) and returns the first name that is actually installed.
    Never writes a nonexistent theme to kdeglobals.
    """
    installed = set(_installed_icon_themes(search_dirs))
    if not installed:
        return "hicolor"

    is_dark = _yiq_luma(palette["background"]) < 128
    prefs = _DARK_ICON_PREFS if is_dark else _LIGHT_ICON_PREFS

    for name in prefs:
        if name in installed:
            return name

    # Fuzzy fallback: prefer any installed theme whose name contains "dark"/"light"
    tag = "dark" if is_dark else "light"
    for name in sorted(installed):
        if tag in name.lower():
            return name

    return sorted(installed)[0]


# --- Theme-name defaults ---

def _default_theme_names(palette: dict[str, str]) -> dict[str, str]:
    """Return sensible defaults for the theme-name keys (kvantum_theme,
    cursor_theme, icon_theme, gtk_theme, plasma_theme) based on whether the
    palette reads as dark or light.

    These defaults keep materialize_plasma_theme / materialize_cursor /
    materialize_gtk / materialize_kvantum from silently early-returning on
    extracted design systems — the skill's 10-layer KDE coverage is only
    real if every materializer actually runs.
    """
    is_dark = _yiq_luma(palette["background"]) < 128
    return {
        "kvantum_theme": "kvantum-dark" if is_dark else "kvantum",
        "cursor_theme": "breeze_cursors",
        "icon_theme": select_icon_theme(palette),
        "gtk_theme": "Adwaita-dark" if is_dark else "Adwaita",
        "plasma_theme": "default",
    }


# --- Public API ---

def extract_palette(image_path: str, *, name: str | None = None) -> dict:
    """Image → full design_system dict (10-slot palette + theme-name defaults).

    Args:
        image_path: path to the wallpaper / reference image
        name: theme name (default: image file stem)

    Returns:
        dict with keys: name, description, palette, mood_tags,
        kvantum_theme, cursor_theme, icon_theme, gtk_theme, plasma_theme.
    """
    path = Path(image_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"image not found: {path}")

    img = _load_and_normalize(str(path))
    swatches = _quantize_swatches(img, n=12)
    if not swatches:
        raise RuntimeError(f"quantization produced no swatches: {path}")

    raw_palette = _assign_slots(swatches)
    palette = _validate_palette(raw_palette)
    mood_tags = _infer_mood_tags(palette)

    theme_name = name or path.stem.replace(" ", "-").lower()
    return {
        "name": theme_name,
        "description": f"Extracted from {path.name}",
        "palette": palette,
        "mood_tags": mood_tags,
        **_default_theme_names(palette),
    }


if __name__ == "__main__":
    import argparse
    import json
    import sys

    ap = argparse.ArgumentParser(description="Extract a design system from an image.")
    ap.add_argument("image", help="path to image")
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    try:
        design = extract_palette(args.image, name=args.name)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    output = json.dumps(design, indent=2)
    if args.out:
        Path(args.out).expanduser().write_text(output + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(output)
