#!/usr/bin/env python3
"""
Generate a KDE Plasma panel-background.svg from a parchment palette.
Palette extracted from the style-transfer mockup.
Output: void-dragon Plasma theme panel-background.svg
"""
import base64
from pathlib import Path
from PIL import Image

ASSETS = Path(__file__).resolve().parent
THEME_DIR = Path.home() / ".local" / "share" / "plasma" / "desktoptheme" / "void-dragon"
WIDGETS_DIR = THEME_DIR / "widgets"

# --- Palette from mockup ---
PARCHMENT_LIGHT = "#fef7d2"   # dominant bright cream
PARCHMENT_MID   = "#fdf1ca"   # mid parchment
PARCHMENT_WARM  = "#fbe2a5"   # warm amber parchment
PARCHMENT_TAN   = "#be9c61"   # darker tan (borders, shadows)
GOLD_BRIGHT     = "#d4a012"   # void-dragon gold (accent)
GOLD_DARK       = "#8b6310"   # darker gold (border stroke)
SHADOW          = "#3a2a0a"   # dark edge shadow
CORNER_DARK     = "#2a1a05"   # deepest corner

# --- Crop a parchment texture patch from the mockup for embedding ---
def get_parchment_patch_b64(size=128):
    mockup_path = ASSETS / "toolbar_parchment_mockup.png"
    if not mockup_path.exists():
        return None
    with Image.open(mockup_path) as raw:
        img = raw.convert("RGB")
    w, h = img.size
    # Crop a center patch avoiding edges
    cx, cy = w // 2, h // 2
    patch = img.crop((cx - size//2, cy - size//2, cx + size//2, cy + size//2))
    patch = patch.resize((size, size), Image.Resampling.LANCZOS)
    import io
    buf = io.BytesIO()
    patch.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()

# SVG template — viewBox "0 0 157 64"
# Layout: 6px corners, 32px center tile, 6px edges
# Total: 6 + 32 + 6 = 44px width minimum, 64px total height (panel height)
# corner=10px, edge=5px thick, center fills the rest

def generate_svg(patch_b64=None):
    # If we have the parchment patch, use it as a pattern in center
    # Otherwise fall back to gradient

    if patch_b64:
        pattern_def = f"""
    <pattern id="parchment-tile" x="0" y="0" width="128" height="128" patternUnits="userSpaceOnUse">
      <image href="data:image/png;base64,{patch_b64}" x="0" y="0" width="128" height="128"
             preserveAspectRatio="xMidYMid slice"/>
    </pattern>"""
        center_fill = "url(#parchment-tile)"
        edge_fill   = "url(#parchment-tile)"
    else:
        pattern_def = ""
        center_fill = "url(#grad-center)"
        edge_fill   = "url(#grad-center)"

    svg = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   id="svg2"
   height="64"
   viewBox="0 0 157 64"
   width="157"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   xmlns="http://www.w3.org/2000/svg">

  <defs id="defs1">

    <!-- Parchment center gradient (fallback if no patch) -->
    <linearGradient id="grad-center" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
      <stop offset="0"   stop-color="{PARCHMENT_LIGHT}" stop-opacity="0.97"/>
      <stop offset="0.4" stop-color="{PARCHMENT_MID}"   stop-opacity="0.95"/>
      <stop offset="1"   stop-color="{PARCHMENT_WARM}"  stop-opacity="0.97"/>
    </linearGradient>

    <!-- Gold top border gradient -->
    <linearGradient id="grad-top" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
      <stop offset="0"   stop-color="{GOLD_BRIGHT}"  stop-opacity="1.0"/>
      <stop offset="0.5" stop-color="{GOLD_DARK}"    stop-opacity="0.9"/>
      <stop offset="1"   stop-color="{PARCHMENT_TAN}" stop-opacity="0.8"/>
    </linearGradient>

    <!-- Gold bottom border gradient (mirror) -->
    <linearGradient id="grad-bottom" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
      <stop offset="0"   stop-color="{PARCHMENT_TAN}" stop-opacity="0.8"/>
      <stop offset="0.5" stop-color="{GOLD_DARK}"     stop-opacity="0.9"/>
      <stop offset="1"   stop-color="{SHADOW}"         stop-opacity="0.6"/>
    </linearGradient>

    <!-- Corner dark vignette -->
    <radialGradient id="grad-corner" cx="0" cy="0" r="1" gradientUnits="objectBoundingBox">
      <stop offset="0"   stop-color="{CORNER_DARK}"  stop-opacity="0.7"/>
      <stop offset="0.6" stop-color="{GOLD_DARK}"    stop-opacity="0.5"/>
      <stop offset="1"   stop-color="{PARCHMENT_TAN}" stop-opacity="0.0"/>
    </radialGradient>

    <!-- Drop shadow for side edges -->
    <linearGradient id="grad-shadow-left" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
      <stop offset="0" stop-color="{SHADOW}" stop-opacity="0.3"/>
      <stop offset="1" stop-color="{SHADOW}" stop-opacity="0.0"/>
    </linearGradient>
    <linearGradient id="grad-shadow-right" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
      <stop offset="0" stop-color="{SHADOW}" stop-opacity="0.0"/>
      <stop offset="1" stop-color="{SHADOW}" stop-opacity="0.3"/>
    </linearGradient>
{pattern_def}
  </defs>

  <!-- ══════════════════════════════════════════
       HINT ELEMENTS — KDE uses these for margins
       ═════════════════════════════════════════= -->
  <g id="hint-tile-center">
    <rect width="1" height="1" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-top-margin">
    <rect width="1" height="4" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-bottom-margin">
    <rect width="1" height="4" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-left-margin">
    <rect width="4" height="1" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-right-margin">
    <rect width="4" height="1" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-top-inset">
    <rect width="1" height="4" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-bottom-inset">
    <rect width="1" height="4" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-left-inset">
    <rect width="4" height="1" x="0" y="0" fill="none"/>
  </g>
  <g id="hint-right-inset">
    <rect width="4" height="1" x="0" y="0" fill="none"/>
  </g>

  <!-- ══════════════════════════════════════════
       CENTER — parchment fill, tiled horizontally
       ViewBox: x=10,y=10 w=137 h=44
       ═════════════════════════════════════════= -->
  <g id="center" transform="translate(10,10)">
    <rect id="center-bg" x="0" y="0" width="137" height="44"
          fill="{center_fill}" />
    <!-- Subtle grain overlay via semi-transparent lines -->
    <rect x="0" y="0" width="137" height="44"
          fill="none" stroke="{PARCHMENT_TAN}" stroke-opacity="0.06"
          stroke-width="0.5"/>
  </g>

  <!-- ══════════════════════════════════════════
       TOP EDGE — gold border strip
       ═════════════════════════════════════════= -->
  <g id="top" transform="translate(10,0)">
    <rect x="0" y="0" width="137" height="10"
          fill="url(#grad-top)"/>
    <!-- Fine gold line at very top -->
    <line x1="0" y1="1" x2="137" y2="1"
          stroke="{GOLD_BRIGHT}" stroke-width="1.5" stroke-opacity="0.9"/>
  </g>

  <!-- ══════════════════════════════════════════
       BOTTOM EDGE
       ═════════════════════════════════════════= -->
  <g id="bottom" transform="translate(10,54)">
    <rect x="0" y="0" width="137" height="10"
          fill="url(#grad-bottom)"/>
    <line x1="0" y1="9" x2="137" y2="9"
          stroke="{SHADOW}" stroke-width="1" stroke-opacity="0.5"/>
  </g>

  <!-- ══════════════════════════════════════════
       LEFT EDGE — shadow vignette
       ═════════════════════════════════════════= -->
  <g id="left" transform="translate(0,10)">
    <rect x="0" y="0" width="10" height="44"
          fill="{edge_fill}"/>
    <rect x="0" y="0" width="10" height="44"
          fill="url(#grad-shadow-left)"/>
  </g>

  <!-- ══════════════════════════════════════════
       RIGHT EDGE
       ═════════════════════════════════════════= -->
  <g id="right" transform="translate(147,10)">
    <rect x="0" y="0" width="10" height="44"
          fill="{edge_fill}"/>
    <rect x="0" y="0" width="10" height="44"
          fill="url(#grad-shadow-right)"/>
  </g>

  <!-- ══════════════════════════════════════════
       CORNERS — gold + dark vignette + scroll ornament
       ═════════════════════════════════════════= -->

  <!-- top-left -->
  <g id="topleft">
    <rect x="0" y="0" width="10" height="10" fill="url(#grad-top)"/>
    <!-- Scroll curl ornament — top-left quarter arc -->
    <path d="M 2,10 Q 2,2 10,2" fill="none"
          stroke="{GOLD_BRIGHT}" stroke-width="1.2" stroke-opacity="0.85"/>
    <path d="M 1,10 Q 1,1 10,1" fill="none"
          stroke="{GOLD_DARK}" stroke-width="0.5" stroke-opacity="0.6"/>
  </g>

  <!-- top-right -->
  <g id="topright" transform="translate(147,0)">
    <rect x="0" y="0" width="10" height="10" fill="url(#grad-top)"/>
    <path d="M 8,10 Q 8,2 0,2" fill="none"
          stroke="{GOLD_BRIGHT}" stroke-width="1.2" stroke-opacity="0.85"/>
    <path d="M 9,10 Q 9,1 0,1" fill="none"
          stroke="{GOLD_DARK}" stroke-width="0.5" stroke-opacity="0.6"/>
  </g>

  <!-- bottom-left -->
  <g id="bottomleft" transform="translate(0,54)">
    <rect x="0" y="0" width="10" height="10" fill="url(#grad-bottom)"/>
    <path d="M 2,0 Q 2,8 10,8" fill="none"
          stroke="{GOLD_DARK}" stroke-width="1" stroke-opacity="0.6"/>
  </g>

  <!-- bottom-right -->
  <g id="bottomright" transform="translate(147,54)">
    <rect x="0" y="0" width="10" height="10" fill="url(#grad-bottom)"/>
    <path d="M 8,0 Q 8,8 0,8" fill="none"
          stroke="{GOLD_DARK}" stroke-width="1" stroke-opacity="0.6"/>
  </g>

</svg>
"""
    return svg


if __name__ == "__main__":
    import sys
    embed_patch = "--no-patch" not in sys.argv

    print("Extracting parchment texture patch...")
    patch_b64 = get_parchment_patch_b64(size=128) if embed_patch else None
    if patch_b64:
        print(f"  Patch embedded: {len(patch_b64)//1024}KB base64")
    else:
        print("  Using gradient fallback (no patch)")

    print("Generating SVG...")
    svg_content = generate_svg(patch_b64)

    WIDGETS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = WIDGETS_DIR / "panel-background.svg"
    out_path.write_text(svg_content, encoding="utf-8")
    print(f"  Written: {out_path} ({out_path.stat().st_size // 1024}KB)")

    # Also write metadata.desktop for the theme
    meta_path = THEME_DIR / "metadata.desktop"
    if not meta_path.exists():
        meta_path.write_text("""\
[Desktop Entry]
Name=Void Dragon
Comment=DragonFable-inspired parchment panel theme for KDE Plasma
X-KDE-PluginInfo-Name=void-dragon
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-Author=linux-ricing
X-KDE-PluginInfo-Email=
X-KDE-PluginInfo-Website=
X-KDE-PluginInfo-Category=
X-KDE-PluginInfo-Depends=
X-KDE-PluginInfo-License=GPL
X-KDE-PluginInfo-EnabledByDefault=true
X-Plasma-API=5.0
""", encoding="utf-8")
        print(f"  Wrote: {meta_path}")

    print("\nDone. To apply:")
    print("  plasma-apply-desktoptheme void-dragon")
    print("  qdbus6 org.kde.KWin /KWin reconfigure")
    print("\nTo undo:")
    print("  plasma-apply-desktoptheme default")
