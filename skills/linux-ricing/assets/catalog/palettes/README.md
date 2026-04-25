# Palette Options

Common color-direction choices for Linux ricing. These are conceptual palette families the user can pick from before implementation.

## Popular Dark Palettes

| Palette | Vibe | Typical Colors |
|---------|------|----------------|
| Catppuccin Mocha | Soft polished dark | Navy, lavender, peach, teal |
| Nord | Arctic, muted, clean | Slate blue, icy cyan |
| Gruvbox Dark | Retro warm terminal | Brown, mustard, muted green |
| Dracula | Neon dark | Purple, pink, orange |
| Tokyo Night | Futuristic cool dark | Deep blue, cyan, magenta |
| Rose Pine | Cozy dark, romantic | Mauve, rose, pine green |
| Doom Knight | Gothic fantasy | Black, gold, purple, crimson |
| Void Dragon | Void fantasy / cyan-gold | Void blue, cyan, gold, magenta |

## Popular Light / Warm Palettes

| Palette | Vibe | Typical Colors |
|---------|------|----------------|
| Catppuccin Latte | Soft pastel light | Cream, blue, rose |
| Solarized Light | Technical beige | Warm beige, blue, cyan |
| Parchment / Scroll | Fantasy manuscript | Tan, brown, gold, dark ink |
| Sepia | Vintage terminal | Sand, brown, amber |

## How to Decide

Pick 1 mood + 1 accent direction:
- Cool / minimal → Nord, Tokyo Night
- Warm / retro → Gruvbox, parchment, sepia
- Soft / polished → Catppuccin
- Dark fantasy → Doom Knight, Void Dragon
- Neon / cyberpunk → Dracula, Tokyo Night

## Palette Keys Used by ricer

Every preset needs these 10 keys:

```json
background, foreground, primary, secondary, accent,
surface, muted, danger, success, warning
```

## Recommendation Flow

1. Pick mood: minimalist / cozy / fantasy / cyberpunk / parchment
2. Pick primary accent: cyan / gold / purple / red / green
3. Pick UI density: soft rounded / flat sharp / ornate
4. Then map to Kvantum, cursor, GTK, wallpaper, and terminal theme choices