# Fastfetch — Hyprland-Specific Notes

> **For full fastfetch configuration, custom braille logos, palette integration, thematic separators, and module keys, see `shared/fastfetch.md`.**
>
> **For the image → braille conversion pipeline, see `shared/braille-art.md`.**

This stub covers only Hyprland-specific details.

---

## Hyprland Compositor Module

Fastfetch auto-detects Hyprland and shows it as the WM. The `"wm"` module displays `Hyprland` with version info when running under a Hyprland session.

---

## Autostart in hyprland.conf

Not typically needed (fastfetch runs on shell startup, not as a daemon), but if you want it in a specific terminal on login:

```ini
exec-once = kitty --hold fastfetch
```

---

## Hyprland-Specific Module Keys

When ricing for Hyprland, the `"wm"` module key can be themed to match:

```json
{"type": "wm", "key": "  WM"}
```
