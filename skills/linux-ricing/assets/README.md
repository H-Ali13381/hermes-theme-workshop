# Hermes Ricer Assets

Preview images, reference materials, and palette swatches for the ricing workflow.

## Directory Structure

```
assets/
├── catalog/       # Decision-making references for customization choices
├── previews/      # Before/after screenshots of applied themes
├── references/    # Style reference images (DragonFable, inspiration)
├── palettes/      # Color palette swatches (generated or extracted)
└── scripts/       # Asset generation helpers
```

## catalog/

This is the important part for user choice. It contains curated READMEs for common
ricing dimensions so the user can compare categories before deciding what to customize.

Categories:
- `catalog/palettes/` — overall color direction and mood
- `catalog/terminals/` — kitty vs Konsole vs Alacritty vs WezTerm
- `catalog/bars/` — KDE panel vs waybar vs polybar
- `catalog/launchers/` — rofi vs wofi vs dmenu
- `catalog/notifications/` — dunst vs mako vs swaync
- `catalog/kvantum/` — installed Qt widget themes on this machine
- `catalog/cursors/` — installed cursor theme options on this machine
- `catalog/themes/` — major desktop layers: colorscheme, panel, wallpaper, GTK, etc.

Use this catalog when the user says things like:
- "What can I customize?"
- "Show me options"
- "What do people usually rice on Linux?"
- "Help me compare before choosing"

The goal is not just to apply a theme, but to help the user choose among common ricing elements.

## Current Assets

### previews/
| File | Description |
|------|-------------|
| `toolbar_crop.png` | Cropped KDE panel for style transfer |
| `toolbar_crop_fullres.png` | Full-resolution panel crop |
| `toolbar_content.png` | Full toolbar content screenshot |
| `toolbar_parchment_mockup.png` | AI-generated parchment-style mockup |
| `bottom_strip.png` | Bottom panel strip |

### references/
| File | Description |
|------|-------------|
| `df_style_ref_hud.png` | DragonFable HUD style reference |
| `df_style_ref_scroll.png` | DragonFable scroll UI style reference |

### palettes/
Empty — place extracted/generated palettes here (PNG swatches, JSON palette files).

## Adding New Assets

1. Place file in appropriate subdirectory
2. Add entry to the table above
3. Commit to dotfiles: `dotfiles add -A ~/.hermes/skills/creative/linux-ricing/assets/`

## Generating Previews

After applying a theme, capture screenshots:

    spectacle -r -o ~/.hermes/skills/creative/linux-ricing/assets/previews/

Then crop and name appropriately.