# Mako Theming

Mako is a Wayland notification daemon with a flat INI-style config at `~/.config/mako/config`. The ricer **fully rewrites** this file from template.

---

## How ricer.py Applies the Theme

1. Writes `~/.config/mako/config` from `templates/mako/config.template`
2. Reloads: `makoctl reload`

**Template variables used:**

| Variable | Role |
|----------|------|
| `{{name}}` | Theme name — written as a comment header |
| `{{background}}` | Notification background |
| `{{foreground}}` | Notification text |
| `{{primary}}` | Normal urgency border |
| `{{surface}}` | Low urgency background variation |
| `{{muted}}` | Low urgency text (dimmed) |
| `{{danger}}` | Critical urgency border + text |
| `{{corner_radius}}` | From design_system `border_radius`, default `6` (integer, no `px`) |

---

## Config Format

Mako uses section headers for urgency-based overrides:

```ini
background-color=#1a1a2e
text-color=#cdd6f4
border-color=#7b5ea7
border-size=2
border-radius=6
icons=1
max-icon-size=32
padding=8
margin=8
font=JetBrainsMono Nerd Font 10

[urgency=low]
border-color=#313244
text-color=#6c7086

[urgency=normal]
border-color=#7b5ea7

[urgency=high]
background-color=#313244
border-color=#f38ba8
text-color=#f38ba8
```

---

## Key Options

| Option | Effect |
|--------|--------|
| `border-radius` | Rounded corners (integer px, no unit) |
| `border-size` | Border thickness in px |
| `padding` | Inner padding in px |
| `margin` | Gap between notification and screen edge |
| `max-visible` | Max stacked notifications (default unlimited) |
| `sort` | Sort order: `+time` (oldest first) or `-time` (newest first) |
| `layer` | Wayland layer: `top` (above windows) or `overlay` |
| `anchor` | Position: `top-right`, `bottom-right`, `top-center`, etc. |

---

## Reload After Apply

```bash
makoctl reload
```

If makoctl is unavailable (daemon not running):
```bash
mako &
```

---

## Pitfalls

- **`border-radius` is an integer, not `6px`.** Using CSS-style `px` suffix causes a parse error and mako falls back to defaults silently.
- **Font must be installed.** If `JetBrainsMono Nerd Font` isn't present, mako falls back to the system default — no error shown. Verify with `fc-list | grep JetBrains`.
- **swaync conflict.** If both mako and swaync are running, both intercept notifications. Pick one — disable the other from autostart.
- **Hyprland layer.** On Hyprland, `layer=overlay` is needed for notifications to appear above fullscreen windows.
