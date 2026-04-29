"""Color math utilities: hex↔RGB conversion, hue rotation, lightness adjustment, YIQ.

This is the single source of truth for colour primitives.  Both the
materializer layer (``from core.colors import …``) and the palette-extraction
layer (``core.palette_primitives`` re-exports under private names) use the
implementations defined here.
"""
import colorsys


def _normalize_hex(hex_color: str) -> str:
    """Return a 6-digit lowercase hex string from a '#rgb', '#rrggbb', or '#rrggbbaa' input.

    Raises ValueError on any other length so callers get an explicit error
    instead of silently mis-decoding channel bytes.
    """
    h = hex_color.lstrip("#").lower()
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    elif len(h) == 8:
        h = h[:6]  # strip alpha channel
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    return h


def hex_to_rgb(hex_color: str) -> str:
    """Convert '#rrggbb' (or 3-digit shorthand) to 'r,g,b' decimal string as KDE .colors expects."""
    h = _normalize_hex(hex_color)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


def hex_to_rgb_tuple(hex_color: str) -> tuple[int, int, int]:
    """Convert '#rrggbb' (or 3-digit shorthand) to (r, g, b) integer tuple."""
    h = _normalize_hex(hex_color)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_tuple_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) integers to '#rrggbb' hex string."""
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def yiq_text_color(hex_color: str) -> str:
    """Return '#ffffff' or '#000000' for maximum readability over hex_color background.

    Uses the YIQ perceptual luma formula:  yiq = (r*299 + g*587 + b*114) / 1000
    Under 200 → white text.  200+ → black text.
    """
    r, g, b = hex_to_rgb_tuple(hex_color)
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "#ffffff" if yiq < 200 else "#000000"


def is_dark_palette(palette: dict) -> bool:
    """Return True if the palette background is perceptually dark (YIQ luma ≤ 128).

    Uses the same YIQ formula as yiq_text_color but with the theme-classification
    threshold (128) rather than the text-readability threshold (200).
    """
    r, g, b = hex_to_rgb_tuple(palette.get("background", "#000000"))
    return (r * 299 + g * 587 + b * 114) / 1000 <= 128


def rotate_hue(hex_color: str, degrees: float) -> str:
    """Rotate the hue of hex_color by degrees (0-360).  Preserves saturation and value."""
    r, g, b = hex_to_rgb_tuple(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + degrees / 360.0) % 1.0
    nr, ng, nb = colorsys.hsv_to_rgb(h, s, v)
    return rgb_tuple_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


def adjust_lightness(hex_color: str, factor: float) -> str:
    """Multiply the HSL lightness of hex_color by factor.

    factor < 1 darkens (0.8 = 20% darker), factor > 1 lightens (1.3 = 30% lighter).
    Clamps to [0.0, 1.0].  Preserves hue and saturation.
    """
    r, g, b = hex_to_rgb_tuple(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    l = max(0.0, min(1.0, l * factor))
    nr, ng, nb = colorsys.hls_to_rgb(h, l, s)
    return rgb_tuple_to_hex(int(nr * 255), int(ng * 255), int(nb * 255))


# ---------------------------------------------------------------------------
# Extras used by the palette-extraction pipeline
# ---------------------------------------------------------------------------

def rgb_to_hls(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """Convert (r, g, b) integer tuple to (h, l, s) floats in [0, 1]."""
    r, g, b = rgb
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def hex_to_hls(hex_color: str) -> tuple[float, float, float]:
    """Convert '#rrggbb' to (h, l, s) floats."""
    return rgb_to_hls(hex_to_rgb_tuple(hex_color))


def yiq_luma(hex_color: str) -> float:
    """Return the YIQ perceptual luma of hex_color (0–255 scale)."""
    r, g, b = hex_to_rgb_tuple(hex_color)
    return (r * 299 + g * 587 + b * 114) / 1000


def blend_hex(a: str, b: str, t: float = 0.5) -> str:
    """Linear RGB blend.  t=0 → a, t=1 → b."""
    ra, ga, ba = hex_to_rgb_tuple(a)
    rb, gb, bb = hex_to_rgb_tuple(b)
    return rgb_tuple_to_hex(
        int(ra + (rb - ra) * t),
        int(ga + (gb - ga) * t),
        int(ba + (bb - ba) * t),
    )
