#!/usr/bin/env python3
"""
img_to_braille.py — Convert any image to Braille Unicode ASCII art for Hermes skins.

Braille Unicode (U+2800–U+28FF) gives 2×4 sub-pixel resolution per character:
  - 8 individually addressable dots per cell
  - Always 1 column wide (unlike ░▒▓ block chars which are often 2-wide)
  - Braille blank ⠀ (U+2800) is invisible AND not trimmed by trimEnd()

Output modes:
  --out-yaml    → banner_hero / banner_logo ready YAML value (paste into skin)
  --out-plain   → raw braille art (preview, no markup)
  --out-preview → framed preview for sharing/messaging

Usage:
    python3 img_to_braille.py --input image.png --width 30 --height 15
    python3 img_to_braille.py --input logo.png --width 92 --height 10 --palette gold --out-yaml
    python3 img_to_braille.py --input face.jpg --width 30 --height 15 --validate-colors

Character limits (HARD constraints from Hermes banner.ts):
    banner_hero:  width=30, height=15  (left column beside tool list)
    banner_logo:  width≤100, height≤12  (shown above hero when terminal≥95 cols)

Dependencies: Pillow, numpy
    pip install Pillow numpy
    (NOT available in Hermes execute_code sandbox — run via terminal)
"""

import argparse
import sys
import re
from pathlib import Path

try:
    from PIL import Image, ImageFilter, ImageEnhance
    import numpy as np
except ImportError:
    sys.exit("Missing deps. Install: pip install Pillow numpy")

# ─── Braille encoding ────────────────────────────────────────────────────────
# Braille cell layout (unicode bit positions):
#   col0  col1
#   dot1  dot4   → bit0  bit3
#   dot2  dot5   → bit1  bit4
#   dot3  dot6   → bit2  bit5
#   dot7  dot8   → bit6  bit7
#
# The source image is sampled at 2× width, 4× height resolution relative to
# the character grid, giving one dot per pixel block.

BRAILLE_DOTS = [
    (0, 0, 0),  # dot1: col=0, row=0, bit=0
    (0, 1, 1),  # dot2: col=0, row=1, bit=1
    (0, 2, 2),  # dot3: col=0, row=2, bit=2
    (1, 0, 3),  # dot4: col=1, row=0, bit=3
    (1, 1, 4),  # dot5: col=1, row=1, bit=4
    (1, 2, 5),  # dot6: col=1, row=2, bit=5
    (0, 3, 6),  # dot7: col=0, row=3, bit=6
    (1, 3, 7),  # dot8: col=1, row=3, bit=7
]

BRAILLE_BASE = 0x2800
BRAILLE_BLANK = "\u2800"  # U+2800 — invisible, 1-wide, immune to trimEnd()


def encode_braille_char(dot_bits: int) -> str:
    return chr(BRAILLE_BASE + dot_bits)


# ─── Color Palettes ───────────────────────────────────────────────────────────

PALETTES = {
    "gold": {                            # DragonFable / Doomherald
        "bright": "#f0d688",
        "mid":    "#cc9e24",
        "dim":    "#885d14",
        "shadow": "#3a2008",
        "accent": "#8c1a2e",             # Crimson fell (shadows/edges)
    },
    "crimson": {
        "bright": "#f08888",
        "mid":    "#c93030",
        "dim":    "#7a1010",
        "shadow": "#2a0808",
        "accent": "#c9a227",
    },
    "cyan": {
        "bright": "#88f0f0",
        "mid":    "#27c9c9",
        "dim":    "#107a7a",
        "shadow": "#082a2a",
        "accent": "#c9a227",
    },
    "mono": {
        "bright": "#ffffff",
        "mid":    "#cccccc",
        "dim":    "#888888",
        "shadow": "#444444",
        "accent": "#aaaaaa",
    },
    "purple": {
        "bright": "#e0b8f8",
        "mid":    "#9b30d0",
        "dim":    "#5a1080",
        "shadow": "#200830",
        "accent": "#c9a227",
    },
}


# ─── Color Classification ─────────────────────────────────────────────────────
# IMPORTANT: Do NOT classify solely from grayscale luminance.
# Saturated dark colors (crimson #d42818 → gray ~89) are INVISIBLE under
# a pure luminance threshold. Always combine luminance + saturation masks.

