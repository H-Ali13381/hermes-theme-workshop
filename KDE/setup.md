# KDE Plasma Ricing — Setup & Overview

## The 6-Layer Stack

A colorscheme alone produces subtle changes — only Qt window chrome shifts.
For dramatic, system-wide transformation, apply ALL layers in order:

| Layer | What It Controls | Apply Command |
|-------|-----------------|---------------|
| 1. Colorscheme | Qt window borders, titlebars, system menus | `plasma-apply-colorscheme <name>` |
| 2. Kvantum | Entire Qt widget renderer — buttons, scrollbars, dropdowns | `kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum` |
| 3. Cursor | Cursor theme across all apps | `plasma-apply-cursortheme "<Theme Name>"` |
| 4. Splash screen | Boot splash | `kwriteconfig6 --file ksplashrc --group KSplash --key Theme <id>` |
| 5. Plasma theme | Panel/taskbar SVG backgrounds | `plasma-apply-desktoptheme <theme-name>` |
| 6. Window decorations | Title bar shape, buttons, borders on every window | `kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze` |

Window decorations are a distinct KWin layer — independent of colorscheme and Kvantum. Common choices:
- **Breeze** — default, minimal, adapts to colorscheme
- **Flat Aurora** — borderless, no title bar buttons visible until hover (clean for riced setups)
- **Klassy** — highly configurable borders, rounded corners, glow effects
- **No decorations** — for tiling setups; set via `kwriteconfig6 --file kwinrc --group Windows --key BorderlessMaximizedWindows true`

Apply without restart:
```bash
qdbus6 org.kde.KWin /KWin reconfigure
```

### Live Reload

```bash
qdbus6 org.kde.KWin /KWin reconfigure
```

**NEVER** call `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.refreshCurrentShell` on Wayland — it kills plasmashell without restarting. Recovery: `plasmashell --replace &`

Already-open Qt apps need to be closed and reopened to pick up Kvantum changes.

---

## KDE Config File Map

Where KDE stores its state — useful for manual inspection or targeted writes:

| Path | Contents |
|------|----------|
| `~/.config/kdeglobals` | Color scheme, fonts, widget style |
| `~/.config/kwinrc` | Window manager settings, tiling, decoration plugin |
| `~/.config/ksplashrc` | Plasma login splash theme |
| `~/.config/kscreenlockerrc` | Lock screen config |
| `~/.config/kcminputrc` | Cursor theme, input settings |
| `~/.config/Kvantum/kvantum.kvconfig` | Active Kvantum theme |
| `~/.config/plasma-org.kde.plasma.desktop-appletsrc` | Panel layout, widget positions, wallpaper |
| `~/.local/share/plasma/desktoptheme/` | User-installed Plasma (panel) themes |
| `~/.local/share/plasma/look-and-feel/` | Global theme bundles |
| `~/.local/share/color-schemes/` | `.colors` files |
| `~/.local/share/icons/` | User icon packs and cursor themes |
| `~/.local/share/aurorae/themes/` | SVG-based window decoration themes |
| `/usr/share/plasma/` | System-wide Plasma themes |
| `/usr/share/icons/` | System-wide icons |

### Global Themes
A **Global Theme** (`~/.local/share/plasma/look-and-feel/`) bundles Plasma Style + Color Scheme + Window Decoration + Icons + Cursors + Splash Screen in one package. Applying one with `plasma-apply-lookandfeel` sets all layers at once, which is why individual layer commands (like `plasma-apply-colorscheme`) are needed when the ricer controls each layer independently.

### KWin Desktop Effects (Blur & Animations)
Enable/configure via System Settings → Workspace → Desktop Effects, or scripted via `kwriteconfig6`:

Key effects for ricing:
- **Blur** — blurs content behind translucent panels/windows. Requires the panel or window to have some transparency set (via Kvantum, Plasma Style, or KWin Rules). Configure Blur Strength (10–15 subtle, 20+ heavy) and optional Noise Strength (grain texture).
- **Background Contrast** — darkens areas behind translucent elements for legibility.
- **Wobbly Windows** — jelly window movement.
- **Magic Lamp** — macOS-style minimize animation.
- **Fall Apart** — windows explode into particles on close.

```bash
# Toggle compositor (X11 only):
qdbus org.kde.KWin /Compositor toggleCompositing
```

**KWin Rules for per-window opacity** (System Settings → Window Management → Window Rules):
Match by window class → apply `Opacity Active = 80`. Also accessible via right-click title bar → More Options → Special Window Settings.

---

## discover_apps() — KDE Sub-system Registration

`kvantum`, `plasma_theme`, and `cursor` have no standalone binary — they are KDE sub-systems. Without explicit registration, the `APP_MATERIALIZERS` loop silently skips them.

Always ensure this block exists in `discover_apps()`:

