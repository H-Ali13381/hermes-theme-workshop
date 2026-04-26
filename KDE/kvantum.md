# Kvantum Widget Style

Kvantum replaces the entire Qt widget renderer — buttons, scrollbars, dropdowns, checkboxes. This is the **biggest visual impact** layer in the KDE ricing stack.

## Installation

```bash
sudo pacman -S kvantum qt6ct
yay -S kvantum-theme-catppuccin-git
```

## Configuration

Config location: `~/.config/Kvantum/kvantum.kvconfig`

```ini
[General]
theme=catppuccin-mocha-teal
```

After writing the config, set the KDE widget style:

```bash
kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum
qdbus6 org.kde.KWin /KWin reconfigure
```

## Available Catppuccin-Mocha Kvantum Themes

All installed via `kvantum-theme-catppuccin-git`:

| Theme Name | Accent Color |
|-----------|-------------|
| `catppuccin-mocha-mauve` | Purple |
| `catppuccin-mocha-teal` | Cyan (used by void-dragon) |
| `catppuccin-mocha-peach` | Warm amber/gold |
| `catppuccin-mocha-maroon` | Dark crimson |
| `catppuccin-mocha-red` | Bright crimson |
| `catppuccin-mocha-yellow` | Gold |

Check installed themes:
```bash
find /usr/share/Kvantum ~/.local/share/Kvantum -maxdepth 1 -type d
```

## Qt SVG Renderer Limitations

Kvantum and Plasma theme SVGs are rendered by Qt's SVG engine, NOT a browser or Inkscape. Qt silently ignores many SVG features:

### UNSUPPORTED (silently ignored)
- `<pattern>` elements (including embedded `<image>` or `data:` URIs inside patterns)
- `feTurbulence`, `feDisplacementMap`, `feColorMatrix`, and ALL SVG filters
- CSS `filter:` properties
- `data:` URI hrefs in `<image>` elements
- `<foreignObject>`

### SUPPORTED
- `linearGradient`, `radialGradient`
- `<rect>`, `<path>`, `<line>`, `<circle>`, `<ellipse>`
- `fill`, `stroke`, `stroke-width`, `opacity`, `stop-color`, `stop-opacity`
- Basic CSS class fills via `<style>` (`ColorScheme-Background` class works)
- `transform="translate(...)"`

**Consequence:** You CANNOT embed a texture PNG via `<pattern>` or base64 data: URI.

## Pitfalls

- **`widgetStyle=kvantum-dark` is WRONG** and silently falls back to Breeze. The correct value is `widgetStyle=kvantum` (lowercase, no suffix). Maps to `/usr/lib/qt6/plugins/styles/libkvantum.so`.
- **`materialize_kvantum` must call `qdbus6 org.kde.KWin /KWin reconfigure`** after writing. Without this, KWin doesn't pick up the change until next login.
- **Already-open Qt apps** need to be closed and reopened to pick up Kvantum changes.
- **PRESETS missing `kvantum_theme`** silently fall back to `"kvantum-dark"` which is almost certainly not installed. Every preset must include `"kvantum_theme"` explicitly.
