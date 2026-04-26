# Dunst — Hyprland-Specific Notes

> **Full INI config, color mapping, include pattern, reload commands:** See [shared/dunst.md](../shared/dunst.md)

---

## Autostart in hyprland.conf

```hyprlang
exec-once = dunst
```

If migrating from a KDE install where plasmashell may still launch:

```hyprlang
exec-once = pkill plasmashell; dunst
```

---

## KDE/Plasmashell DBus Conflict

This is the **#1 cause of "dunst doesn't work"** on a KDE+Hyprland system.

KDE's `plasmashell` registers itself as `org.freedesktop.Notifications` on DBus. If plasmashell starts before dunst (common when Hyprland is launched from SDDM on a KDE install), dunst cannot acquire the name. See shared/dunst.md for diagnosis steps.

### Fix for Hyprland

Ensure plasmashell is killed in your hyprland.conf autostart:

```hyprlang
exec-once = pkill plasmashell; dunst
```

### IMPORTANT

Do NOT run dunst alongside KDE's own notification daemon when in a Plasma session. Dunst is only for standalone Hyprland/Sway sessions, not KDE Plasma with Hyprland as the compositor.
