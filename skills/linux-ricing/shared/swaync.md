# SwayNC Theming

SwayNC (Sway Notification Center) is a Wayland notification daemon with a GTK-CSS stylesheet at `~/.config/swaync/style.css` and a JSON config at `~/.config/swaync/config.json`. The ricer **fully rewrites** the stylesheet from template. The JSON config is not modified.

---

## How ricer.py Applies the Theme

1. Writes `~/.config/swaync/style.css` from `templates/swaync/style.css.template`
2. Reloads: `swaync-client --reload-css`

**Template variables used:**

| Variable | Role |
|----------|------|
| `{{name}}` | Theme name — CSS comment header |
| `{{background}}` | Notification and panel background |
| `{{foreground}}` | Text color |
| `{{primary}}` | Notification border, button highlight |
| `{{surface}}` | Hover state backgrounds |
| `{{accent}}` | Focused / active button state |
| `{{danger}}` | Critical notification border |
| `{{radius}}` | Border radius (e.g. `8px`) |

---

## CSS Selector Reference

SwayNC exposes a rich set of GTK CSS selectors:

| Selector | Element |
|----------|---------|
| `.notification-row` | Individual notification container |
| `.notification` | Notification card |
| `.notification.critical` | Critical-urgency notification |
| `.notification-content` | Inner content area |
| `.notification-default-action` | Main click target |
| `.close-button` | × dismiss button |
| `.control-center` | The slide-out panel |
| `.control-center-list` | Notification list inside panel |
| `.widget-title` | Panel section headers |
| `.widget-dnd` | Do Not Disturb toggle |
| `.widget-buttons-grid button` | Quick-action buttons |

---

## Example Minimal Theme

```css
.notification {
    border-radius: 8px;
    border: 2px solid #7b5ea7;
    background-color: #1a1a2e;
    color: #cdd6f4;
    padding: 12px;
    margin: 4px;
}

.notification.critical {
    border-color: #f38ba8;
}

.control-center {
    background-color: #1a1a2e;
    border: 1px solid #7b5ea7;
    border-radius: 8px;
}
```

---

## Reload After Apply

```bash
swaync-client --reload-css
```

Full restart if reload fails:
```bash
pkill swaync && swaync &
```

---

## JSON Config (Not Ricer-Managed)

`~/.config/swaync/config.json` controls behavior (position, timeout, max notifications). The ricer does not touch it. Useful defaults:

```json
{
  "positionX": "right",
  "positionY": "top",
  "timeout": 5,
  "timeout-low": 2,
  "timeout-critical": 0,
  "control-center-margin-top": 8,
  "control-center-margin-bottom": 8,
  "control-center-margin-right": 8,
  "notification-2fa-action": true,
  "widgets": ["title", "dnd", "notifications"]
}
```

---

## Pitfalls

- **mako conflict.** SwayNC and mako both register as notification daemons via D-Bus. Only one can run. Disable the other in autostart.
- **`--reload-css` is safe** — doesn't drop pending notifications. Full restart does.
- **GTK theme interaction.** SwayNC respects the active GTK theme for base widget styling. The CSS overrides most of it, but if colors look wrong, check your GTK theme isn't bleeding through. Add `* { all: unset; }` to the top of style.css as a nuclear option (may break icon rendering).
- **Hyprland autostart.** Add to `hyprland.conf`: `exec-once = swaync` (not `exec-always` — duplicate instances fight over D-Bus).
