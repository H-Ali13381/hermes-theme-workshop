# Palette Extraction — Image to Design System

## Overview

Deterministic extraction of a 10-key design system palette from any image.
CLI: `ricer extract --image WALLPAPER [--out design.json] [--name NAME]`

Depends on Pillow only. Same image → same palette (deterministic).

## 4 Vision Passes (Subagent Method)

When using a vision-capable subagent for analysis:

1. **Background / environment colors** — sky, ambient, negative space
2. **Character/subject primary colors** — armor, skin, material
3. **Accent / glow / energy colors** — highlights, light sources
4. **Decorative elements** — frame, trim, filigree, UI chrome

Use `delegate_task` with toolsets `["vision", "file"]` — NOT browser vision (returns blank for local files).

## Pillow Deterministic Algorithm

### 1. Load + Alpha-Composite
Open image, composite alpha over neutral gray (`#808080`) so transparent regions don't bias toward black. Convert to RGB.

### 2. Downsample
Thumbnail to 400×400 max. Preserves perceptual structure, 10×+ faster.

### 3. Quantize
```python
img.quantize(colors=12, method=Image.Quantize.MAXCOVERAGE, kmeans=0)
```
MAXCOVERAGE biases toward covering color space (catches narrow accent clusters). Falls back to MEDIANCUT on error.

### 4. Classify
Each swatch is assigned to one of 6 ricemood buckets via HLS thresholds (`s > 0.4` for "vibrant", `l ∈ (0.25, 0.75)` for "mid"):
- **Vibrant** — most vivid, mid-luminance
- **LightVibrant** — bright vivid (high L, high S)
- **DarkVibrant** — dark vivid (low L, high S)
- **Muted** — desaturated mid
- **LightMuted** — light desaturated
- **DarkMuted** — dark desaturated

Swatches sorted by `(-pixel_count, hex_string)` before classification for determinism.

### 5. Assign 10 Semantic Slots

| Slot | Primary Source | Fallback Cascade |
|------|---------------|-----------------|
| background | DarkMuted (darkest) | DarkVibrant ×0.6 lightness → `#0a0a0a` |
| foreground | LightMuted (lightest) | LightVibrant → yiq-contrast of background |
| primary | Vibrant, max chroma | LightVibrant → DarkVibrant → `rotate_hue(foreground, 210°)` |
| secondary | DarkVibrant, max chroma | Vibrant ×0.6 lightness → primary ×0.65 |
| accent | LightVibrant (hue differs from primary ≥30°) | `rotate_hue(LightVibrant, 20°)` → `rotate_hue(primary, 30°)` |
| surface | Muted, max chroma | `blend(background, #808080, t=0.20)` |
| muted | DarkMuted ×1.3 lightness | `blend(background, #808080, t=0.12)` |
| danger | Saturated swatch, hue ±40° of red (0°) | synthesize `#cc3344` at primary's lightness |
| success | Saturated swatch, hue ±40° of green (120°) | synthesize `#3a9b5c` at primary's lightness |
| warning | Saturated swatch, hue ±35° of amber (45°) | synthesize `#d4a012` at primary's lightness |

"Saturated" = `s ≥ 0.3` in HLS. Semantic-hue slots (danger/success/warning) are role-based, not triadic — avoids collisions when primary is already red/amber/green.

### 6. Validate
- **Contrast:** Enforce `abs(yiq(bg) − yiq(fg)) ≥ 128` (≈ 4.5:1 AA-equivalent). Lighten/darken foreground until met.
- **Uniqueness:** No two slots share a hex. Perturb duplicates by `adjust_lightness ±15%` + `rotate_hue 20°`. Falls back to blend toward `primary` when stuck at pure black/white.

### 7. Mood Tags
2-3 inferred from aggregate palette: mean lightness → dark/light, mean saturation → vibrant/muted, primary hue bucket → warm/cool/amber/violet.

## Collision Defense

The `primary == warning` ANSI-blue collision is fixed at materializer stage: when detected, ANSI color4 swaps to `secondary`. The extractor's uniqueness pass catches other collisions at palette-gen time.

## Python API

```python
from palette_extractor import extract_palette
design = extract_palette("/path/to/wallpaper.jpg", name="my-theme")
# Returns: {"name": ..., "description": ..., "palette": {...}, "mood_tags": [...]}
```
