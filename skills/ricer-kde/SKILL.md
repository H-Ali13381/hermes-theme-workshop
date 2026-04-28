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

`kvantum`, `plasma_theme`, `cursor`, and `kde_lockscreen` have no standalone binary — they are KDE sub-systems.
Without explicit registration, the `APP_MATERIALIZERS` loop silently skips them.

Always ensure this block exists in `discover_apps()`:

```python
if "kde" in apps:
    apps["kvantum"] = {"installed": True}
    apps["plasma_theme"] = {"installed": True}
    apps["cursor"] = {"installed": True}
    apps["kde_lockscreen"] = {"installed": True}
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

## TODO (Needs Deeper Investigation)

- **KDE notification styling** — KDE's built-in notification daemon (part of plasmashell) cannot be themed via INI/CSS the same way dunst/mako can. The notification frame, colors, and font are controlled by the active Plasma theme's `dialogs/background.svg` and the KDE colorscheme. On a flat/stock Plasma theme, notifications will look stock even with a custom colorscheme applied. Options to investigate: (1) write a custom Plasma theme with navy `dialogs/background.svg`; (2) replace with a Wayland-compatible notification daemon that supports CSS (e.g. swaync); (3) use KDE's own notification applet settings under System Settings > Notifications. The current ricer does not touch notification styling on KDE at all.

- **SDDM greeter theme** — The login/SDDM screen's visual appearance (user input box style, clock, background artwork) is controlled by a QML SDDM theme package, not by wallpaper or colorscheme alone. Setting the SDDM background image changes only the wallpaper — the panel chrome (clock, password widget, buttons) stays as the active SDDM theme (default: `breeze`). To fully theme SDDM: install a custom SDDM theme package (e.g. `sddm-theme-sugar-candy` from AUR) and set `Current=<name>` in `/etc/sddm.conf`. This requires root, a QML-capable theme, and manual testing at logout. The ricer currently only sets the background image — needs a full SDDM theme materializer.

- **KDE lock screen clock/PIN styling** — Similar to SDDM: the clock, date, and password input widget on the KDE lock screen are rendered by a QML "greeter" component. Setting `Image=` in `kscreenlockerrc` only changes the background wallpaper. The widget chrome is controlled by the active Plasma theme and KDE colorscheme, but the QML layout (rounded corner box, blurred backdrop) requires a custom `kscreenlocker` theme or a Look-and-Feel package override. Default `breeze` greeter uses a flat layout. Needs a custom QML greeter or a Look-and-Feel package swap to change the PIN widget shape/style.

- **KDE panel / toolbar theming** — The panel background (taskbar, bottom bar) is NOT controlled by colorschemes or Kvantum. It is controlled by the Plasma theme SVGs in `~/.local/share/plasma/desktoptheme/<name>/widgets/panel-background.svg`. The ricer currently does not write a custom Plasma theme. As a result the panel stays stock (Breeze-dark or whatever L&F is active). A full Plasma theme materializer needs to be built — with Qt SVG renderer constraints in mind (no `<pattern>`, no `data:` URIs, no CSS filters).

- **Kvantum "dead button" / no visual change issue** — If Kvantum IS set (`widgetStyle=kvantum` in kdeglobals, theme=catppuccin-mocha-teal in kvantum.kvconfig) but visually nothing changes, the most common cause is KDE's compositor not having picked up the widgetStyle change. Symptoms: windows look like stock Breeze. Fixes to try in order: (1) `qdbus6 org.kde.KWin /KWin reconfigure`; (2) log out and log back in; (3) open Qt5/Qt6 Settings (`qt5ct`/`qt6ct`) and verify `Style=kvantum`. Note: `kvantummanager --test` hangs in non-interactive terminal sessions — do NOT run it in background or scripted contexts.

## Window Decorations (Titlebar Buttons)

Window decorations (close/minimize/maximize buttons, titlebar chrome) are controlled by
KWin's decoration plugin — completely separate from both Kvantum and colorschemes.

Default: `org.kde.breeze` — square-ish Breeze buttons.

### macOS-style circular colored buttons

The preview.html design spec uses red/yellow/green traffic-light circles (`#C04040` / `#D4820A` / `#3A8060`).
To implement this in KDE, do NOT use Kvantum — it has no control over titlebars.

**Recommended: Klassy (AUR)** — best-maintained KDE decoration with explicit macOS button mode.

    yay -S klassy

Then configure:

    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.klassy
    kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme klassy
    qdbus6 org.kde.KWin /KWin reconfigure

Fine-tune in System Settings > Appearance > Window Decorations > Klassy > Configure:
- Button shape: Circle
- Button colors: use custom (set close=red, minimize=yellow, maximize=green)
- Button placement: Left side (macOS layout)
- Title bar height: 34px to match preview spec

**Alternative: Aurorae SVG themes** — requires a manually installed SVG theme directory.
Never set `library=org.kde.kwin.aurorae.v2` unless a real Aurorae theme dir exists at
`~/.local/share/aurorae/themes/<name>/` or `/usr/share/aurorae/themes/<name>/`.
Without it, KWin silently removes all titlebar buttons (critical breakage — see pitfalls).

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

