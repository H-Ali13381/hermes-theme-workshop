# Waybar — Config, CSS & Theming

Status bar for Wayland compositors (Hyprland, Sway, River, etc.). Config in JSONC, styling in GTK CSS.

---

## File Locations

```
~/.config/waybar/config.jsonc    — module layout and settings
~/.config/waybar/style.css       — visual theme (GTK CSS)
```

---

## Config Structure (config.jsonc)

```jsonc
{
    "layer": "top",
    "position": "top",
    "height": 36,
    "spacing": 0,
    "modules-left": ["custom/logo"],
    "modules-center": [],
    "modules-right": [
        "custom/separator",
        "cpu",
        "memory",
        "custom/separator",
        "pulseaudio",
        "network",
        "custom/separator",
        "clock",
        "tray",
        "custom/power"
    ],

    "clock": {
        "format": "  {:%H:%M}",
        "format-alt": "  {:%A, %B %d}",
        "tooltip-format": "{:%Y-%m-%d | %H:%M:%S}"
    },

    "cpu": {
        "format": "  {usage}%",
        "interval": 5
    },

    "memory": {
        "format": "  {percentage}%",
        "interval": 5
    },

    "pulseaudio": {
        "format": "{icon} {volume}%",
        "format-muted": "  muted",
        "format-icons": { "default": ["", "", ""] },
        "on-click": "pavucontrol"
    },

    "network": {
        "format-wifi": "  {signalStrength}%",
        "format-ethernet": "  {ifname}",
        "format-disconnected": "  off"
    },

    "custom/logo": {
        "format": " ⟐ ",
        "tooltip": false
    },

    "custom/separator": {
        "format": " │ ",
        "tooltip": false
    },

    "custom/power": {
        "format": " ⏻ ",
        "on-click": "bash ~/.config/rofi/power-menu.sh",
        "tooltip": false
    }
}
```

> **Note:** Workspace and window-title modules are compositor-specific. See your compositor's waybar doc (e.g., Hyprland/waybar.md) for those modules.

---

## CSS Theming (style.css)

### Full rewrite vs @import injection

**Detection rule:** Check if style.css already has a custom theme:
```bash
grep -c "@define-color" ~/.config/waybar/style.css
```
If count > 3, the file IS the theme — do a **full rewrite**, not an @import injection.

**@import injection** (for vanilla/minimal style.css):
1. Write `~/.config/waybar/style-hermes.css` with full CSS palette
2. Prepend `@import "style-hermes.css";  /* linux-ricing */` to the top of style.css
3. Check for existing `/* linux-ricing */` marker to avoid duplicate injections

**Full rewrite** (for already-themed style.css):
Back up the existing file, write a complete replacement.

### Example themed CSS

```css
/* Theme: void-dragon */
@define-color bg rgba(12, 18, 32, 1);
@define-color fg rgba(228, 240, 255, 1);
@define-color primary rgba(122, 212, 240, 1);
@define-color accent rgba(212, 160, 18, 1);
@define-color surface rgba(28, 30, 42, 1);

* {
    font-family: "JetBrainsMono Nerd Font", monospace;
    font-size: 14px;
    border: none;
    border-radius: 0;
    min-height: 0;
}

window#waybar {
    background-color: @bg;
    color: @fg;
    border-bottom: 2px solid @primary;
}

#workspaces button {
    padding: 0 8px;
    color: @fg;
    background: transparent;
}

#workspaces button.active {
    background-color: @primary;
    color: @bg;
    border-bottom: 2px solid @accent;
}

#clock, #cpu, #memory, #pulseaudio, #network, #tray {
    padding: 0 10px;
    color: @fg;
}

#custom-logo {
    color: @primary;
    font-size: 16px;
    padding: 0 12px;
}

#custom-separator {
    color: @surface;
}

#custom-power {
    color: @accent;
    padding: 0 12px;
}

tooltip {
    background-color: @surface;
    border: 1px solid @primary;
    color: @fg;
}
```

---

## Live Reload

```bash
pkill -SIGUSR2 waybar
```

If SIGUSR2 doesn't pick up changes (common with @define-color changes), hard restart:
```bash
pkill waybar; waybar &
```

Run waybar from a terminal (not background) during development to see parse errors in stdout.

---

## 3 GTK CSS Pitfalls

### Pitfall 1 — @define-color inside @keyframes

GTK CSS rejects `@define-color` variables and `alpha()` inside `@keyframes` blocks with *"Expected closing bracket after keyframes block"*.

**Bad:**
```css
@keyframes pulse {
    0% { text-shadow: 0 0 4px alpha(@primary, 0.3); }
}
```

**Good:**
```css
@keyframes pulse {
    0% { text-shadow: 0 0 4px rgba(122, 212, 240, 0.3); }
}
```

### Pitfall 2 — 8-digit hex colors in @define-color

`#RRGGBBAA` format doesn't work in `@define-color`. Use `rgba(r, g, b, a)` instead.

**Bad:** `@define-color bg #0c1220ee;`
**Good:** `@define-color bg rgba(12, 18, 32, 0.93);`

### Pitfall 3 — No live CSS variable reload

Changing `@define-color` values requires a full waybar restart — SIGUSR2 alone won't update them. Always `pkill waybar; waybar &` when changing color variables.

### Pitfall 4 — Compositor-specific modules survive theme migrations

When migrating a waybar config from Hyprland to KDE (or vice versa), compositor-specific module IDs in `config.jsonc` will silently fail — waybar starts but those modules are missing or broken.

**Hyprland-only modules (remove/replace when on KDE):**
- `hyprland/workspaces` — Hyprland IPC only
- `hyprland/window` — Hyprland IPC only
- `hyprland/language` — Hyprland IPC only

**KDE Plasma has no waybar workspace module.** On KDE Wayland, remove workspace/window modules entirely from `modules-left`. Waybar runs fine alongside plasmashell; just don't use compositor-specific modules.

**Detection:** Check `modules-left/center/right` in config.jsonc for any `hyprland/` prefix when on a non-Hyprland system.

### Pitfall 5 — power-menu.sh logout command is compositor-specific

The standard `custom/power` rofi power menu often hardcodes `hyprctl dispatch exit` for logout.
On KDE this does nothing (hyprctl not available or wrong compositor).

**KDE-correct commands:**
```bash
Lock:     loginctl lock-session
Logout:   loginctl terminate-user "$USER"
Reboot:   systemctl reboot
Shutdown: systemctl poweroff
```

**Hyprland-correct commands:**
```bash
Lock:     hyprlock
Logout:   hyprctl dispatch exit
```
