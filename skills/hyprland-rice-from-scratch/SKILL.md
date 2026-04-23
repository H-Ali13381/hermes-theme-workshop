---
name: hyprland-rice-from-scratch
description: "Set up a full Hyprland tiling WM rice on Arch Linux from a stock KDE install. Covers package installation, complete config generation for Hyprland + waybar + rofi + dunst + kitty + hyprlock + hypridle + hyprpaper + fastfetch, all themed to a cohesive palette. Use when the user wants to go from stock KDE to a full tiling WM setup."
---

# Hyprland Full Rice from Scratch

Use when setting up Hyprland as a new desktop session alongside KDE (or standalone) on Arch Linux. This covers everything from package installation through complete configuration.

## Package Installation

### Arch Linux package names (verified May 2025)

Core WM + session:
    hyprland xdg-desktop-portal-hyprland

Bar + launcher + notifications:
    waybar rofi dunst

IMPORTANT package name gotchas:
- `rofi-wayland` does NOT exist in Arch repos. Use `rofi` (v2.0+ includes native Wayland support).
- `swww` does NOT exist in Arch repos. It was renamed to `awww` ("An Answer to your Wayland Wallpaper Woes").

Terminal:
    kitty

Wallpaper + lock + idle:
    awww hyprpaper hyprlock hypridle

Icons + fonts:
    papirus-icon-theme ttf-jetbrains-mono-nerd otf-firamono-nerd

Utilities:
    fastfetch wl-clipboard grim slurp brightnessctl playerctl

Wayland compatibility:
    polkit-kde-agent qt5-wayland qt6-wayland

GTK settings:
    nwg-look

### No conflicts with KDE

All packages coexist with KDE Plasma. Hyprland appears as a separate session at SDDM login. KDE stays fully functional as a fallback. None of these packages autostart under KDE — they only run when launched.

### Install command

    sudo pacman -S --noconfirm hyprland xdg-desktop-portal-hyprland waybar rofi dunst kitty awww hyprlock hypridle hyprpaper papirus-icon-theme ttf-jetbrains-mono-nerd otf-firamono-nerd fastfetch wl-clipboard grim slurp brightnessctl playerctl polkit-kde-agent qt5-wayland qt6-wayland nwg-look

## Config File Structure

All configs go in ~/.config/:

    ~/.config/hypr/hyprland.conf      — main WM config (monitors, keybinds, rules, animations)
    ~/.config/hypr/hyprpaper.conf     — wallpaper per monitor
    ~/.config/hypr/hyprlock.conf      — lockscreen layout and colors
    ~/.config/hypr/hypridle.conf      — idle timeouts (dim, lock, dpms)
    ~/.config/waybar/config.jsonc     — bar modules and layout
    ~/.config/waybar/style.css        — bar CSS styling
    ~/.config/rofi/void-dragon.rasi   — launcher theme (or whatever name)
    ~/.config/dunst/dunstrc           — notification styling
    ~/.config/kitty/kitty.conf        — terminal colors, font, opacity
    ~/.config/fastfetch/config.jsonc  — system info display

Create all dirs first:

    mkdir -p ~/.config/{hypr,waybar,rofi,dunst,kitty,fastfetch}
    mkdir -p ~/Pictures/Screenshots

## Hyprland Config Essentials

### Multi-monitor

    monitor = DP-1, 1920x1080@120, 0x0, 1
    monitor = HDMI-A-1, 1920x1080@60, 1920x0, 1

Use `hyprctl monitors` to discover names and supported modes.

PITFALL — monitor order: Hyprland auto-places monitors alphabetically if only one is
explicitly defined. Always define ALL monitors in config with explicit positions, otherwise
left/right order will be wrong. The x-offset in the position field (e.g. `1920x0`) determines
physical left/right arrangement.

PITFALL — workspace pinning: by default Hyprland assigns workspaces to monitors based on
which monitor is "first". To control which workspace appears on which monitor, pin them:

    workspace = 1, monitor:DP-1, default:true
    workspace = 2, monitor:DP-1
    workspace = 3, monitor:DP-1
    workspace = 4, monitor:DP-1
    workspace = 5, monitor:DP-1
    workspace = 6, monitor:HDMI-A-1, default:true
    workspace = 7, monitor:HDMI-A-1
    workspace = 8, monitor:HDMI-A-1
    workspace = 9, monitor:HDMI-A-1
    workspace = 10, monitor:HDMI-A-1

