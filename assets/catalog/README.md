# Ricing Catalog

Visual reference for available customization options. Browse categories below to see what's available.

## Categories

| Category | Description |
|----------|-------------|
| [palettes/](palettes/) | Color schemes — Nord, Gruvbox, Dracula, Catppuccin, Tokyo Night, Rose Pine, custom |
| [terminals/](terminals/) | Terminal emulators — kitty, Alacritty, WezTerm, Konsole |
| [bars/](bars/) | Status bars — waybar, polybar |
| [launchers/](launchers/) | App launchers — rofi, wofi, dmenu |
| [notifications/](notifications/) | Notification daemons — dunst, mako |
| [kvantum/](kvantum/) | Qt widget themes — Catppuccin variants, Nordic, etc. |
| [cursors/](cursors/) | Mouse cursor themes |
| [themes/](themes/) | Full desktop themes — Plasma, splash screens |

## How to Use

1. Browse the category folders above
2. Open `examples.svg` inside each category to compare the visual role of that customization layer
3. Read the category README for package choices, recommendations, and install/apply notes
4. Edit your preset in `ricer.py` to include your choices
5. Run `ricer preset <name>` to apply

## Example Images

Each category now includes a generated `examples.svg` reference sheet:

| Category | Example image |
|----------|---------------|
| palettes | `palettes/examples.svg` |
| terminals | `terminals/examples.svg` |
| bars | `bars/examples.svg` |
| launchers | `launchers/examples.svg` |
| notifications | `notifications/examples.svg` |
| kvantum | `kvantum/examples.svg` |
| cursors | `cursors/examples.svg` |
| themes | `themes/examples.svg` |

These are comparison/mockup boards to help the user decide what they want to customize before implementation.

## Real Capture Pipeline

For ground-truth references, use:

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/capture_theme_references.py --category kvantum
python3 ~/.hermes/skills/creative/linux-ricing/scripts/capture_theme_references.py --category cursors
```

This pipeline:
1. Restores a Breeze Dark KDE baseline
2. Standardizes default Plasma theme, Breeze cursor, and Breeze icons
3. Applies one customization only
4. Captures a real screenshot
5. Saves it to `assets/catalog/<category>/<option>/preview.png`
6. Restores baseline before the next capture

Use the generated per-option preview folders as the canonical catalog once real captures exist.

## Adding New Options

To add a new option to the catalog:

1. Create folder: `assets/catalog/<category>/<name>/`
2. Add `README.md` with description and install command
3. Add preview screenshots if available
4. Update this index