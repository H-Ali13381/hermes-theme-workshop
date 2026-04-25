# Plasma Panel / Theme SVGs

The panel background (taskbar) is NOT controlled by colorschemes or Kvantum. It is controlled by a **Plasma theme** — SVG files under:

```
~/.local/share/plasma/desktoptheme/<theme-name>/
```

## Required SVG Element IDs

The key file is `widgets/panel-background.svg`. KDE uses named element IDs to locate regions. These MUST exist or KDE silently ignores the file:

```
center, top, bottom, left, right,
topleft, topright, bottomleft, bottomright,
hint-tile-center
```

## Important Plasma Theme SVG Files

| File | Controls |
|------|----------|
| `widgets/panel-background.svg` | The panel bar itself |
| `widgets/tasks.svg` | Active/inactive taskbar buttons |
| `widgets/tooltip.svg` | Tooltip popups |
| `widgets/plasmoidheading.svg` | Widget title bars |
| `dialogs/background.svg` | System dialogs, notification popups |
| `colors` | Fallback color hints (text, shadows) |
| `metadata.desktop` | Theme name, author, KDE version compat |

## Applying a Custom Plasma Theme

```bash
plasma-apply-desktoptheme <theme-name>
```

## SVG Template Theming

Use placeholder strings in SVGs and substitute palette values:

```python
svg = Path("panel-background.svg").read_text()
for key, val in palette.items():
    svg = svg.replace(f"RICER_{key.upper()}", val)
Path("panel-background-themed.svg").write_text(svg)
```

## Real Texture Alternatives (ranked by quality)

Since Qt's SVG renderer cannot handle textures, use these workarounds:

1. **Semi-transparent panel + textured wallpaper** — easiest, most common
2. **Kvantum** — supports PNG tile textures for Qt widget surfaces (not panel bg)
3. **QML plasmoid** — full QtQuick with `Image{}` elements, real PNGs, drop shadows
4. **Waybar with CSS** — replace KDE panel entirely; CSS supports `background-image`, `border-image`

SVG Plasma themes are suitable only for: flat colors, gradients, rounded corners.

## Pitfalls

- **SVGs with wrong element IDs are silently ignored.** KDE will not error — the panel will use its fallback theme.
- **Cannot embed textures** via `<pattern>` or base64 `data:` URI — Qt silently ignores both.
- **`plasma-apply-desktoptheme` requires** the theme directory to exist under `~/.local/share/plasma/desktoptheme/` or `/usr/share/plasma/desktoptheme/`.
