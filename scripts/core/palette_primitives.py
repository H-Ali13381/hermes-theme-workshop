"""core/palette_primitives.py — Private-name re-exports of core.colors.

The palette-extraction pipeline (palette_engine, palette_extractor) uses
underscore-prefixed names by convention.  All implementations live in
core.colors — this module simply re-exports them under the expected names.
"""
from core.colors import (
    hex_to_rgb_tuple  as _hex_to_rgb,
    rgb_tuple_to_hex  as _rgb_to_hex,
    rgb_to_hls        as _rgb_to_hls,
    hex_to_hls        as _hex_to_hls,
    yiq_luma          as _yiq_luma,
    rotate_hue        as _rotate_hue,
    adjust_lightness  as _adjust_lightness,
    blend_hex         as _blend_hex,
)