def classify_color(r: int, g: int, b: int, a: int, palette_name: str) -> str | None:
    """
    Map RGBA pixel to a palette tier name, or None for transparent/background.

    Returns: 'bright' | 'mid' | 'dim' | 'shadow' | 'accent' | None

    The dual-mask strategy:
      - 'bright' mask: high luminance pixels (gold, highlights)
      - saturation mask: strongly hue-dominant pixels regardless of lightness
        (crimson gems, deep blue accents, forest green — all dark but vivid)
    """
    if a < 30:
        return None  # transparent

    lum = 0.299 * r + 0.587 * g + 0.114 * b

    # ── Saturation-dominant branches (checked BEFORE luminance) ──────────────
    # Red-dominant: catches crimson #d42818 (lum ~89, r=212 > g=24*1.4=33, b=24*1.6=38)
    if r > 90 and r > g * 1.4 and r > b * 1.6:
        return "accent" if lum < 160 else "bright"

    # Blue-dominant: deep blue, sapphire
    if b > 90 and b > r * 1.3 and b > g * 1.2:
        return "dim" if lum < 80 else "mid"

    # Green-dominant: forest green, jade
    if g > 90 and g > r * 1.3 and g > b * 1.2:
        return "dim" if lum < 80 else "mid"

    # ── Luminance tiers (warm/neutral colors) ─────────────────────────────────
    if lum > 180:
        return "bright"
    if lum > 110:
        return "mid"
    if lum > 55:
        return "dim"
    if lum > 20:
        return "shadow"
    return None  # near-black → background


# ─── Image Preprocessing ──────────────────────────────────────────────────────

