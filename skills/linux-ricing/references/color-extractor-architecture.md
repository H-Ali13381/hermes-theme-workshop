# Color Extractor — Architecture Decision

## Current State
`scripts/palette_extractor.py` uses HLS with manual thresholds (S≥0.45, L∈[0.15,0.85]).
**Problem:** HLS is geometrically broken for perceptual work. Yellow at L=0.5 looks twice as bright as blue at L=0.5. Threshold tweaking is patching symptoms of using the wrong color model.

## Agreed Next Architecture: Matugen-First Hybrid

### Priority order
1. **Check for `matugen`** (common in Hyprland ecosystem) → call as subprocess, map MD3 color roles to 10-key schema
2. **Fall back to OKLCH-aware Python** — perceptually uniform, chroma C > 0.15 reliably means "vivid" regardless of hue
3. **HLS extractor** — last resort only, document limitations

### The fundamental insight about semantic slots
`danger/success/warning` must **always be synthesized** at fixed OKLCH semantic hues.
They don't live in wallpapers. Forcing extraction produces muddy browns for "danger red."

MD3 reference hues (OKLCH):
- Error/Danger: H = 25°, C ≥ 0.84
- Success: H = 145°, C ≥ 0.50
- Warning: H = 60°, C ≥ 0.60

Only `background/foreground/primary/secondary/accent/surface/muted` should be extracted from the image.

### OKLCH chroma thresholds
- C > 0.15 = vibrant/saturated (replace S > 0.35 in HLS)
- C < 0.05 = achromatic/muted
- L > 0.75 = light
- L < 0.35 = dark

### Vibrant.js reference thresholds (industry standard)
```
Vibrant:      S∈[0.35, 1.0], L∈[0.30, 0.70]
LightVibrant: S∈[0.35, 1.0], L∈[0.55, 1.00]
DarkVibrant:  S∈[0.35, 1.0], L∈[0.00, 0.45]
Muted:        S∈[0.00, 0.40], L∈[0.30, 0.70]
Scoring:      Luma×6, Saturation×3, Population×1
```

### matugen subprocess interface
```bash
# Check for matugen
command -v matugen

# Generate from image
matugen image /path/to/wallpaper.png --json hex > /tmp/matugen_out.json

# Map MD3 roles to 10-key schema:
# background    ← surface_dim
# foreground    ← on_surface
# primary       ← primary
# secondary     ← secondary
# accent        ← tertiary
# surface       ← surface_container
# muted         ← surface_variant
# danger        ← error (synthesized)
# success       ← synthesize at H=145°
# warning       ← synthesize at H=60°
```

## References
- [material-color-utilities](https://github.com/material-foundation/material-color-utilities)
- [pywal source](https://github.com/dylanaraps/pywal/blob/master/pywal/colors.py)
- [color.js OKLCH](https://colorjs.io/docs/oklch)
- Vibrant.js source: `node_modules/@vibrant/color/src/color.ts`