Apply live without restart: `hyprctl keyword workspace "1, monitor:DP-1"` etc.

PITFALL — waybar after monitor reconfiguration: after applying monitor/workspace changes
live with `hyprctl keyword`, waybar sometimes loses its bars (renders blank or disappears).
Fix: `pkill waybar; waybar &`. A full Hyprland restart is not needed.

### Autostart

exec-once = waybar
exec-once = pkill plasmashell; dunst
exec-once = awww-daemon
exec-once = awww img /path/to/wallpaper.png
    exec-once = hypridle
    exec-once = /usr/lib/polkit-kde-authentication-agent-1
    exec-once = wl-paste --type text --watch cliphist store
    exec-once = wl-paste --type image --watch cliphist store

### Themed borders (gradient example)

    col.active_border = rgba(7ad4f0ee) rgba(d4a012ee) 45deg
    col.inactive_border = rgba(0c1220aa)

### Key animation beziers for game-UI feel

    bezier = voidSnap, 0.05, 0.9, 0.1, 1.0     — sharp snap-in
    bezier = voidSlide, 0.16, 1, 0.3, 1          — smooth slide
    bezier = voidFade, 0.33, 1, 0.68, 1          — quick fade

### Essential keybindings

    Super+Enter = terminal (kitty)
    Super+D     = launcher (rofi -show drun -theme <theme>.rasi)
    Super+Q     = kill window
    Super+F     = fullscreen
    Super+V     = toggle floating
    Super+HJKL  = vim-style focus movement
    Super+1-0   = workspaces
    Print       = screenshot via grim+slurp

### Window rules for HUD aesthetic

NOTE: `windowrulev2` is deprecated in Hyprland 0.54.x. Use `windowrule` instead.

    windowrule = opacity 0.92 0.85, class:^(kitty)$    — slight transparency
    windowrule = float, class:^(rofi)$                  — launcher floats
    windowrule = float, class:^(pavucontrol)$           — volume control floats

## Waybar Config Notes

- Use `config.jsonc` (JSON with comments support)
- `hyprland/workspaces` module for workspace indicators
- `hyprland/window` module for active window title
- Custom modules via `custom/<name>` for logo, separators, power button
- Nerd Font icons in format strings: `"format": "  {usage}%"`

### CSS theming approach

- `window#waybar > box` for the bar container (use `background: alpha(@bg, 0.88)` for transparency)
- Zero border-radius for game-UI sharp edges
- `border-bottom: 2px solid` for HUD-style bottom glow
- `text-shadow: 0 0 8px alpha(@color, 0.6)` for glowing text
- `@keyframes` for pulsing urgent indicators

PITFALL — @keyframes and GTK CSS variables:
GTK CSS does NOT support `@define-color` variables or the `alpha()` function inside
`@keyframes` blocks. Using them causes: "Expected closing bracket after keyframes block"
and waybar refuses to start. Fix: use raw `rgba(r, g, b, a)` values inside keyframes.

Bad:
    @keyframes urgent-pulse {
        0% { text-shadow: 0 0 4px alpha(@magenta, 0.3); }
    }

Good:
    @keyframes urgent-pulse {
        0% { text-shadow: 0 0 4px rgba(204, 48, 144, 0.3); }
    }

## Rofi Launcher Notes

- Theme file is `.rasi` format
- Reference with: `rofi -show drun -theme ~/.config/rofi/<name>.rasi`
- `border-radius: 0px` for sharp game-menu edges
- `border: 0 0 0 3px` on selected element for left-edge highlight (like a game menu cursor)
- Placeholder text: `placeholder: "Execute command..."`

## Kitty Terminal Notes

- `background_opacity 0.88` for transparency (requires compositor)
- `hide_window_decorations yes` to remove title bar
- `tab_bar_style powerline` + `tab_powerline_style slanted` for styled tabs
- Full 16-color palette mapping for terminal colors
- Live reload: `kill -SIGUSR1 $(pgrep -x kitty)` — no restart needed

## Hyprlock Notes

- `blur_passes` and `brightness` on the background for frosted effect
- `shadow_passes` on labels for glow effect
- `rounding = 0` on input-field for sharp edges
- `fail_text` for custom ACCESS DENIED message