def auto_crop_tight(img: Image.Image, margin: int = 3) -> Image.Image:
    """
    Remove transparent/near-black padding from a PNG.
    Composites onto black, finds non-background pixels, crops tight.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
    composited = Image.alpha_composite(bg, img)
    gray = np.array(composited.convert("L"))
    mask = gray > 20  # above near-black
    ys, xs = np.where(mask)
    if ys.size == 0:
        return img  # nothing found — return as-is
    H, W = gray.shape
    y0 = max(0, int(ys.min()) - margin)
    y1 = min(H, int(ys.max()) + margin)
    x0 = max(0, int(xs.min()) - margin)
    x1 = min(W, int(xs.max()) + margin)
    return composited.crop((x0, y0, x1, y1))


def load_and_prepare(path: str, target_w: int, target_h: int,
                     sharpen: bool = False, auto_crop: bool = True) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    if auto_crop:
        img = auto_crop_tight(img)
    # Resize to 2× width, 4× height (one dot per pixel block)
    dot_w = target_w * 2
    dot_h = target_h * 4
    img = img.resize((dot_w, dot_h), Image.LANCZOS)
    if sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=2))
        img = ImageEnhance.Sharpness(img).enhance(1.4)
    return img


# ─── Luminance mask with saturation override ─────────────────────────────────

def compute_on_mask(rgba_arr: np.ndarray,
                    lum_threshold: float = 110.0,
                    red_ratio_g: float = 1.4,
                    red_ratio_b: float = 1.6) -> np.ndarray:
    """
    Compute a boolean "dot on" mask that catches BOTH:
      - bright pixels (gold, highlights) via luminance
      - saturated dark colors (crimson, deep blue) via hue dominance

    Parameters
    ----------
    rgba_arr        : H×W×4 uint8 array
    lum_threshold   : luminance cutoff (0–255). Default 110 works for most images.
    red_ratio_g     : r must exceed g by this factor to count as red-dominant.
    red_ratio_b     : r must exceed b by this factor to count as red-dominant.

    Returns bool H×W mask. True = dot lit.
    """
    r = rgba_arr[:, :, 0].astype(np.float32)
    g = rgba_arr[:, :, 1].astype(np.float32)
    b = rgba_arr[:, :, 2].astype(np.float32)
    a = rgba_arr[:, :, 3].astype(np.float32)

    gray = 0.299 * r + 0.587 * g + 0.114 * b

    # Percentile contrast stretch (2%–98%) before threshold
    flat = gray[a > 30].flatten()
    if flat.size > 0:
        lo, hi = np.percentile(flat, [2, 98])
        gray_s = np.clip((gray - lo) / max(hi - lo, 1.0) * 255.0, 0, 255)
    else:
        gray_s = gray

    # Luminance mask
    bright = gray_s > lum_threshold

    # Saturation masks (catch dark but vivid colors)
    red_dom  = (r > 90) & (r > g * red_ratio_g) & (r > b * red_ratio_b)
    blue_dom = (b > 90) & (b > r * 1.3) & (b > g * 1.2)
    grn_dom  = (g > 90) & (g > r * 1.3) & (g > b * 1.2)

    # Transparent pixels never light a dot
    visible = a > 30

    return (bright | red_dom | blue_dom | grn_dom) & visible


# ─── Braille grid builder ─────────────────────────────────────────────────────

def image_to_braille_grid(img: Image.Image,
                           on_mask: np.ndarray,
                           palette_name: str) -> list[list[tuple[str, str | None]]]:
    """
    Build a 2D grid of (char, color_hex | None) tuples.

    Each cell covers a 2-wide × 4-tall dot block.
    color_hex is determined by the average RGBA of all lit dots in the cell.
    """
    rgba = np.array(img)
    char_h = img.height // 4
    char_w = img.width // 2
    palette = PALETTES[palette_name]

    grid = []
    for cy in range(char_h):
        row = []
        for cx in range(char_w):
            # Build braille bitmask
            bits = 0
            lit_pixels = []
            for (dot_col, dot_row, bit) in BRAILLE_DOTS:
                py = cy * 4 + dot_row
                px = cx * 2 + dot_col
                if on_mask[py, px]:
                    bits |= (1 << bit)
                    lit_pixels.append((int(rgba[py, px, 0]),
                                       int(rgba[py, px, 1]),
                                       int(rgba[py, px, 2]),
                                       int(rgba[py, px, 3])))

            ch = encode_braille_char(bits) if bits else BRAILLE_BLANK

            if lit_pixels:
                # Average RGBA of lit dots → classify to palette tier → hex color
                avg_r = int(np.mean([p[0] for p in lit_pixels]))
                avg_g = int(np.mean([p[1] for p in lit_pixels]))
                avg_b = int(np.mean([p[2] for p in lit_pixels]))
                avg_a = int(np.mean([p[3] for p in lit_pixels]))
                tier  = classify_color(avg_r, avg_g, avg_b, avg_a, palette_name)
                color = palette.get(tier) if tier else None
            else:
                color = None

            row.append((ch, color))
        grid.append(row)
    return grid


# ─── Color validation ─────────────────────────────────────────────────────────

def validate_color_coverage(grid: list[list[tuple[str, str | None]]],
                              palette_name: str,
                              verbose: bool = True) -> dict:
    """
    Report per-tier coverage to verify color classification is working.

    Useful for debugging missing features (e.g. "the red gem is invisible"):
    - Count cells per color tier
    - Warn if accent/crimson tier is < 20 cells (likely silently dropped)
    - Warn if >90% cells are blank (source might be wrong format)

    Returns dict of tier → cell count.
    """
    from collections import Counter
    palette = PALETTES[palette_name]
    tier_counts = Counter()
    total = 0
    blank = 0
    for row in grid:
        for ch, color in row:
            total += 1
            if ch == BRAILLE_BLANK or color is None:
                blank += 1
                tier_counts["blank"] += 1
            else:
                # Reverse-map hex → tier name
                tier = next((k for k, v in palette.items() if v == color), "unknown")
                tier_counts[tier] += 1

    if verbose:
        print("\n── Color Coverage Validation ──────────────────────")
        print(f"  Total cells : {total}")
        print(f"  Blank cells : {blank} ({100*blank//total}%)")
        for tier, count in sorted(tier_counts.items()):
            pct = 100 * count // total
            marker = ""
            if tier == "accent" and count < 20:
                marker = "  ⚠  LOW — saturated feature may be invisible; tune red_ratio"
            if tier == "blank" and pct > 85:
                marker = "  ⚠  HIGH — source image may be wrong format or too dim"
            print(f"  {tier:<10} : {count:4d} ({pct:3d}%) {marker}")
        print("─" * 50)

    return dict(tier_counts)


# ─── Rich markup output ───────────────────────────────────────────────────────

def grid_to_rich_lines(grid: list[list[tuple[str, str | None]]]) -> list[str]:
    """
    Run-length encode color changes into Rich markup lines.
    Uses BRAILLE_BLANK for all colorless cells (immune to trimEnd()).
    """
    lines = []
    for row in grid:
        parts = []
        i = 0
        while i < len(row):
            ch, color = row[i]
            # Group consecutive cells with the same color
            j = i
            while j < len(row) and row[j][1] == color:
                j += 1
            segment = "".join(c for c, _ in row[i:j])
            if color:
                parts.append(f"[{color}]{segment}[/]")
            else:
                # Replace with braille blanks to preserve column positions
                parts.append(BRAILLE_BLANK * len(segment))
            i = j
        lines.append("".join(parts))
    return lines


def lines_to_yaml_value(lines: list[str], field: str = "banner_hero") -> str:
    escaped = "\\n".join(lines)
    return f'{field}: "{escaped}"'


def frame_preview(lines: list[str], label: str = "") -> str:
    w = len(lines[0]) if lines else 0
    # Use raw braille chars — strip markup for preview
    def strip_markup(s):
        return re.sub(r'\[/?[^\]]*\]', '', s)
    plain_lines = [strip_markup(l) for l in lines]
    inner_w = max(len(l) for l in plain_lines)
    bar = "─" * (inner_w + 2)
    header = f"┌{bar}┐  {label}"
    footer = f"└{bar}┘"
    rows = [f"│ {l}{' ' * (inner_w - len(l))} │" for l in plain_lines]
    return "\n".join([header] + rows + [footer])


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Convert image to Braille Unicode art for Hermes skins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Character limits (Hermes banner.ts hard constraints):
  banner_hero:  --width 30  --height 15
  banner_logo:  --width 92  --height 10  (max 100 cols)

Examples:
  python3 img_to_braille.py --input logo.png --width 30 --height 15 --out-yaml
  python3 img_to_braille.py --input face.jpg --width 92 --height 10 --palette gold --validate-colors
  python3 img_to_braille.py --input art.png  --width 30 --height 15 --out-preview
        """
    )
    ap.add_argument("--input",  "-i", required=True, help="Path to source image")
    ap.add_argument("--width",  "-W", type=int, default=30,  help="Character columns (default 30 for hero)")
    ap.add_argument("--height", "-H", type=int, default=15,  help="Character rows    (default 15 for hero)")
    ap.add_argument("--palette", "-p", choices=list(PALETTES), default="gold",
                    help="Color palette (default: gold)")
    ap.add_argument("--lum-threshold", type=float, default=110.0,
                    help="Luminance threshold 0–255 for 'dot on' (default 110)")
    ap.add_argument("--red-ratio-g", type=float, default=1.4,
                    help="Red/green ratio to trigger red-dominant mask (default 1.4)")
    ap.add_argument("--red-ratio-b", type=float, default=1.6,
                    help="Red/blue ratio to trigger red-dominant mask (default 1.6)")
    ap.add_argument("--sharpen", action="store_true",
                    help="Apply unsharp mask + sharpness enhance (good for faces/portraits)")
    ap.add_argument("--no-auto-crop", action="store_true",
                    help="Skip automatic tight bounding-box crop")
    ap.add_argument("--field", default="banner_hero",
                    help="YAML field name (default: banner_hero, use banner_logo for wide art)")
    ap.add_argument("--out-yaml",    action="store_true", help="Output YAML value (paste into skin)")
    ap.add_argument("--out-plain",   action="store_true", help="Output raw braille, no markup")
    ap.add_argument("--out-preview", action="store_true", help="Output framed preview (messaging-safe)")
    ap.add_argument("--validate-colors", action="store_true",
                    help="Print per-tier coverage report (for debugging missing features)")
    args = ap.parse_args()

    if not Path(args.input).exists():
        sys.exit(f"File not found: {args.input}")

    # Enforce hard dimension limits
    if args.width > 100:
        print(f"⚠  Warning: width {args.width} exceeds 100-col Hermes limit. Using 100.", file=sys.stderr)
        args.width = 100
    if args.field == "banner_hero" and (args.width != 30 or args.height != 15):
        print(f"ℹ  banner_hero hard constraint: 30×15. You specified {args.width}×{args.height}.",
              file=sys.stderr)

    print(f"Loading {args.input} → {args.width}×{args.height} braille grid...", file=sys.stderr)
    img = load_and_prepare(args.input, args.width, args.height,
                            sharpen=args.sharpen, auto_crop=not args.no_auto_crop)

    rgba_arr = np.array(img)
    on_mask  = compute_on_mask(rgba_arr,
                                lum_threshold=args.lum_threshold,
                                red_ratio_g=args.red_ratio_g,
                                red_ratio_b=args.red_ratio_b)
    grid     = image_to_braille_grid(img, on_mask, args.palette)

    if args.validate_colors:
        validate_color_coverage(grid, args.palette, verbose=True)

    lines = grid_to_rich_lines(grid)

    if args.out_plain:
        import re as _re
        for line in lines:
            print(_re.sub(r'\[/?[^\]]*\]', '', line))
    elif args.out_preview:
        print(frame_preview(lines, label=f"{args.width}×{args.height} {args.palette}"))
    else:
        # Default: YAML value
        print(lines_to_yaml_value(lines, field=args.field))


if __name__ == "__main__":
    main()
