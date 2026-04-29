"""core/palette_primitives.py — Low-level colour math for palette extraction.

Extracted from scripts/palette_extractor.py to keep that file within the
300-line budget.  These helpers are intentionally standalone (only stdlib
colorsys) so they can be imported by both palette_engine and palette_extractor
without creating a circular dependency.
"""
from __future__ import annotations

import colorsys


def _normalize_hex(hex_color: str) -> str:
    """Return a 6-digit lowercase hex string.

    Accepts '#rrggbb', '#rgb' (3-digit shorthand), and '#rrggbbaa' (strips alpha).
    Raises ValueError on any other length so callers get an explicit error instead
    of silently mis-decoding channel bytes.
    """
    h = hex_color.lstrip("#").lower()
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    elif len(h) == 8:
        h = h[:6]  # strip alpha channel
    if len(h) != 6:
        raise ValueError(f"Invalid hex color: {hex_color!r}")
    return h


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = _normalize_hex(hex_color)
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
