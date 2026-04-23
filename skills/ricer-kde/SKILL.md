---
name: ricer-kde
description: "KDE Plasma theming layer for hermes-ricer. Load when applying or debugging KDE colorscheme, Kvantum widget style, cursor theme, Plasma theme, or panel SVG. Covers the full KDE ricing stack and all known pitfalls."
---

# ricer-kde — KDE Plasma Theming Layer

Part of the hermes-ricer suite. Load this alongside the main `hermes-ricer` skill for any KDE-specific work.

---

## Full KDE Ricing Stack

A colorscheme alone produces subtle changes — only Qt window chrome shifts.
To get dramatic, system-wide transformation, apply ALL layers in order:

### 1. Colorscheme
Qt window borders, titlebars, system menus.

    plasma-apply-colorscheme <name>

The name comes from the `[General] ColorScheme=` key in the `.colors` file.
ricer.py generates and writes `~/.local/share/color-schemes/hermes-<name>.colors` automatically.

### 2. Kvantum (biggest visual impact)
Replaces the entire Qt widget renderer — buttons, scrollbars, dropdowns, checkboxes.

Install:

    sudo pacman -S kvantum qt6ct

Install a theme pack:

    yay -S --aur kvantum-theme-catppuccin-git

Then set the theme:

    mkdir -p ~/.config/Kvantum
    echo -e "[General]\ntheme=<theme-name>" > ~/.config/Kvantum/kvantum.kvconfig
    kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum

Available catppuccin-mocha Kvantum accents (all installed via kvantum-theme-catppuccin-git):
- `catppuccin-mocha-mauve`   — purple
- `catppuccin-mocha-teal`    — cyan (used by void-dragon)
- `catppuccin-mocha-peach`   — warm amber/gold
- `catppuccin-mocha-maroon`  — dark crimson
- `catppuccin-mocha-red`     — bright crimson
- `catppuccin-mocha-yellow`  — gold

### 3. Cursor

    plasma-apply-cursortheme "<Theme Name>"
    kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "<Theme Name>"

Note: KDE shows a confirmation popup about system-wide SDDM apply. Normal — dismiss as preferred.

### 4. Splash screen

    kwriteconfig6 --file ksplashrc --group KSplash --key Theme <theme-id>
    kwriteconfig6 --file ksplashrc --group KSplash --key Engine KSplashQML

### 5. Live reload

    qdbus6 org.kde.KWin /KWin reconfigure

Already-open Qt apps need to be closed and reopened to pick up Kvantum changes.

---

## KDE Panel / Toolbar Appearance

The panel background (taskbar) is NOT controlled by colorschemes or Kvantum.
It is controlled by a **Plasma theme** — SVG files under:

    ~/.local/share/plasma/desktoptheme/<theme-name>/

The key file is `widgets/panel-background.svg`.

### Required SVG element IDs for panel-background.svg

KDE uses named element IDs to locate regions. These MUST exist or KDE silently ignores the file:

    center, top, bottom, left, right,
    topleft, topright, bottomleft, bottomright,
    hint-tile-center

### Other important Plasma theme SVG files

| File | Controls |
|------|----------|
| `widgets/panel-background.svg` | The panel bar itself |
| `widgets/tasks.svg` | Active/inactive taskbar buttons |
| `widgets/tooltip.svg` | Tooltip popups |
| `widgets/plasmoidheading.svg` | Widget title bars |
| `dialogs/background.svg` | System dialogs, notification popups |
| `colors` | Fallback color hints (text, shadows) |
| `metadata.desktop` | Theme name, author, KDE version compat |

### Applying a custom Plasma theme

    plasma-apply-desktoptheme <theme-name>

### CRITICAL: Qt SVG renderer limitations

Plasma theme SVGs are rendered by Qt's SVG engine, NOT a browser or Inkscape.
Qt silently ignores the following with no error:

    UNSUPPORTED (silently ignored):
      <pattern> elements (including embedded <image> or data: URIs inside patterns)
      feTurbulence, feDisplacementMap, feColorMatrix, and ALL SVG filters
      CSS filter: properties
      data: URI hrefs in <image> elements
      <foreignObject>

    SUPPORTED:
      linearGradient, radialGradient
      <rect>, <path>, <line>, <circle>, <ellipse>
      fill, stroke, stroke-width, opacity, stop-color, stop-opacity
      Basic CSS class fills via <style> (ColorScheme-Background class works)
      transform="translate(...)"

Consequence: you CANNOT embed a parchment PNG texture via `<pattern>` or base64 data: URI.

### Real texture alternatives (ranked by quality)

