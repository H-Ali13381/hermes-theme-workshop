# Rofi — Hyprland-Specific Notes

> **Full rasi theme structure, color mapping, power menu script:** See [shared/rofi.md](../shared/rofi.md)

---

## Keybinding in hyprland.conf

```hyprlang
# App launcher
bind = $mainMod, D, exec, rofi -show drun -theme ~/.config/rofi/theme.rasi

# Power menu
bind = $mainMod, X, exec, bash ~/.config/rofi/power-menu.sh
```

---

## Power Menu — Hyprland Commands

The shared power-menu.sh uses generic lock/logout. For Hyprland, use these commands:

```bash
case "$chosen" in
    "  Lock")     hyprlock ;;
    "  Logout")   hyprctl dispatch exit ;;
    "  Reboot")   systemctl reboot ;;
    "  Shutdown") systemctl poweroff ;;
esac
```

- **Lock:** `hyprlock` (requires hyprlock installed)
- **Logout:** `hyprctl dispatch exit` (cleanly exits Hyprland session)