## Workspace-to-Monitor Pinning

Always explicitly assign workspaces to monitors. Without this, Hyprland assigns them
arbitrarily and the "wrong" monitor ends up as workspace 1.

Pattern: assign 1 as default on primary, 2 as default on secondary, then spread the rest:

    workspace = 1, monitor:DP-1, default:true
    workspace = 2, monitor:HDMI-A-1, default:true
    workspace = 3, monitor:DP-1
    workspace = 4, monitor:DP-1
    workspace = 5, monitor:DP-1
    workspace = 6, monitor:HDMI-A-1
    workspace = 7, monitor:HDMI-A-1
    workspace = 8, monitor:HDMI-A-1
    workspace = 9, monitor:HDMI-A-1
    workspace = 10, monitor:HDMI-A-1

PITFALL: `hyprctl keyword workspace` live-patching does NOT move already-spawned
workspaces. A full `hyprctl dispatch exit` + re-login is required for workspace
assignments to take effect properly.

PITFALL: After any monitor reassignment (live or via restart), waybar loses its
output binding and goes blank. Always `pkill waybar && waybar &` after touching
monitor or workspace config.

## KDE / Plasmashell Conflict

When launching Hyprland from SDDM on a system that also has KDE installed, plasmashell
may start in the background and squat on the `org.freedesktop.Notifications` DBus name.
This silently blocks dunst — notify-send succeeds but nothing appears.

Diagnosis:
    dbus-send --session --print-reply --dest=org.freedesktop.DBus \
      /org/freedesktop/DBus org.freedesktop.DBus.GetNameOwner \
      string:org.freedesktop.Notifications
    # Then check which PID owns that name — if it's not dunst, plasmashell is squatting.

Fix in autostart (hyprland.conf):
    exec-once = pkill plasmashell; dunst

Also: killing plasmashell mid-session can cause monitors to go dark (DPMS off).
Fix with: `hyprctl dispatch dpms on <monitor-name>`

## Monitor Layout

Always explicitly define BOTH monitors in hyprland.conf. Without it, Hyprland
auto-places the second monitor and ordering can be wrong:

    monitor = DP-1,    1920x1080@120, 0x0,    1   # left / primary
    monitor = HDMI-A-1, 1920x1080@60, 1920x0, 1   # right / secondary

Use `hyprctl monitors` to confirm actual names and positions.

## Activation

Log out of KDE. At SDDM login, select "Hyprland" session. Log in. KDE session remains available for fallback.

## Plasmashell Conflict (KDE + Hyprland dual session)

When Hyprland is launched via SDDM alongside an existing KDE install, `plasmashell`
may start in the background and claim the `org.freedesktop.Notifications` DBus name
before dunst gets a chance. Dunst then exits with:

    CRITICAL: Cannot acquire 'org.freedesktop.Notifications': Name is acquired by 'Plasma' with PID 'XXXX'

And all notify-send calls silently succeed (exit 0) but nothing appears on screen.

Fix: kill plasmashell before dunst starts. In hyprland.conf autostart:

    exec-once = pkill plasmashell; dunst

Also kill it manually if Hyprland is already running:

    kill $(pgrep plasmashell)

Side effect: killing plasmashell can toggle monitor DPMS off. If a monitor goes dark
after killing plasmashell, run:

    hyprctl dispatch dpms on DP-1
    hyprctl dispatch dpms on HDMI-A-1

The WM reported in fastfetch as "kwin" is also a symptom of this — means kwin is
still running under the hood alongside Hyprland.

## Wallpaper — use awww, not hyprpaper

`hyprpaper` v0.8.3 (current Arch repo version as of 2026-04) silently fails to apply
wallpapers — it starts, produces no errors, but the desktop stays black. Use `awww`
instead (package name: `awww`, binary: `awww-daemon` + `awww img`).

In hyprland.conf autostart:

    exec-once = awww-daemon
    exec-once = awww img /path/to/wallpaper.png

Do NOT use hyprpaper unless you install a newer version. Remove or skip hyprpaper.conf.

If you already have hyprpaper in exec-once, replace it with the above two lines.

## Debugging First Launch

