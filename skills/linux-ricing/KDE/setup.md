# KDE Plasma Ricing — Setup & Overview

## The 5-Layer Stack

A colorscheme alone produces subtle changes — only Qt window chrome shifts.
For dramatic, system-wide transformation, apply ALL layers in order:

| Layer | What It Controls | Apply Command |
|-------|-----------------|---------------|
| 1. Colorscheme | Qt window borders, titlebars, system menus | `plasma-apply-colorscheme <name>` |
| 2. Kvantum | Entire Qt widget renderer — buttons, scrollbars, dropdowns | `kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle kvantum` |
| 3. Cursor | Cursor theme across all apps | `plasma-apply-cursortheme "<Theme Name>"` |
| 4. Splash screen | Boot splash | `kwriteconfig6 --file ksplashrc --group KSplash --key Theme <id>` |
| 5. Plasma theme | Panel/taskbar SVG backgrounds | `plasma-apply-desktoptheme <theme-name>` |

### Live Reload

```bash
qdbus6 org.kde.KWin /KWin reconfigure
```

**NEVER** call `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.refreshCurrentShell` on Wayland — it kills plasmashell without restarting. Recovery: `plasmashell --replace &`

Already-open Qt apps need to be closed and reopened to pick up Kvantum changes.

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

## Key Pitfalls

- **KDE .colors files require DECIMAL RGB** (`r,g,b`), NOT hex (`#rrggbb`). Writing hex produces a silently invalid colorscheme.
- **`widgetStyle=kvantum-dark` is WRONG** — silently falls back to Breeze. Correct: `widgetStyle=kvantum`.
- **`undo()` must use `--delete`** to clear `widgetStyle`, not an empty string.
- **Incomplete `pacman -Syu` can destroy plasmashell panels.** Fix: `sudo pacman -S plasma-desktop --overwrite '*'` then `kquitapp6 plasmashell && plasmashell --replace &`
- **Dunst conflicts with KDE's notification server.** Don't start dunst when Plasma is active.
- **Waybar is redundant on KDE.** KDE has its own panel via plasmashell.
