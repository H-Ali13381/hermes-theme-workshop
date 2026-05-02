# Hyprland Setup — Full Rice from Scratch

Complete guide to setting up Hyprland as a tiling WM on Arch Linux, alongside or replacing KDE.

---

## Package Installation

### Verified Arch Linux package names (April 2026)

**Core WM + session:**
```
hyprland xdg-desktop-portal-hyprland uwsm
```

**Bar + launcher + notifications:**
```
waybar rofi dunst
```

**CRITICAL package name gotchas:**
- `rofi-wayland` does **NOT** exist in Arch official repos — install from AUR (`yay -S rofi-wayland`). This is the lbonn fork with native Wayland support. Stock `rofi` (1.7.x) only works via XWayland and misrenders on HiDPI/multi-monitor under Hyprland.
- `hyprpaper` v0.8.3 silently fails (desktop stays black) — use `awww` instead (AUR: `awww`, a maintained swww fork at v0.12.0)

**Terminal:**
```
kitty
```

**Wallpaper + lock + idle:**
```
awww hyprlock hypridle
```

**Icons + fonts:**
```
papirus-icon-theme ttf-jetbrains-mono-nerd ttf-firacode-nerd
```

**Utilities:**
```
fastfetch wl-clipboard grim slurp brightnessctl playerctl
```

**Wayland compatibility + GTK settings:**
```
polkit-kde-agent qt5-wayland qt6-wayland nwg-look
```

### One-liner install

```bash
sudo pacman -S --noconfirm hyprland xdg-desktop-portal-hyprland uwsm \
  waybar rofi dunst kitty awww hyprlock hypridle \
  papirus-icon-theme ttf-jetbrains-mono-nerd ttf-firacode-nerd \
  fastfetch wl-clipboard grim slurp brightnessctl playerctl cliphist \
  polkit-kde-agent qt5-wayland qt6-wayland

# AUR packages (require yay/paru):
yay -S --noconfirm rofi-wayland nwg-look
```

All packages coexist with KDE Plasma. Hyprland appears as a separate session at SDDM login.

---

## Config File Structure

```
~/.config/hypr/hyprland.conf      — main WM config
~/.config/hypr/hyprlock.conf      — lockscreen
~/.config/hypr/hypridle.conf      — idle timeouts
~/.config/waybar/config.jsonc     — bar modules
~/.config/waybar/style.css        — bar CSS
~/.config/rofi/<theme>.rasi       — launcher theme
~/.config/rofi/power-menu.sh      — power menu script
~/.config/dunst/dunstrc           — notifications
~/.config/kitty/kitty.conf        — terminal
~/.config/fastfetch/config.jsonc  — system info (NOT .json — fastfetch v2.x uses .jsonc)
```

### Create all directories first

```bash
mkdir -p ~/.config/{hypr,waybar,rofi,dunst,kitty,fastfetch}
mkdir -p ~/Pictures/Screenshots
```

---

## Session Launch — uwsm

Use `uwsm` (Universal Wayland Session Manager) to start Hyprland from SDDM:

1. Install `uwsm` (included in the package list above)
2. At SDDM login, select **"Hyprland (uwsm-managed)"**

Direct binary execution (`Hyprland` from TTY) skips environment/session setup and produces warnings + broken env vars. Always use uwsm.

---

## KDE / Plasmashell Conflict Resolution

When Hyprland launches from SDDM on a KDE system, `plasmashell` may start in the background causing two problems:

### 1. Dunst notifications silently fail

plasmashell squats on `org.freedesktop.Notifications` DBus name before dunst can claim it. Dunst logs: *"Cannot acquire 'org.freedesktop.Notifications': Name is acquired by 'Plasma'"*. `notify-send` exits 0 but nothing appears.

**Diagnose:**
```bash
dbus-send --session --print-reply --dest=org.freedesktop.DBus \
  /org/freedesktop/DBus org.freedesktop.DBus.GetNameOwner \
  string:org.freedesktop.Notifications
# Compare returned PID against: pgrep dunst vs pgrep plasmashell
```

**Fix — kill plasmashell before dunst in autostart:**
```
exec-once = pkill plasmashell 2>/dev/null || true; dunst
```

### 2. Monitor goes dark when plasmashell is killed

Killing plasmashell can trigger DPMS-off on monitors. Recover:

```bash
hyprctl dispatch dpms on DP-1
hyprctl dispatch dpms on HDMI-A-1
```

