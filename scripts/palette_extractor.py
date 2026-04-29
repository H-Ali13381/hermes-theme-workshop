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

from pathlib import Path

from core.palette_primitives import (
    _hex_to_rgb, _rgb_to_hex, _rgb_to_hls, _hex_to_hls,
    _yiq_luma, _rotate_hue, _adjust_lightness, _blend_hex,
)
from core.palette_engine import (
    _load_and_normalize, _quantize_swatches, _assign_slots,
    _classify_swatch,  # re-exported so tests can access it via this module's namespace
)

# _load_and_normalize, _quantize_swatches, _assign_slots, _classify_swatch moved to
# core/palette_engine.py; _classify_swatch is re-exported here for backward compatibility.
# Color primitives moved to core/palette_primitives.py

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
