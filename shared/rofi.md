# Rofi — Launcher Theme & Power Menu

Rofi is a Wayland/X11 application launcher. Themes use `.rasi` format. Works across compositors and DEs.

---

## File Locations

```
~/.config/rofi/<theme-name>.rasi    — theme file
~/.config/rofi/config.rasi          — global config (optional)
~/.config/rofi/power-menu.sh        — power menu script
```

---

## Rasi Theme Structure

Rasi uses its own variable syntax in `* {}` — NOT `@define-color` (that's GTK CSS).

```rasi
/* Generated theme — void-dragon */
* {
    background: #0c1220;
    foreground: #e4f0ff;
    primary:    #7ad4f0;
    accent:     #d4a012;
    surface:    #1c1e2a;
    muted:      #3d2214;
    danger:     #cc3090;

    background-color: transparent;
    text-color:       @foreground;
}

window {
    background-color: @background;
    border:           2px solid;
    border-color:     @primary;
    border-radius:    0px;       /* sharp edges for game-UI feel */
    width:            600px;
    padding:          20px;
}

mainbox {
    background-color: transparent;
    children:         [ inputbar, listview ];
}

inputbar {
    background-color: @surface;
    padding:          12px;
    border:           0 0 2px 0;
    border-color:     @primary;
}

entry {
    background-color: transparent;
    text-color:       @foreground;
    placeholder:      "Execute command...";
    placeholder-color: @muted;
}

listview {
    background-color: transparent;
    lines:            8;
    spacing:          4px;
    padding:          8px 0 0 0;
}

element {
    padding:          8px 12px;
    background-color: transparent;
    text-color:       @foreground;
}

element selected {
    background-color: @surface;
    text-color:       @primary;
    border:           0 0 0 3px;    /* left-edge highlight like game menu cursor */
    border-color:     @accent;
}

element-text {
    background-color: transparent;
    text-color:       inherit;
}

element-icon {
    background-color: transparent;
    size:             24px;
}
```

### Launch with theme

```bash
rofi -show drun -theme ~/.config/rofi/void-dragon.rasi
```

---

## Color Mapping from 10-Key Palette

| Rasi Variable | Palette Key | Usage |
|---------------|-------------|-------|
| `background`  | background  | Window fill |
| `foreground`  | foreground  | Default text |
| `primary`     | primary     | Borders, focused text |
| `accent`      | accent      | Selected element highlight |
| `surface`     | surface     | Input bar, selected bg |
| `muted`       | muted       | Placeholder text |
| `danger`      | danger      | Error/power actions |

---

## Rasi Pitfalls

### No CSS child combinators

Rasi does NOT support `window > box {}` or any child combinator syntax. The parser silently falls back to defaults with just a WARNING. Use flat selectors only: `window {}`, `mainbox {}`, `element {}`.

### Test for parse errors

```bash
rofi -theme ~/.config/rofi/theme.rasi -dump-theme 2>&1 | head -5
```

A parse failure still dumps the default theme — look for the WARNING line at top.

### Variable syntax

Rasi variables are defined in `* {}` block and referenced with `@name`. This is NOT `@define-color` (GTK CSS) or `$var` (SCSS). Mixing syntaxes causes silent fallback to defaults.

---

## Power Menu Script

The `rofi-power-menu` plugin doesn't exist in Arch repos. Use a dmenu-based bash script instead.

### ~/.config/rofi/power-menu.sh

```bash
#!/bin/bash
options="  Lock\n  Logout\n  Reboot\n  Shutdown"
chosen=$(echo -e "$options" | rofi -dmenu -p "POWER" -theme ~/.config/rofi/theme.rasi)
case "$chosen" in
    "  Lock")     loginctl lock-session ;;
    "  Logout")   echo "Logout command depends on compositor" ;;
    "  Reboot")   systemctl reboot ;;
    "  Shutdown") systemctl poweroff ;;
esac
```

> **Note:** Lock and Logout commands are compositor-specific. See your compositor's rofi doc (e.g., Hyprland/rofi.md) for the correct commands.

```bash
chmod +x ~/.config/rofi/power-menu.sh
```

### Wire to waybar

In `~/.config/waybar/config.jsonc`:

```jsonc
"custom/power": {
    "format": " ⏻ ",
    "on-click": "bash ~/.config/rofi/power-menu.sh",
    "tooltip": false
}
```
