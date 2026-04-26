# Plasma Panel / Theme SVGs

## What does NOT theme the Plasma panel

This is the most common source of "the rice looks great in the preview but the panel is still default" failures. The Plasma panel background — the actual taskbar strip and its tray/launcher slots — is **not** affected by:

- The active **colorscheme** (`.colors` file via `plasma-apply-colorscheme`). Colorschemes only retint Qt window chrome, menus, selection states, and a handful of fallback hints. The panel SVG ignores them.
- **Kvantum**. Kvantum re-skins Qt widgets *inside* windows (buttons, scrollbars, tabs). The Plasma panel is a plasmoid container, not a Qt widget — Kvantum cannot reach it.
- **GTK** themes, icon themes, cursor themes.

The panel background is controlled by a **Plasma theme** — SVG files under:

```
~/.local/share/plasma/desktoptheme/<theme-name>/
```

If a Step 4 preview shows a custom-colored, textured, or shaped panel, applying a colorscheme + Kvantum will not produce it. You must either ship a matching Plasma theme, replace the panel with an EWW overlay, or surface the limitation to the user. **Do not pretend the result matches.**

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

## When the panel can't match the preview

If the Step 4 preview specifies a panel that the Plasma theme SVG renderer cannot reproduce (image textures, photographic backgrounds, irregular shapes, per-region blur, raster shadows), the Step 6 implementation contract triggers. Stop, present these three options to the user, and record their choice in session.md:

1. **Plasma theme SVG (closest-flat-equivalent).** Reduce the preview to flat colors + gradients + rounded corners and ship a custom Plasma theme. Cheapest path; honest about the loss. Explicitly call out which preview details (texture, shadow, raster art) are dropped.
2. **EWW overlay panel.** Hide the Plasma panel (`qdbus6 … panels().forEach(p => p.hiding = "windowscancover")` — see `KDE/widgets.md` §4) and render the high-fidelity panel as an EWW window. EWW supports CSS `background-image`, `border-image`, real shadows, hover/animation, and arbitrary shapes. Cost: lose the Plasma system-tray ergonomics (network, bluetooth, battery) unless re-implemented in EWW or kept on a secondary Plasma panel.
3. **Accepted limitation.** Keep the default-shaped Plasma panel and document the gap in the handoff. Use this when the user does not want extra moving parts and the panel is not central to the design.

The decision is the user's. The agent's job is to surface it — not to silently pick option 1 and call it done. Whichever is chosen, log it via `append-item` (e.g. `panel: accepted-deviation: preview shows photo texture; using flat Plasma SVG (user OK)`).

## Pitfalls

- **SVGs with wrong element IDs are silently ignored.** KDE will not error — the panel will use its fallback theme.
- **Cannot embed textures** via `<pattern>` or base64 `data:` URI — Qt silently ignores both.
- **`plasma-apply-desktoptheme` requires** the theme directory to exist under `~/.local/share/plasma/desktoptheme/` or `/usr/share/plasma/desktoptheme/`.