If monitor is still dark (Hyprland thinks it's active but screen is black):
```bash
hyprctl keyword monitor HDMI-A-1,1920x1080@60,1920x0,1
hyprctl dispatch dpms on HDMI-A-1
```

If fastfetch shows WM as "kwin" — kwin/plasmashell is still running under Hyprland. Kill it.

---

## Multi-Monitor Setup

Always define **ALL** monitors explicitly. If only one is defined, Hyprland auto-places the second and left/right ordering will be wrong.

```hyprlang
monitor = DP-1,    1920x1080@120, 0x0,    1   # left / primary
monitor = HDMI-A-1, 1920x1080@60, 1920x0, 1   # right / secondary
```

Discover monitor names: `hyprctl monitors`

---

## Workspace Pinning

Without explicit pinning, Hyprland assigns workspaces arbitrarily. Pin them after `monitor=` lines:

```hyprlang
workspace = 1, monitor:DP-1,     default:true
workspace = 2, monitor:HDMI-A-1, default:true
workspace = 3, monitor:DP-1
workspace = 4, monitor:DP-1
workspace = 5, monitor:DP-1
workspace = 6, monitor:HDMI-A-1
workspace = 7, monitor:HDMI-A-1
workspace = 8, monitor:HDMI-A-1
workspace = 9, monitor:HDMI-A-1
workspace = 10, monitor:HDMI-A-1
```

**PITFALL:** `hyprctl keyword workspace` live-patching does NOT move already-spawned workspaces. A full `hyprctl dispatch exit` + re-login is required.

**PITFALL:** After any monitor reassignment, waybar loses its output binding and goes blank. Always `pkill waybar; waybar &` after touching monitor/workspace config.

---

## Autostart (Correct Order)

Order is critical — especially the plasmashell kill timing:

```hyprlang
exec-once = pkill plasmashell 2>/dev/null || true; dunst          # kill KDE BEFORE dunst starts
exec-once = awww-daemon
exec-once = awww img /path/to/wallpaper.png
exec-once = sleep 2 && hyprctl dispatch dpms on HDMI-A-1   # wake secondary monitor
exec-once = waybar
exec-once = hypridle
exec-once = /usr/lib/polkit-kde-authentication-agent-1
exec-once = wl-paste --type text --watch cliphist store
exec-once = wl-paste --type image --watch cliphist store
```

**Why this order:**
1. Kill plasmashell first to free DBus for dunst
2. Start awww-daemon before setting wallpaper
3. DPMS fix with delay to recover monitors after plasmashell kill
4. Waybar after monitors are stable
5. Polkit and clipboard last (non-visual)

---

## Full UI Restart Sequence

When waybar, wallpaper, or notifications disappear (config changes, monitor events):

```bash
pkill waybar; pkill awww-daemon; pkill dunst; sleep 1
awww-daemon &
waybar &
dunst -config ~/.config/dunst/dunstrc &
sleep 2
awww img /path/to/wallpaper.png
hyprctl keyword monitor "HDMI-A-1,1920x1080@60,1920x0,1"
hyprctl dispatch dpms on HDMI-A-1
```

Order matters: awww-daemon must start before `awww img`. DPMS commands at the end rescue secondary monitors that went dark during restart.

---

## Essential Keybindings

```hyprlang
$mainMod = SUPER

bind = $mainMod, Return, exec, kitty
bind = $mainMod, D, exec, rofi -show drun -theme ~/.config/rofi/theme.rasi
bind = $mainMod, Q, killactive
bind = $mainMod, F, fullscreen
bind = $mainMod, V, togglefloating
bind = $mainMod, H, movefocus, l
bind = $mainMod, J, movefocus, d
bind = $mainMod, K, movefocus, u
bind = $mainMod, L, movefocus, r
bind = $mainMod, 1, workspace, 1
bind = $mainMod, 2, workspace, 2
bind = $mainMod, 3, workspace, 3
bind = $mainMod, 4, workspace, 4
bind = $mainMod, 5, workspace, 5
bind = $mainMod, 6, workspace, 6
bind = $mainMod, 7, workspace, 7
bind = $mainMod, 8, workspace, 8
bind = $mainMod, 9, workspace, 9
bind = $mainMod, 0, workspace, 10
bind = $mainMod SHIFT, 1, movetoworkspace, 1
bind = $mainMod SHIFT, 2, movetoworkspace, 2
bind = $mainMod SHIFT, L, exec, hyprlock
bind = $mainMod, Print, exec, grim -g "$(slurp)" ~/Pictures/Screenshots/$(date +%Y%m%d_%H%M%S).png
```

---

## Debugging First Launch

| Symptom | Cause | Fix |
|---------|-------|-----|
| Waybar doesn't appear | CSS syntax error | Run `waybar` from kitty, read stderr |
| Black screen / no wallpaper | hyprpaper 0.8.3 broken | Switch to `awww-daemon` + `awww img` |
| Notifications don't appear | plasmashell on DBus | `pkill plasmashell`, restart dunst |
| Monitor goes dark | DPMS triggered | `hyprctl dispatch dpms on <monitor>` |
| Rofi theme fails silently | rasi parse error | `rofi -theme file.rasi -dump-theme 2>&1 \| head -5` |
| Qt apps look wrong | Missing env var | Add `env = QT_QPA_PLATFORMTHEME,qt6ct` to hyprland.conf |

---

## Hyprland Crashes on Launch (Aquamarine SIGSEGV)

If Hyprland crashes immediately on login, it's almost certainly a dependency library bug (aquamarine, hyprutils), not your config.

**Diagnose:**
```bash
coredumpctl list | grep -i hyprland
coredumpctl info <PID>
```

**Common crash sites:**
- `Aquamarine::SDRMConnector::disconnect` — aquamarine bug (fixed in git 2026-04-11, commit 24f1db3, unreleased as of April 2026)
- `Aquamarine::CLogger::log` — aquamarine null dereference

**Build Aquamarine from git:**
```bash
sudo pacman -S cmake ninja
git clone https://github.com/hyprwm/Aquamarine.git /tmp/aquamarine-build
cd /tmp/aquamarine-build && mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install
```

**What does NOT help with library-level crashes:**
- Disabling monitors in config
- Disabling autostart apps
- Switching SDDM vs uwsm

---

## Deprecated Config Migration (Hyprland 0.54.x)

- `windowrulev2` → now just `windowrule`
- `dwindle:no_gaps_when_only` → removed entirely
- `force_default_wallpaper`, `disable_splash_rendering` → removed

---

## Plugins — Going Beyond Config (Advanced)

A Hyprland plugin is a C++ shared library (`.so`) loaded into the compositor process at runtime. Plugins extend Hyprland *itself* — they can add dispatchers, config keywords, event hooks, window decorations, custom layouts, IPC fields, render-pipeline modifications, and overrides of built-in behavior.

**Default position for this skill: do not generate plugins.** Almost every rice can be expressed via `hyprland.conf` + a layer-shell client (Quickshell/EWW/waybar). Plugins are a last resort when those two tiers cannot reach the desired effect.

### When a plugin is the only path

| Need | Why config + widgets can't reach it |
|---|---|
| Custom window decorations (e.g. 9-slice image borders, tiled trim, badges) | Hyprland reserves and renders the border region itself; layer-shell clients can't draw inside it. |
| New tiling layouts (PaperWM-style horizontal scroll, manual tiling, spiral) | `general:layout` only accepts built-ins. |
| Augmenting IPC event payloads (e.g. attach window class to `closewindow`) | The IPC schema is fixed by Hyprland source. |
| Per-frame render hooks (custom shaders, post-processing, special compositing) | No config knob exposes the render pipeline. |
| New dispatchers / config keywords | The keyword and dispatcher tables are compiled-in. |

If the design need is in any of those rows, a plugin is the only path. If it isn't, write config and widgets instead.

### Loading

- **`hyprpm`** — official plugin manager. `hyprpm add <git-url>` → builds against the installed Hyprland version, `hyprpm enable <name>` activates it. Requires the Hyprland headers (`hyprland` source) installed.
- **Manual** — `plugin = /path/to/plugin.so` in `hyprland.conf`, or `hyprctl plugin load /path/to/plugin.so` at runtime.

### Constraints

- **ABI fragility.** Hyprland breaks plugin ABI frequently. Every Hyprland upgrade typically requires `hyprpm update` to rebuild every plugin. A plugin without an active maintainer becomes unloadable within months.
- **Crashes the compositor.** A null deref in plugin code kills the entire graphical session. There is no safe-mode reload.
- **C++ only.** No stable bindings for other languages. The internal types are Hyprland's own (`CWindow`, `CMonitor`, etc.) and the canonical reference is the Hyprland source itself; documentation is thin.
- **Build dependency on user's Hyprland version.** Pre-built `.so` files don't ship — every plugin is compiled on-host against the running Hyprland headers.

### Reference plugins

Useful as study material when generating a custom one:

| Plugin | Pattern demonstrated |
|---|---|
| `hyprbars` | Per-window decorations (title bars on tiled windows) |
| `hyprscroller` | Custom layout |
| `hyprtrails` | Per-frame rendering hook |
| `borders-plus-plus` | Multiple decoration layers |
| `hyprexpo` | Overlay / overview rendering (largely upstreamed) |

### If the skill is asked to generate a plugin

Treat it as a separate, opt-in deliverable, not part of the standard craft loop:

1. **Confirm the bucket-3 test above.** If config + a layer-shell client can express it, refuse and route to widgets instead.
2. **Generate a minimal plugin first.** A 1-callback plugin (event hook, no rendering) is the right starting point before attempting rendering or decoration plugins.
3. **Write a `Makefile` / `meson.build` against `pkg-config --cflags hyprland`.** Pin the targeted Hyprland version in a comment.
4. **Implement the destructor.** Forgetting a destructor declared in the header causes immediate SIGSEGV on load — the single most common first-plugin bug.
5. **Defer destroy/free to after the current frame.** Freeing a resource (texture, buffer, surface struct) inside a callback while the renderer is still reading from it segfaults the compositor. Queue destroys and run them at frame boundaries.
6. **Document the rebuild step.** Every plugin must come with a "run after Hyprland upgrade" instruction. `hyprpm update` if installed via hyprpm; otherwise rebuild manually.
7. **Mark the rice as plugin-dependent.** Surface this in the rice's README so the user knows their session can be killed by an ABI break.
