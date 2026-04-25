# Cursor Theme Options

Installed cursor themes on this system.

## Available

| Theme | Accent |
|-------|--------|
| `breeze_cursors` | KDE default |
| `catppuccin-macchiato-teal-cursors` | Cyan / teal |
| `catppuccin-macchiato-mauve-cursors` | Purple |
| `catppuccin-macchiato-yellow-cursors` | Gold |
| `catppuccin-macchiato-red-cursors` | Red |
| `catppuccin-macchiato-green-cursors` | Green |
| `catppuccin-macchiato-blue-cursors` | Blue |
| `catppuccin-macchiato-pink-cursors` | Pink |
| `catppuccin-macchiato-sapphire-cursors` | Deep blue |
| `catppuccin-macchiato-sky-cursors` | Light blue |
| `catppuccin-macchiato-maroon-cursors` | Dark red |
| `catppuccin-macchiato-peach-cursors` | Orange / peach |
| `catppuccin-macchiato-lavender-cursors` | Lavender |
| `catppuccin-macchiato-flamingo-cursors` | Coral |
| `catppuccin-macchiato-rosewater-cursors` | Soft pink |

## Recommendation Mapping

- Void / cyan themes → `catppuccin-macchiato-teal-cursors`
- Gold / parchment themes → `catppuccin-macchiato-yellow-cursors`
- Doom / crimson themes → `catppuccin-macchiato-maroon-cursors` or `...-red-cursors`
- Arcane / purple themes → `catppuccin-macchiato-mauve-cursors`

## Apply Manually

```bash
plasma-apply-cursortheme "catppuccin-macchiato-teal-cursors"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "catppuccin-macchiato-teal-cursors"
``` 

## Real Capture References

Real captured references should live in per-option folders:

- `catppuccin-macchiato-teal-cursors/preview.png`
- `catppuccin-macchiato-mauve-cursors/preview.png`
- `catppuccin-macchiato-yellow-cursors/preview.png`
- `catppuccin-macchiato-red-cursors/preview.png`

Generate them with:

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/capture_theme_references.py \
  --category cursors
```

This script restores a Breeze Dark baseline, standardizes Breeze icons/cursor/panel theme,
applies one cursor theme, captures the screenshot with the pointer enabled, saves it to the
correct catalog folder, then restores the baseline.

## Preset Key

```python
"cursor_theme": "catppuccin-macchiato-teal-cursors"
```