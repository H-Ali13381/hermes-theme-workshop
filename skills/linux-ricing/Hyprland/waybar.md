# Waybar — Hyprland-Specific Notes

> **Full config, CSS theming, GTK pitfalls:** See [shared/waybar.md](../shared/waybar.md)

---

## Autostart in hyprland.conf

```hyprlang
exec-once = waybar
```

---

## Hyprland-Specific Modules

Add these to `modules-left` / `modules-center` in `config.jsonc`:

```jsonc
"modules-left": ["custom/logo", "hyprland/workspaces"],
"modules-center": ["hyprland/window"],
```

### Workspaces module

```jsonc
"hyprland/workspaces": {
    "format": "{id}",
    "on-click": "activate",
    "sort-by-number": true
}
```

### Window title module

```jsonc
"hyprland/window": {
    "format": "{}",
    "max-length": 50
}
```

---

## Reload via hyprctl

SIGUSR2 works for CSS changes (except `@define-color` — see shared doc). For a full restart from a Hyprland keybind or script:

```bash
pkill waybar; waybar &
```

Or dispatch from hyprctl:

```bash
hyprctl dispatch exec "pkill waybar; waybar"
```