If waybar doesn't appear: run `waybar` from kitty and read the error output. Common cause:
  CSS syntax error. Check for `@keyframes` blocks using `@define-color` variables or
  `alpha()` — GTK CSS rejects those inside keyframes. Replace with raw `rgba()` values.

### Dunst notifications silent (DBus name taken by Plasma)

If dunst starts but notifications never appear, plasmashell is squatting on
`org.freedesktop.Notifications`. Dunst logs: "Cannot acquire 'org.freedesktop.Notifications':
Name is acquired by 'Plasma' with PID XXXX"

This happens when SDDM launches a lingering plasma DBus session alongside Hyprland.

Fix — kill plasmashell first, then start dunst. In hyprland.conf autostart:

    exec-once = pkill plasmashell; dunst

Verify dunst owns the name after starting:

    dbus-send --session --print-reply --dest=org.freedesktop.DBus \
      /org/freedesktop/DBus org.freedesktop.DBus.GetNameOwner \
      string:org.freedesktop.Notifications

The returned PID should match dunst. If it matches plasmashell, kill it and restart dunst.

### Rofi power-menu mode does not exist

`rofi -show power-menu` requires the `rofi-power-menu` plugin — NOT in Arch repos.
Clicking a waybar power button wired to it gives: "Mode power menu is not found"

Use a plain bash script with rofi dmenu instead. Create ~/.config/rofi/power-menu.sh:

    #!/bin/bash
    options="  Lock\n  Logout\n  Reboot\n  Shutdown"
    chosen=$(echo -e "$options" | rofi -dmenu -p "POWER" -theme ~/.config/rofi/<theme>.rasi)
    case "$chosen" in
        "  Lock")     hyprlock ;;
        "  Logout")   hyprctl dispatch exit ;;
        "  Reboot")   systemctl reboot ;;
        "  Shutdown") systemctl poweroff ;;
    esac

chmod +x the script, then wire in waybar config.jsonc:

    "on-click": "bash ~/.config/rofi/power-menu.sh"

If no wallpaper: don't use hyprpaper v0.8.3 — it silently fails. Use awww instead:
  `awww-daemon &` then `awww img /path/to/wallpaper.png`

If dunst notifications don't appear: check if plasmashell is running (`pgrep plasmashell`).
  It squats on the org.freedesktop.Notifications DBus name and blocks dunst.
  Kill it: `kill $(pgrep plasmashell)` then restart dunst.
  dunst will log: "Cannot acquire 'org.freedesktop.Notifications': Name is acquired by 'Plasma'"
  Fix permanently in autostart: `exec-once = pkill plasmashell; dunst`

If a monitor goes dark after killing plasmashell: it may have killed the DPMS state.
  Restore with: `hyprctl dispatch dpms on HDMI-A-1` (or whichever monitor went dark)
  Then re-enable: `hyprctl keyword monitor HDMI-A-1,1920x1080@60,1920x0,1`

If apps look wrong (no Qt theme): set `env = QT_QPA_PLATFORMTHEME,qt6ct` in hyprland.conf
Monitor issues: `hyprctl monitors` to see what Hyprland detected

### Waybar CSS pitfalls (GTK CSS parser is strict)

Waybar uses GTK CSS, which has limitations vs. standard web CSS:

1. **`@define-color` variables DO NOT work inside `@keyframes` blocks.**
   This fails with `Expected closing bracket after keyframes block`:
   ```
   @keyframes pulse {
       0% { text-shadow: 0 0 4px alpha(@magenta, 0.3); }  /* BROKEN */
   }
   ```
   Fix: use literal `rgba()` values inside keyframes:
   ```
   @keyframes pulse {
       0% { text-shadow: 0 0 4px rgba(204, 48, 144, 0.3); }  /* OK */
   }
   ```
   Even with literal values, GTK sometimes still chokes on `@keyframes`. If it does, remove the animation and use a static `text-shadow` instead — the bar must render before effects matter.

2. **8-digit hex colors (`#RRGGBBAA`) don't work in `@define-color`.** Convert to `rgba(r, g, b, a)` format.

3. **Reload workflow:** `pkill waybar; waybar &` — waybar has no live CSS reload. Always re-run from terminal to see parse errors; running via `exec-once` hides them.

### Wallpaper: hyprpaper 0.8.3 on Arch is broken (2026-04)

