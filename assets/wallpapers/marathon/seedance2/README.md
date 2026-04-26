# Marathon 2025 — Animated Wallpapers (Seedance v2)

Three animated wallpaper variants generated for the Marathon 2025 desktop theme.
Each was generated via FAL + Seedance image-to-video from a static theme reference.

## Variants

| File | Theme | Palette character |
|------|-------|-------------------|
| `chrysalis.mp4` | Chrysalis | Deep purples, violet haze, cosmic transformation |
| `cortex.mp4` | Cortex | Dark teal, blue-green neural tones, dark steel |
| `extraction.mp4` | Extraction | Steel blue, slate grey, cold white highlights |

## Usage

With awww (swww v0.12+):

```bash
# Start daemon if not running
pgrep awww-daemon || (awww-daemon & sleep 2)

# Set wallpaper (transition: fade)
awww img ~/.config/wallpapers/marathon/seedance2/chrysalis.mp4 \
  --transition-type fade --transition-duration 2

# Or use mpvpaper for true video loop
mpvpaper '*' ~/.config/wallpapers/marathon/seedance2/chrysalis.mp4 \
  -o "no-audio loop"
```

## Source

Preview image: `assets/previews/marathon2025-themes.png`
Generated: April 2026 via `fal-ai/seedance-1-lite`
