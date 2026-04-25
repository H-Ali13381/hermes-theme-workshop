# Hyprlock — Lock Screen

Hyprlock is the lockscreen for Hyprland. Config is a full rewrite each time — no include/import system.

---

## File Location

```
~/.config/hypr/hyprlock.conf
```

---

## Config Format

Hyprlock reads its config fresh on every lock invocation — no reload needed.

> **Color format:** hyprlock uses `rgba(rrggbbaa)` — 8 hex digits, no spaces, no commas. Example: `rgba(7ad4f0ff)` (fully opaque), `rgba(7ad4f0cc)` (80% opacity). **Do NOT use `rgba(r, g, b, a)` decimal form** — it is not reliably parsed across hyprlock versions and silently falls back to black.

### Full example config

```hyprlang
# hyprlock.conf — void-dragon theme

background {
    monitor =
    path = /home/user/Pictures/wallpaper.png
    blur_passes = 3
    blur_size = 6
    brightness = 0.7
    contrast = 1.0
    vibrancy = 0.2
}

# Time display
label {
    monitor =
    text = cmd[update:1000] echo "$(date +%H:%M)"
    color = rgba(7ad4f0ff)
    font_size = 88
    font_family = JetBrainsMono Nerd Font
    position = 0, 200
    halign = center
    valign = center
    shadow_passes = 2
    shadow_size = 4
    shadow_color = rgba(7ad4f0cc)
}

# Date display
label {
    monitor =
    text = cmd[update:60000] echo "$(date '+%A, %B %d')"
    color = rgba(e4f0ffff)
    font_size = 20
    font_family = JetBrainsMono Nerd Font
    position = 0, 120
    halign = center
    valign = center
}

# Password input
input-field {
    monitor =
    size = 300, 50
    outline_thickness = 2
    dots_size = 0.25
    dots_spacing = 0.3
    outer_color = rgba(7ad4f0ff)
    inner_color = rgba(1c1e2aff)
    font_color = rgba(e4f0ffff)
    fade_on_empty = true
    placeholder_text = <i>Enter password...</i>
    hide_input = false
    rounding = 0
    check_color = rgba(2a8060ff)
    fail_color = rgba(cc3090ff)
    fail_text = <b>ACCESS DENIED</b>
    capslock_color = rgba(c87820ff)
    position = 0, -20
    halign = center
    valign = center
}
```

---

## Themeable Elements

| Element | Palette Mapping |
|---------|----------------|
| `background.path` | Current wallpaper (auto-detect from awww or existing config) |
| `background.blur_passes` | 2-4 for frosted glass effect |
| `background.brightness` | 0.6-0.8 (dim for readability) |
| Time label color | primary |
| Time label shadow | primary @ 0.3 alpha |
| Date label color | foreground |
| `outer_color` | primary (input border) |
| `inner_color` | surface (input fill) |
| `font_color` | foreground |
| `check_color` | success |
| `fail_color` | danger |
| `capslock_color` | warning |
| `rounding` | 0 for sharp edges |

---

## Mood-Aware Placeholders

The placeholder text can adapt to theme mood:

| Theme Mood | Placeholder Text |
|------------|-----------------|
| Game / MapleStory | `HP: ∞ \| MP: ∞` |
| Gothic / blood | `Enter passphrase...` |
| Void / dragon | `Void gate passphrase...` |
| Default | `Enter password...` |

Set in the input-field block:
```hyprlang
placeholder_text = <i>Void gate passphrase...</i>
```

---

## Keybind

```hyprlang
bind = $mainMod SHIFT, L, exec, hyprlock
```

---

## Hypridle Integration

Hypridle triggers hyprlock after idle timeout. Config at `~/.config/hypr/hypridle.conf`:

```hyprlang
general {
    lock_cmd = pidof hyprlock || hyprlock
    before_sleep_cmd = loginctl lock-session
    after_sleep_cmd = hyprctl dispatch dpms on
}

# Screen dim after 5 minutes
listener {
    timeout = 300
    on-timeout = brightnessctl -s set 10
    on-resume = brightnessctl -r
}

# Lock after 10 minutes
listener {
    timeout = 600
    on-timeout = loginctl lock-session
}

# Screen off after 15 minutes
listener {
    timeout = 900
    on-timeout = hyprctl dispatch dpms off
    on-resume = hyprctl dispatch dpms on
}

# Suspend after 30 minutes
listener {
    timeout = 1800
    on-timeout = systemctl suspend
}
```

### Autostart

```hyprlang
exec-once = hypridle
```

### Tips

- `pidof hyprlock || hyprlock` prevents multiple lock instances
- `before_sleep_cmd` ensures lock happens before lid close / suspend
- `after_sleep_cmd` with `dpms on` ensures monitors wake after resume
- Brightness dimming gives a visual warning before lock kicks in
