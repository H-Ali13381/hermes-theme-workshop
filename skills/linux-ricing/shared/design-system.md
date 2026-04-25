# Design System — 10-Key Palette Schema

## JSON Structure

```json
{
  "name": "my-theme",
  "description": "One-sentence description.",
  "palette": {
    "background": "#0c1220",
    "foreground": "#e4f0ff",
    "primary":    "#7ad4f0",
    "secondary":  "#0d2e32",
    "accent":     "#d4a012",
    "surface":    "#1c1e2a",
    "muted":      "#3d2214",
    "danger":     "#cc3090",
    "success":    "#2a8060",
    "warning":    "#c87820"
  },
  "kvantum_theme": "catppuccin-mocha-teal",
  "cursor_theme": "catppuccin-macchiato-teal-cursors",
  "icon_theme": "Papirus-Dark",
  "gtk_theme": "Adwaita-dark",
  "mood_tags": ["dark", "dragon", "cyan"]
}
```

All 10 palette keys are required. Every preset must also include `kvantum_theme`, `cursor_theme`, `icon_theme`, and `gtk_theme`.

## Color Derivation Algorithms

### YIQ Automatic Text Color

Never hardcode foreground for text on a colored background:

```python
def yiq_text_color(hex_color):
    """Return '#ffffff' or '#000000' based on perceptual brightness."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return '#000000' if yiq >= 128 else '#ffffff'
```

Green carries 58.7% of perceived brightness — a saturated green that looks light needs dark text even though HSL says 50%.

### Hue Rotation

```python
def rotate_hue(hex_color, degrees):
    """Shift hue by degrees, preserving saturation and value."""
    r, g, b = hex_to_rgb_tuple(hex_color)
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    h = (h + degrees / 360.0) % 1.0
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return rgb_tuple_to_hex(int(r2*255), int(g2*255), int(b2*255))
```

### Blend

```python
def blend_hex(hex_a, hex_b, t=0.5):
    """Linear RGB mix. t=0 returns a, t=1 returns b."""
    ra, ga, ba = hex_to_rgb_tuple(hex_a)
    rb, gb, bb = hex_to_rgb_tuple(hex_b)
    return rgb_tuple_to_hex(
        int(ra + (rb - ra) * t),
        int(ga + (gb - ga) * t),
        int(ba + (bb - ba) * t)
    )
```

### Adjust Lightness

```python
def adjust_lightness(hex_color, factor):
    """Multiply HSL lightness. factor < 1 darkens, > 1 lightens."""
    r, g, b = hex_to_rgb_tuple(hex_color)
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    l = min(1.0, max(0.0, l * factor))
    r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
    return rgb_tuple_to_hex(int(r2*255), int(g2*255), int(b2*255))
```

## 10-Key → 16 ANSI Color Mapping

```
color0  (black)   → surface
color1  (red)     → danger
color2  (green)   → success
color3  (yellow)  → warning
color4  (blue)    → primary   (swap to secondary if primary==warning)
color5  (magenta) → secondary
color6  (cyan)    → accent
color7  (white)   → foreground

color8  (bright black)   → muted  × 1.4 lightness
color9  (bright red)     → danger  rotate +15°, × 1.3 lightness
color10 (bright green)   → success rotate +10°, × 1.3 lightness
color11 (bright yellow)  → warning × 1.3 lightness
color12 (bright blue)    → primary rotate -10°, × 1.3 lightness
color13 (bright magenta) → secondary rotate +20°, × 1.3 lightness
color14 (bright cyan)    → accent  rotate +15°, × 1.3 lightness
color15 (bright white)   → foreground × 1.25 lightness
```

## SVG Template Theming

Use placeholder strings in SVG files and substitute palette values:

```python
svg = Path("panel-background.svg").read_text()
for key, val in palette.items():
    svg = svg.replace(f"RICER_{key.upper()}", val)
Path("panel-background-themed.svg").write_text(svg)
```

## Materializer Contract

Every `materialize_<app>()` function must:

1. Accept `(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]`
2. On `dry_run=True`: return change dicts describing what WOULD happen (no writes)
3. Before any write: call `backup_file(path, backup_ts, "app/filename")` for each file
4. Inject include/source directives with a `# linux-ricing` marker for clean undo
5. Return a list of change dicts, one per file written or action taken