```python
if "kde" in apps:
    apps["kvantum"] = {"installed": True}
    apps["plasma_theme"] = {"installed": True}
    apps["cursor"] = {"installed": True}
```

Any future materializer for a KDE sub-system (icon theme, splash, SDDM) MUST be registered the same way — binary detection will not find it.

---

## snapshot_kde_state() — What Gets Captured

The hardened snapshot captures:

| Key | Source |
|-----|--------|
| `active_colorscheme` | `[General] ColorScheme=` in kdeglobals; falls back to `[KDE] LookAndFeelPackage=` |
| `look_and_feel` | `[KDE] LookAndFeelPackage=` |
| `kvantum_theme` | `~/.config/Kvantum/kvantum.kvconfig` |
| `widget_style` | `[KDE] widgetStyle=` in kdeglobals |
| `plasma_theme` | `[General] lookAndFeelPackage=` in plasmarc |
| `cursor_theme` | `[Mouse] cursorTheme=` in kcminputrc |
| `wallpaper` | `Image=` from `~/.config/plasma-org.kde.plasma.desktop-appletsrc` |

---

## Package Requirements (Arch)

```bash
# Core KDE theming tools (usually pre-installed)
sudo pacman -S plasma-desktop kconfig

# Kvantum (biggest visual impact)
sudo pacman -S kvantum qt6ct

# Catppuccin Kvantum themes (AUR)
yay -S kvantum-theme-catppuccin-git

# Catppuccin cursors (AUR)
yay -S catppuccin-cursors-macchiato

# Screenshot tool
sudo pacman -S spectacle
```

### AUR Pitfall

`yay -S --noconfirm` fails in non-TTY (can't escalate sudo). Fix: build with yay (no sudo needed for build), install resulting `.pkg.tar.zst` with `sudo pacman -U`.

---

## Service Cache & Icon Refresh

**`kbuildsycoca6`** rebuilds the KService database — the index of `.desktop` files, MIME types, and plugins. Use it when a newly installed app is missing from the launcher, or a MIME association stopped working:

```bash
kbuildsycoca6   # Plasma 6 — incremental rebuild (sufficient for most cases)
```

This is NOT the icon cache. Changing an icon theme via `kwriteconfig6` + `qdbus6 reconfigure` is sufficient in Plasma 6 — the per-process icon cache (`icon-cache.kcache`) was removed from KF6 apps. If icons from a theme are still stale after `qdbus6 reconfigure`, log out and back in.

---

## Key Pitfalls

- **KDE .colors files require DECIMAL RGB** (`r,g,b`), NOT hex (`#rrggbb`). Writing hex produces a silently invalid colorscheme.
- **`widgetStyle=kvantum-dark` is WRONG** — silently falls back to Breeze. Correct: `widgetStyle=kvantum`.
- **`undo()` must use `--delete`** to clear `widgetStyle`, not an empty string.
- **Incomplete `pacman -Syu` can destroy plasmashell panels.** Fix: `sudo pacman -S plasma-desktop --overwrite '*'` then `kquitapp6 plasmashell && plasmashell --replace &`
- **Dunst conflicts with KDE's notification server.** Don't start dunst when Plasma is active — plasmashell owns `org.freedesktop.Notifications`. Theme the KDE notification system via the colorscheme instead.
- **Waybar is redundant on KDE.** KDE has its own panel via plasmashell. However, if the user runs waybar anyway (common for riced setups), remove all `hyprland/*` modules from config.jsonc — they silently fail on KDE Plasma.
- **KDE Wayland screen geometry: `xrandr` lies.** Under Plasma Wayland, `xrandr` reports the Xwayland scaled framebuffer, not KDE's actual monitor modes/logical geometry. Use `kscreen-doctor -o` as source of truth. Example: a 2560x1440@144Hz monitor at scale 1 can appear as 3200x1800 in `xrandr`; a 1920x1080 monitor at scale 1.25 may have logical geometry 1536x864. For wallpaper/mockups: use native mode for assets, KDE logical geometry for UI density/layout.
- **org.kde.video wallpaper is fake.** It appears in the wallpaper type enum but has no installed package. It can be "set" via qdbus6 without error, but plasmashell logs "no valid package loaded" and the desktop stays black. Use `plasma6-wallpapers-smart-video-wallpaper-reborn` (AUR) — plugin ID `luisbocanegra.smart.video.wallpaper.reborn`.
- **Plasmashell restart resets wallpaper.** After `kquitapp6 plasmashell && plasmashell --replace`, re-apply wallpaper via qdbus6.
- **Dunst v2 deprecated keys.** `geometry` and `shrink` are dunst v1 — v2 ignores them with a WARNING. Replace with `width`, `offset`, `origin`. See SKILL.md §12.
- **Rofi x-offset/y-offset.** Not valid rofi properties. Use `location` and `anchor` instead.
