# Kvantum Theme Options

Installed Qt widget themes on this system. These affect buttons, menus, scrollbars, checkboxes, and other Qt controls.

## Recommended Picks

### Catppuccin Mocha Variants
Best for dark themes. Pick accent color by palette:

| Theme | Best for |
|-------|----------|
| `catppuccin-mocha-teal` | Cyan / void / blue-green themes |
| `catppuccin-mocha-mauve` | Purple / arcane / gothic themes |
| `catppuccin-mocha-peach` | Amber / gold / warm themes |
| `catppuccin-mocha-maroon` | Dark red / crimson themes |
| `catppuccin-mocha-red` | Bright red accents |
| `catppuccin-mocha-yellow` | Gold / sand / parchment themes |
| `catppuccin-mocha-sky` | Brighter blue-cyan themes |
| `catppuccin-mocha-sapphire` | Deep blue themes |
| `catppuccin-mocha-green` | Emerald / nature themes |
| `catppuccin-mocha-pink` | Pink / neon themes |

### Built-in Kvantum Themes
| Theme | Style |
|-------|-------|
| `KvArcDark` | Flat modern dark |
| `KvDark` | Generic dark |
| `KvAdaptaDark` | Material-inspired dark |
| `KvMojave` | macOS-inspired |
| `KvYaru` | Ubuntu-inspired |
| `KvOxygen` | Classic KDE |

## How to Choose

- Want strong contrast and modern polished widgets? → Catppuccin Mocha
- Want neutral/boring but safe? → KvArcDark or KvDark
- Want warm parchment/gold? → Catppuccin Mocha Yellow or Peach
- Want void-dragon cyan? → Catppuccin Mocha Teal

## Apply Manually

```bash
mkdir -p ~/.config/Kvantum
echo -e "[General]\ntheme=catppuccin-mocha-teal" > ~/.config/Kvantum/kvantum.kvconfig
kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum
qdbus6 org.kde.KWin /KWin reconfigure
```

## Real Capture References

Real captured references should live in per-option folders:

- `catppuccin-mocha-teal/preview.png`
- `catppuccin-mocha-mauve/preview.png`
- `catppuccin-mocha-peach/preview.png`
- `catppuccin-mocha-yellow/preview.png`

Generate them with:

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/capture_theme_references.py \
  --category kvantum
```

This script restores a Breeze Dark baseline, standardizes Breeze icons/cursor/panel theme,
applies one Kvantum theme, takes a screenshot, saves it to the correct catalog folder,
then restores the baseline before moving to the next option.

## Preset Key

In `ricer.py` presets:

```python
"kvantum_theme": "catppuccin-mocha-teal"
```