- **`org.kde.kwin.aurorae.v2` with `__aurorae__svg__Breeze` as theme = missing titlebar buttons.**
  The `Breeze` SVG Aurorae theme is NOT installed by default in `/usr/share/aurorae/themes/` nor `~/.local/share/aurorae/themes/`. If kwinrc is set to `library=org.kde.kwin.aurorae.v2` and `theme=__aurorae__svg__Breeze`, KWin cannot find the theme SVGs and silently removes the titlebar buttons (close/minimize/maximize) and the ability to resize windows via titlebar. This is a critical breakage.
  Fix: revert to the standard Breeze decoration: `kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze`
  then `kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme org.kde.breeze`
  then `qdbus6 org.kde.KWin /KWin reconfigure`. The buttons will immediately reappear.
  The previous rice session accidentally set `library=org.kde.kwin.aurorae.v2` — this must not happen unless an actual Aurorae SVG theme directory is installed.

- **qdbus6 `setWallpaper` with QVariantMap string fails for video wallpaper plugin.**
  Calling `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.setWallpaper "<plugin>" "<json-string>" <screen>` with a JSON string for the parameters fails with "Sorry, can't pass arg of type 'QVariantMap'." The correct call is done via a Python script using `subprocess` + `dbus-python` or via `plasma-apply-wallpaperimage` for static images. For the smart-video-wallpaper-reborn plugin, use a Python dbus call or write directly to `~/.config/plasma-org.kde.plasma.desktop-appletsrc` and restart plasmashell.

- **KDE animated wallpaper reverts to static on switch_wallpaper.sh fallback.**
  `switch_wallpaper.sh` checks `if [ -f "$VIDEO" ]; then ... qdbus6 ... else plasma-apply-wallpaperimage $STATIC`. The qdbus6 QVariantMap call always fails (see above), so the script silently falls through to `plasma-apply-wallpaperimage` on the static PNG every time — even when the MP4 exists. The video wallpaper appears to have been applied during the last session via plasmashell restart timing, not via this script. The script needs to be rewritten using Python dbus or direct appletsrc manipulation.

- **CRITICAL: Fastfetch ANSI logo file must contain ESC byte (0x1b) before `[` sequences.**
  When writing a logo.txt with ANSI color codes, the file must contain the actual ESC character
  (`\x1b`) before each `[38;2;...m` sequence. If only the bare `[38;2;46;110;166m` string is
  written (no ESC), the terminal renders it as literal text: `[38;2;46;110;166m` appears on screen.
  Python's `write_file` tool and `echo` can both produce files missing the ESC byte if the
  escape sequences are not explicitly embedded as `\x1b[...m` or `\033[...m`.
  Fix: run `python3 -c "f=open('logo.txt','rb'); d=f.read(); print(b'\\x1b' in d)"` to verify.
  If False, insert ESC before every `[` that precedes a digit (see the patch script used in the
  the-long-con rice session, 2026-04-28).

- **`kvantummanager --test` hangs indefinitely in non-interactive terminal sessions.**
  Never run `kvantummanager` in a scripted or background context — it spawns a GUI and blocks.
  To verify Kvantum is active, use: `kreadconfig6 --file kdeglobals --group KDE --key widgetStyle`
  and `cat ~/.config/Kvantum/kvantum.kvconfig`.

- **Kvantum does NOT control titlebar buttons or window chrome shape.**
  Kvantum styles Qt widgets (buttons, scrollbars, dropdowns, checkboxes, menus) ONLY.
  If the design spec calls for macOS-style colored circle buttons, that requires a window
  decoration plugin (Klassy, Aurorae) — not Kvantum. Confusing the two wastes a debugging
  session. If Kvantum is set correctly but the titlebar looks like stock Breeze circles,
  the decoration plugin is the gap, not Kvantum.

- **Window decoration design intent not implemented — preview vs reality mismatch.**
  Reverting KWin to `org.kde.breeze` after a broken Aurorae mis-set is a RECOVERY fix,
  not a completed implementation. The design spec (preview.html) may still call for
  macOS-style circular colored buttons (red/yellow/green traffic lights, left-side placement).
  After any revert to Breeze, a TODO must be created to install Klassy or a real Aurorae
  theme and match the preview spec. Do NOT mark window decoration as "done" after a Breeze
  revert — it is only stabilized, not themed.
  Verification: grep preview.html for `wc-close`/`wc-min`/`wc-max` button colors and confirm
  the live KWin decoration matches before closing the session.

- **KDE panel appearance not implemented — preview spec vs stock Breeze mismatch.**
  The ricer currently leaves the KDE panel (taskbar) as stock Breeze-dark. The preview.html
  spec typically defines a fully custom panel: deep navy blurred background, gold top border,
  styled launcher button, workspace dots, rounded active-task highlights, JetBrains Mono
  system tray, and Playfair Display italic clock. NONE of this is achieved by colorscheme,
  Kvantum, or wallpaper changes alone — the panel background requires a custom Plasma theme
  SVG (`widgets/panel-background.svg`) and the clock/tray require per-applet config.
  Do NOT consider the panel "themed" until its visual matches preview.html. Documenting it
  as a TODO is not the same as implementing it. A full panel materializer needs to be built:
    1. Write `~/.local/share/plasma/desktoptheme/<name>/widgets/panel-background.svg`
       with valid Qt SVG element IDs (center, top, bottom, left, right, topleft, etc.)
       using flat navy fill + gold top border (no <pattern>, no data: URIs — Qt ignores them).
    2. Apply with `plasma-apply-desktoptheme <name>`.
    3. Configure the digital clock applet to use Playfair Display italic via its config.
    4. Set task manager button style to show labels + rounded highlight via appletsrc.
  Verification: open preview.html, screenshot live desktop, compare side by side.


