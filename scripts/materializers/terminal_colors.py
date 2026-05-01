"""terminal_colors.py — Low-level color-scheme builders for terminal materializers.

Extracted from terminals.py to keep that file within the 300-line budget.
"""


def build_konsole_colorscheme(p: dict, pi: dict, color_scheme_name: str) -> str:
    """Build the full text of a Konsole .colorscheme file.

    Args:
        p:  palette dict (base colours).
        pi: intensified-palette dict (bright/intense variants).
        color_scheme_name: human-readable name written to [General] → Description.
    """
    return f"""[Background]
Color={p['background']}

[BackgroundIntense]
Color={p['surface']}

[Foreground]
Color={p['foreground']}

[ForegroundIntense]
Color={pi['foreground']}
Bold=true

[General]
Anchor=0.5,0.5
Blur=false
ColorRandomization=false
Description={color_scheme_name}
FillStyle=Tile
Wallpaper=
WallpaperFlipType=NoFlip

[Color0]
Color={p['surface']}

[Color0Intense]
Color={pi['muted']}

[Color1]
Color={p['danger']}

[Color1Intense]
Color={pi['danger']}

[Color2]
Color={p['success']}

[Color2Intense]
Color={pi['success']}

[Color3]
Color={p['warning']}

[Color3Intense]
Color={pi['warning']}

[Color4]
Color={p['blue']}

[Color4Intense]
Color={pi['blue']}

[Color5]
Color={p['secondary']}

[Color5Intense]
Color={pi['secondary']}

[Color6]
Color={p['accent']}

[Color6Intense]
Color={pi['accent']}

[Color7]
Color={p['foreground']}

[Color7Intense]
Color={pi['foreground']}
"""
