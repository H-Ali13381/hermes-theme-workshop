# Troubleshooting Reference

Consolidated pitfalls from real ricing sessions. Organized by component.

---

## KDE Plasma

**NEVER call `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.refreshCurrentShell` on Wayland.**
It causes plasmashell to exit without restarting, killing the panel and toolbar entirely.
Use only `qdbus6 org.kde.KWin /KWin reconfigure` for live reloads.
Recovery: `plasmashell --replace &`

**KDE `.colors` files require decimal RGB (`r,g,b`), not hex (`#rrggbb`).**
Writing hex produces a silently invalid colorscheme. Always convert with `hex_to_rgb()`.

**`widgetStyle=kvantum-dark` is wrong and silently falls back to Breeze.**
The correct value is `widgetStyle=kvantum` (no suffix). This maps to `libkvantum.so`.

**`materialize_kvantum` must call `qdbus6 org.kde.KWin /KWin reconfigure` after writing.**
Without it, the `widgetStyle` change is written to `kdeglobals` but KWin doesn't pick it up until next login.

**KDE colorschemes may be inherited from `LookAndFeelPackage`, not set explicitly.**
If `[General] ColorScheme=` is missing from `kdeglobals`, the active scheme comes from
`[KDE] LookAndFeelPackage=`. Always read both keys during snapshot.

**`plasma-apply-colorscheme` expects the scheme NAME, not a file path.**
The name is the value of `[General] ColorScheme=` inside the `.colors` file.

**Colorscheme-only apply looks subtle** if the user was already on a dark theme.
The dramatic change comes from Kvantum. Always apply both together.

**`undo()` must use `--delete` to clear `widgetStyle`, not an empty string.**
`kwriteconfig6 --key widgetStyle ""` sets an empty string — invalid.
Use `--delete` so KDE falls back to the Look-and-Feel default.

**Plasma theme SVGs with wrong element IDs are silently ignored.**
Required element IDs for `panel-background.svg`: `center`, `top`, `bottom`, `left`, `right`,
`topleft`, `topright`, `bottomleft`, `bottomright`, `hint-tile-center`.
Qt's SVG renderer also silently ignores: `<pattern>`, `data:` URIs, `feTurbulence`,
`feDisplacementMap`, `feColorMatrix`, CSS `filter:`, and all other SVG filters.

**Aurorae decoration with missing theme dir removes all titlebar buttons (critical).**
Never set `library=org.kde.kwin.aurorae.v2` unless a real Aurorae theme directory exists at
`~/.local/share/aurorae/themes/<name>/`. Without it, KWin silently removes close/minimize/maximize
buttons and the ability to resize via titlebar.
Fix: `kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key library org.kde.breeze`
then `kwriteconfig6 --file kwinrc --group org.kde.kdecoration2 --key theme org.kde.breeze`
then `qdbus6 org.kde.KWin /KWin reconfigure`.

**Kvantum does NOT control titlebar buttons or window chrome shape.**
Kvantum styles Qt widgets (buttons, scrollbars, dropdowns) only. macOS-style circle buttons
require a window decoration plugin (Klassy or Aurorae), not Kvantum.

**`kvantummanager --test` hangs indefinitely in non-interactive terminal sessions.**
Never run it in a scripted or background context — it spawns a GUI and blocks.
To verify Kvantum is active: `kreadconfig6 --file kdeglobals --group KDE --key widgetStyle`
and `cat ~/.config/Kvantum/kvantum.kvconfig`.

**Presets missing `kvantum_theme` silently fall back to `"kvantum-dark"`, which is not installed.**
Every preset must include `kvantum_theme` explicitly.
Check installed themes: `find /usr/share/Kvantum ~/.local/share/Kvantum -maxdepth 1 -type d`

**Incomplete system updates can destroy plasmashell panels.**
If `pacman -Syu` is interrupted, plasma-desktop files may be partially written.
Fix: `sudo pacman -S plasma-desktop --overwrite '*'` then `kquitapp6 plasmashell && plasmashell --replace &`

**`qdbus6 setWallpaper` with `QVariantMap` string fails for video wallpaper plugin.**
The correct approach is direct `dbus-python` calls or writing directly to
`~/.config/plasma-org.kde.plasma.desktop-appletsrc` and restarting plasmashell.