Arch's packaged `hyprpaper` (0.8.3-4 as of April 2026) silently fails on wayland — process starts but never renders, and `hyprctl hyprpaper listloaded` returns `error: invalid hyprpaper request` / `protocol version too low`. Result: black screens on all monitors.

**Fix: use `awww` (swww fork) instead.** It's already in Arch repos as the package named `awww`.

Replace `exec-once = hyprpaper` with:
```
exec-once = awww-daemon
exec-once = awww img /path/to/wallpaper.png
```

For runtime use:
```
pkill hyprpaper
awww-daemon &
awww img /path/to/wallpaper.png
```

awww handles multi-monitor automatically — no per-monitor config needed. Supports transitions: `awww img <path> --transition-type wipe --transition-duration 2`.

Remove `hyprpaper.conf` or leave it unused — don't mix both daemons.

### Hyprland Crashes on Launch (SIGSEGV)

If Hyprland crashes immediately on login, do NOT waste time tweaking your config. The crash is almost certainly in a dependency library (aquamarine, hyprutils), not your hyprland.conf.

**Diagnosis steps:**

1. Check coredumps:
   ```
   coredumpctl list | grep -i hyprland
   coredumpctl info <PID>
   ```
2. Look at the stack trace — the crashing function tells you which library is broken. Common crash sites:
   - `Aquamarine::SDRMConnector::disconnect` → aquamarine bug
   - `Aquamarine::CLogger::log` → aquamarine bug (null dereference)
   - `xdg-desktop-portal-hyprland` → portal bug (usually secondary to Hyprland crash)
3. Check if the crash is a known unfixed bug:
   ```
   # Compare your installed version vs latest release
   pacman -Q aquamarine hyprland
   # Check upstream commits for fixes AFTER the latest release
   git clone https://github.com/hyprwm/Aquamarine.git /tmp/aquamarine-check
   cd /tmp/aquamarine-check && git log --oneline | grep -i "guard\|null\|crash\|fix\|disconnect"
   ```
4. If a fix exists in git but NOT in the released version → build from source.

**Building Aquamarine from git (when AUR is behind):**

The AUR `aquamarine-git` package is often outdated (was at 0.8.0 when 0.10.0 was stable). Build directly from upstream instead:

```
sudo pacman -S cmake ninja
git clone https://github.com/hyprwm/Aquamarine.git /tmp/aquamarine-build
cd /tmp/aquamarine-build && mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
```

After installing, reboot or restart Hyprland to pick up the new library.

**IMPORTANT: What does NOT help with library-level crashes:**
- Disabling monitors in config (the crash is in DRM backend, not config parsing)
- Disabling autostart apps (the crash happens before any app launches)
- Switching SDDM vs uwsm (same compositor, same crash)
- Downgrading hyprland (the bug is in the dependency, not hyprland itself)

**Testing bottleneck:** The user must log out of their current desktop (or use Ctrl+Alt+F3) to test Hyprland. This makes iteration slow. **Always batch related config changes before asking for a test cycle.**

**There is no shortcut.** Hyprland cannot run in a VM (needs real GPU DRM access). No way to validate config beyond syntax without actually launching. Plan changes in batches.

**Common crash causes (2026):**
- Aquamarine v0.10.0 null dereference in `SDRMConnector::disconnect` (fixed in git on 2026-04-11, commit 24f1db3, but not released).
- Use `coredumpctl info` + stack trace to identify which library is crashing.
- Building from git is often necessary when AUR git packages lag.

**Deprecated config migration (Hyprland 0.54.x):**
- `dwindle:no_gaps_when_only` → removed entirely
- `windowrulev2` → now just `windowrule` (v2 syntax is deprecated)
- `force_default_wallpaper`, `disable_splash_rendering`, some blur options often trigger warnings
- Always check red box at login for exact deprecated options.

## User Expectations

Users who ask for "full UI replacement" or compare to "video game menus" want:
- Zero border radius (sharp, angular, not bubbly)
- Glowing accents (text-shadow, colored borders)
- Transparency/blur (not opaque flat surfaces)
- Custom everything — bar, launcher, notifications, lockscreen, terminal all themed
- Animated transitions that feel snappy, not floaty
- HUD-style information display, not traditional desktop metaphor

Do NOT hold back on drastic changes when the user asks for a full rice. They want unrecognizable.