1. Semi-transparent panel + textured wallpaper behind it — easiest, most common
2. Kvantum — supports PNG tile textures for Qt widget surfaces (not panel bg)
3. QML plasmoid — full QtQuick with Image{} elements, real PNGs, drop shadows
4. Waybar with CSS — replace KDE panel entirely; CSS supports background-image, border-image

SVG Plasma themes are suitable only for: flat colors, gradients, rounded corners.

---

## discover_apps — KDE Sub-system Registration

`kvantum`, `plasma_theme`, and `cursor` have no standalone binary — they are KDE sub-systems.
Without explicit registration, the `APP_MATERIALIZERS` loop silently skips them.

Always ensure this block exists in `discover_apps()`:

```python
if "kde" in apps:
    apps["kvantum"] = {"installed": True}
    apps["plasma_theme"] = {"installed": True}
    apps["cursor"] = {"installed": True}
```

Any future materializer for a KDE sub-system (icon theme, splash, SDDM) MUST be registered
the same way — binary detection will not find it.

---

## snapshot_kde_state — What Gets Captured

The hardened snapshot captures all of these (as of 2026-04-22):

- `active_colorscheme` — from `[General] ColorScheme=` in kdeglobals; falls back to `[KDE] LookAndFeelPackage=`
- `look_and_feel` — `[KDE] LookAndFeelPackage=`
- `kvantum_theme` — from `~/.config/Kvantum/kvantum.kvconfig`
- `widget_style` — `[KDE] widgetStyle=` in kdeglobals
- `plasma_theme` — `[General] lookAndFeelPackage=` in plasmarc
- `cursor_theme` — `[Mouse] cursorTheme=` in kcminputrc
- `wallpaper` — `Image=` from `~/.config/plasma-org.kde.plasma.desktop-appletsrc`

---

## Known Pitfalls

- **NEVER call `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.refreshCurrentShell` on Wayland.**
  It causes plasmashell to exit without restarting, killing the panel and toolbar.
  Use ONLY `qdbus6 org.kde.KWin /KWin reconfigure` for live reloads.
  Recovery: `terminal(background=True, command="plasmashell --replace")`

- **KDE .colors files require DECIMAL RGB (`r,g,b`), NOT hex (`#rrggbb`).** Writing hex
  produces a silently invalid colorscheme. Use `hex_to_rgb()` to convert all palette values.

- **`widgetStyle=kvantum-dark` is WRONG and silently falls back to Breeze.**
  The correct value is `widgetStyle=kvantum` (lowercase, no suffix). This maps to
  `/usr/lib/qt6/plugins/styles/libkvantum.so`.

- **`materialize_kvantum` must call `qdbus6 org.kde.KWin /KWin reconfigure` after writing.**
  Without this, the `widgetStyle` change is written to `kdeglobals` but KWin doesn't pick
  it up until next login.

- **KDE colorschemes may be inherited from LookAndFeelPackage, not explicit.**
  If `[General] ColorScheme=` is missing from `kdeglobals`, the active scheme is inherited
  from `[KDE] LookAndFeelPackage=`. Always read both keys during snapshot.

- **`plasma-apply-colorscheme` expects the NAME, not a file path.**
  The name is the value of `[General] ColorScheme=` in the `.colors` file.

- **Colorscheme-only apply looks subtle** if the user was already on a dark theme.
  The dramatic change comes from Kvantum. Always install and configure Kvantum alongside
  the colorscheme for visible results.

- **Plasma theme SVGs with wrong element IDs are silently ignored.**
  KDE will not error. The panel will just use its fallback.

- **`undo()` must use `--delete` to clear `widgetStyle`, not an empty string.**
  `kwriteconfig6 --key widgetStyle ""` sets the key to an empty string — invalid, causes
  KDE to display no style. Use `--delete` so KDE falls back to the L&F default.

- **Incomplete system updates can destroy plasmashell panels.**
  If `pacman -Syu` is interrupted, plasma-desktop files may be partially written.
  Fix: `sudo pacman -S plasma-desktop --overwrite '*'` then `kquitapp6 plasmashell && plasmashell --replace &`
  Prevention: never run system updates via non-TTY background terminal.

- **`yay -S --noconfirm` fails in non-TTY** (can't escalate sudo).
  Fix: build with yay (no sudo needed for build), install resulting `.pkg.tar.zst` with `sudo pacman -U`.

- **PRESETS missing `kvantum_theme` key silently fall back to `"kvantum-dark"`**
  which is almost certainly not installed. Every preset must include `"kvantum_theme"` explicitly.
  Check installed themes: `find /usr/share/Kvantum ~/.local/share/Kvantum -maxdepth 1 -type d`
