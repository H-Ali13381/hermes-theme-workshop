"""Color math utilities: hex↔RGB conversion, hue rotation, lightness adjustment, YIQ."""
import colorsys


def _normalize_hex(hex_color: str) -> str:
    """Return a 6-digit lowercase hex string from a '#rgb', '#rrggbb', or '#rrggbbaa' input."""
    h = hex_color.lstrip("#").lower()
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    elif len(h) == 8:
        h = h[:6]  # strip alpha channel
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