**`yay -S --noconfirm` fails in non-TTY** (can't escalate sudo).
Fix: build with yay (no sudo for build), install resulting `.pkg.tar.zst` with `sudo pacman -U`.

---

## Hyprland

**`rofi-wayland` does not exist in Arch repos.** Use `rofi` (v2.0+ has native Wayland support).

**`swww` does not exist in Arch repos.** It was renamed to `awww`.

**`hyprpaper` v0.8.3 (Arch, April 2026) silently fails to apply wallpapers.**
Process starts, no errors, desktop stays black. `hyprctl hyprpaper listloaded` returns
`error: invalid hyprpaper request` / `protocol version too low`.
Fix: use `awww` instead.
```
exec-once = awww-daemon
exec-once = awww img /path/to/wallpaper.png
```

**Always define ALL monitors explicitly in `hyprland.conf`.**
Hyprland auto-places monitors alphabetically if only one is defined — left/right order will be wrong.
The x-offset in the position field (e.g. `1920x0`) determines physical arrangement.

**`windowrulev2` is deprecated in Hyprland 0.54.x.** Use `windowrule` instead.

**Workspace pinning requires a full restart to take effect for existing workspaces.**
Live `hyprctl keyword workspace` only affects newly created workspaces.

**waybar loses its bars after monitor reconfiguration.**
After applying monitor/workspace changes live with `hyprctl keyword`, waybar sometimes
renders blank or disappears. Fix: `pkill waybar; waybar &`.

**plasmashell squats on `org.freedesktop.Notifications` DBus name, silently blocking dunst.**
Dunst logs: `Cannot acquire 'org.freedesktop.Notifications': Name is acquired by 'Plasma' with PID XXXX`
Diagnosis: `dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.GetNameOwner string:org.freedesktop.Notifications`
Fix in autostart: `exec-once = pkill plasmashell; dunst`

**Killing plasmashell can toggle monitor DPMS off.**
If a monitor goes dark after killing plasmashell:
`hyprctl dispatch dpms on DP-1` (repeat for each monitor)
If monitor still not rendering: `hyprctl keyword monitor HDMI-A-1,1920x1080@60,1920x0,1` then dpms on.

**`rofi -show power-menu` requires `rofi-power-menu` plugin, which is NOT in Arch repos.**
Use a plain bash script with `rofi -dmenu` instead.

**GTK CSS does not support `@define-color` variables or `alpha()` inside `@keyframes` blocks.**
This applies to waybar CSS. Using them causes: `Expected closing bracket after keyframes block`
and waybar refuses to start. Use literal `rgba(r, g, b, a)` values inside keyframes.

**Hyprland crashes on launch (SIGSEGV) are almost always a dependency bug, not a config issue.**
Check: `coredumpctl list | grep -i hyprland` then `coredumpctl info <PID>`.
Common cause (2026): Aquamarine null dereference in `SDRMConnector::disconnect` — fixed in git
but not yet released. Build from source: `git clone https://github.com/hyprwm/Aquamarine`
then `cmake .. -DCMAKE_INSTALL_PREFIX=/usr && make -j$(nproc) && sudo make install`.
What does NOT help: disabling monitors in config, disabling autostart, switching SDDM vs uwsm.

**Deprecated config keys in Hyprland 0.54.x:**
- `dwindle:no_gaps_when_only` — removed entirely
- `windowrulev2` — use `windowrule`
Check the red box at login for exact deprecated options.


---

## GTK

**`kde-gtk-config` is NOT installed on most systems.** Write `settings.ini` files directly.
Do not rely on KDE System Settings > "Legacy Application Style".

**GTK apps require a full restart to pick up `settings.ini` changes.** There is no live-reload equivalent.

**`gtk-application-prefer-dark-theme=1` only works for apps that respect it.**
Well-behaved GTK4 apps honor it; older GTK3 apps may not.

**GTK 3 and GTK 4 use the same `settings.ini` format but different theme packages.**
A GTK3 theme will not apply to GTK4 apps. Use `gtk.css` for GTK4 overrides.

**`Adwaita-dark` is always available as a safe fallback GTK theme** — no install required.

**GTK theming does not control web page content, app icons, or font rendering.**
Firefox picks up GTK colors only for the headerbar and menu bar — not page content.

---

## Terminals

**Konsole requires a new session to activate theme changes.** Running instances are not affected.

**CRITICAL: `DefaultProfile` activation requires writing the key explicitly.**
The `.profile` file alone is not enough. Read the active profile first:
`kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile`
If no default exists, create one and set that exact profile name with
`kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile <profile>.profile`.

**Konsole color scheme format uses decimal RGB (`r,g,b`), not hex.** Same rule as KDE `.colors` files.

**kitty reload safety:** do not broadcast `SIGUSR1` to all Kitty processes from
automation. Defer to next launch unless the user explicitly asks for a targeted
reload and the exact PID/session is known.

**CRITICAL: Fastfetch ANSI logo files must contain the actual ESC byte (`\x1b`) before `[` sequences.**
If only the bare `[38;2;...m` string is written (no ESC), the terminal renders it as literal text.
Verify: `python3 -c "f=open('logo.txt','rb'); d=f.read(); print(b'\x1b' in d)"`
If False, re-generate with explicit `\x1b[...m` or `\033[...m` escapes.

---

## Waybar

**waybar has no live CSS reload.** Always `pkill waybar; waybar &` to apply changes.
Run from terminal to see parse errors — `exec-once` hides them.

**`@import` injection into `style.css` must deduplicate.** Check for an existing `# hermes-ricer`
marker before injecting to avoid stacking multiple import lines on repeated runs.

**8-digit hex colors (`#RRGGBBAA`) don't work in `@define-color`.** Use `rgba(r, g, b, a)`.

---

## Custom Widgets (Quickshell / EWW)

**Widget runs but renders nothing / wrong size / no input — `WAYLAND_DEBUG=1` first.**
Layer-shell clients fail silently when the protocol negotiation goes wrong (missing anchor,
zero size requested, surface configured before role). Run the widget as
`WAYLAND_DEBUG=1 quickshell -c ./shell.qml` (or `WAYLAND_DEBUG=1 eww open <name>`) and
read the dumped protocol log. The bug is almost always visible in the last 20 lines
before the first error or the moment rendering should have started.

**Doubled gap at a screen edge = two clients claiming exclusive zone.**
Both waybar and a Quickshell/EWW bar anchored to the same edge with non-zero exclusive
zone will each reserve space, producing a visible doubled strip. Either drop one of
them, or set `exclusionMode: ExclusionMode.Ignore` (Quickshell) / `:exclusive false`
(EWW) on the secondary window so it overlays without reserving space.

**Widget frozen on stale data = frame callback isn't firing.**
Both frameworks render only when their data source signals a change (Quickshell reactive
bindings, EWW `defpoll` / `deflisten`). A widget that looks dead is usually one whose
source isn't emitting. For Quickshell: confirm the `Process` / `Timer` / IPC service is
actually producing output (`hyprctl -j ...` works in the terminal but not in the QML?
check the spawned process's environment). For EWW: `eww state` lists current variable
values; missing or stale entries point at the broken `defpoll`/`deflisten`.

---

## Dunst / Notifications

**`dunst` include directives require dunst >= 1.7.0.**
On older versions the fragment file is written but not auto-loaded.

**Dunst silent failure (no notifications appearing) is almost always the DBus name conflict with plasmashell.**
See the Hyprland section above.

---

## Wallpaper

**`hermes chat -Q -q` with foreground mode will time out on image generation (10–30s).**
Always use `terminal(background=True, notify_on_complete=True)` for image_gen calls.

**`fal-ai/image-editing/style-transfer` is not suitable for UI work** — full-image repaint, no structure preservation, no reference image input.

**Use `queue.fal.run` for fal.ai submission, not `fal.run` directly.**
Always use `status_url` and `response_url` from the job response — do not construct them manually.

**Multi-monitor HiDPI setups produce oversized combined screenshots.**
`spectacle --fullscreen` captures all monitors at 2× DPR. Crop and resize explicitly rather
than hardcoding pixel counts — dimensions vary per setup.

**Vision tool may be broken if `gemini-2.5-turbo` is configured as auxiliary model.**
This model ID is invalid — all `vision_analyze` and `browser_vision` calls fail with 400.

---

## Rollback / Undo

**Pre-2026-04-22 manifests are incomplete** — missing `kvantum_theme`, `plasma_theme`, `cursor_theme`.
Run `desktop_state_audit.py` to capture a fresh baseline before undoing from old manifests.

**Wallpaper changed manually after a session snapshot will not be restored by undo.**
Undo restores the wallpaper path recorded at snapshot time.

**Post-flight audit uses nested JSON paths, not flat keys.**
Correct: `kde.colorscheme.active_scheme`, `kde.kvantum.kvantum_theme`.
Flat top-level key lookups will never match — post-flight comparison will always show SAME.

---

## Catalog Capture / Screenshots (Wayland)

**`spectacle --current` captures the focused monitor, not the reference window monitor.**
In batch automation the terminal usually has focus. Use `spectacle --fullscreen` + PIL crop instead.

**`spectacle --activewindow` misses panel, desktop, and wallpaper context.** Use fullscreen + crop.

**On Wayland, Qt's `raise_()`, `activateWindow()`, `move()`, and `setScreen()` are silently ignored by KWin.**
The compositor places new windows on whichever monitor has current focus.
The only reliable approach is KWin D-Bus scripting to move and activate after the window opens.
```javascript
var clients = workspace.windowList();
for (var i = 0; i < clients.length; i++) {
    if (clients[i].caption.indexOf("Your Window Title") !== -1) {
        clients[i].frameGeometry = {x: newX, y: newY, width: clients[i].width, height: clients[i].height};
        workspace.activeWindow = clients[i];
        break;
    }
}
```
Load via:
```bash
ID=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript /path/to/script.js name)
qdbus6 org.kde.KWin "/Scripting/Script${ID}" run
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript name
```

**Desktop shortcut icons need KDE trust metadata to render correctly.**
After writing a `.desktop` file to `~/Desktop/`:
1. `chmod +x file.desktop`
2. `setfattr -n user.xdg.origin.url -v "file:///path/to/file.desktop" file.desktop`
3. Restart plasmashell so the folder view picks up changes.

**Close stray GUI windows before capture.** Open image viewers, file managers, etc. appear in fullscreen screenshots and obscure the reference window.
