#!/usr/bin/env python3
"""Convert an image to a Hermes banner_hero (30x15, Rich markup colored).

Usage:
    python3 image_to_hero.py <image_path> [--ramp blocky|classic|doom]
                                           [--palette gold|crimson|cyan|mono]
                                           [--sharpen]

Output: prints the banner_hero YAML value to stdout. Paste into
~/.hermes/skins/<name>.yaml under banner_hero.

Dependencies: Pillow, numpy. Not present in Hermes execute_code sandbox —
run via `python3 <path>` in terminal instead.
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
except ImportError:
    sys.exit("Missing deps. Install: pip install Pillow numpy")

# HARD dimension constraint — see ui-tui/src/banner.ts CADUCEUS_WIDTH = 30
WIDTH = 30
HEIGHT = 15

RAMPS = {
    # Plain ASCII — safest, always 1-wide
    "classic": " .:-=+*#%@",                # Paul Bourke's 10-level
    "doom": " .,:-=+o*#%@$",                # classic doom-like
    # Mixed ASCII + extended — LOOKS best, test in target terminal first
    "blocky": " .,:;=+*#■▓█",                # liked by Hasan; ■▓█ can be ambiguous-width
    # AVOID in most cases — ░▒▓ often render 2-wide
    "shade": " .,:;-=░▒▓█",
}

# Color palettes. Keys are ramp chars; values are hex colors.
# Dense chars get the brightest color; dim chars get the background/shadow color.
PALETTES = {
    "gold": {  # DragonFable / Doomherald
        "dense": "#c9a227",    # Dragon Gold
        "mid":   "#e8b947",    # Bright gold
        "low":   "#8c1a2e",    # Crimson fell
        "dim":   "#5a3a0a",    # Tarnished
    },
    "crimson": {
        "dense": "#c93030", "mid": "#e85050", "low": "#8c1a2e", "dim": "#3a0a0a",
    },
    "cyan": {
        "dense": "#27c9c9", "mid": "#47e8e8", "low": "#1a8c8c", "dim": "#0a3a3a",
    },
    "mono": {
        "dense": "#ffffff", "mid": "#cccccc", "low": "#888888", "dim": "#444444",
    },
}


def image_to_ascii(path: str, ramp: str, sharpen: bool) -> list[str]:
    img = Image.open(path).convert("L").resize((WIDTH, HEIGHT), Image.LANCZOS)
    if sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
        img = ImageEnhance.Sharpness(img).enhance(1.4)

    arr = np.array(img).astype(np.float32)
    # Percentile contrast stretch — pushes extremes to full 0..255 range
    lo, hi = np.percentile(arr, [2, 98])
    arr = np.clip((arr - lo) / max(hi - lo, 1) * 255, 0, 255).astype(np.uint8)

    # Decide direction: dark bg (corners dark) → invert so bright pixel = dense char
    corner = (int(arr[0, 0]) + int(arr[0, -1]) + int(arr[-1, 0]) + int(arr[-1, -1])) / 4
    center = float(arr[HEIGHT // 2 - 2:HEIGHT // 2 + 2,
                       WIDTH // 2 - 2:WIDTH // 2 + 2].mean())
    invert = corner < center

    n = len(ramp)
    idx = (arr.astype(np.float32) / 255 * (n - 1)).astype(int)
    if not invert:
        idx = (n - 1) - idx

    return ["".join(ramp[v] for v in row) for row in idx]


def char_to_color_tier(char: str, ramp: str) -> str:
    """Map a char to a color tier: dense|mid|low|dim|None (space)."""
    if char == " ":
        return None
    i = ramp.index(char)
    n = len(ramp)
    frac = i / (n - 1)
    if frac >= 0.75:
        return "dense"
    if frac >= 0.5:
        return "mid"
    if frac >= 0.25:
        return "low"
    return "dim"


def colorize_rle(lines: list[str], ramp: str, palette: dict) -> str:
    """Run-length encode color runs into Rich markup per line.

    CRITICAL: Replaces every ASCII space with braille blank U+2800 to defeat
    the Rich parser's trimEnd() and Table.grid's centering. Without this,
    any asymmetric art drifts line-by-line and renders misaligned.
    """
    BLANK = "\u2800"  # braille blank — 1-wide, invisible, NOT whitespace
    out = []
    for line in lines:
        parts = []
        i = 0
        while i < len(line):
            tier = char_to_color_tier(line[i], ramp)
            j = i
            while j < len(line) and char_to_color_tier(line[j], ramp) == tier:
                j += 1
            seg = line[i:j]
            if tier is None:
                # Replace spaces with braille blank (inside AND at line edges)
                parts.append(seg.replace(" ", BLANK))
            else:
                parts.append(f"[{palette[tier]}]{seg}[/]")
            i = j
        out.append("".join(parts))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--ramp", choices=list(RAMPS), default="blocky")
    ap.add_argument("--palette", choices=list(PALETTES), default="gold")
    ap.add_argument("--sharpen", action="store_true")
    ap.add_argument("--plain", action="store_true", help="skip colors, print raw ASCII")
    args = ap.parse_args()

    if not Path(args.image).exists():
        sys.exit(f"Not found: {args.image}")

    ramp = RAMPS[args.ramp]
    lines = image_to_ascii(args.image, ramp, args.sharpen)

    if args.plain:
        print("\n".join(lines))
        return

    colored = colorize_rle(lines, ramp, PALETTES[args.palette])
    # YAML value form: single line with \n escapes inside double quotes
    yaml_value = colored.replace("\n", "\\n")
    print(f'banner_hero: "{yaml_value}"')


if __name__ == "__main__":
    main()
