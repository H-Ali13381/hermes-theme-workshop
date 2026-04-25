# Borders, Animations & Window Rules

Hyprland visual tuning: border colors, gaps, rounding, animation curves, and window rules.

---

## Border Colors from Palette

Borders support gradients with angle. Use `rgba()` format with alpha suffix.

```hyprlang
general {
    gaps_in = 4
    gaps_out = 8
    border_size = 2
    col.active_border = rgba(7ad4f0ee) rgba(d4a012ee) 45deg
    col.inactive_border = rgba(0c1220aa)
    layout = dwindle
}
```

### Palette Mapping

| Setting | Palette Key | Notes |
|---------|-------------|-------|
| `col.active_border` (start) | primary | First gradient color |
| `col.active_border` (end) | accent | Second gradient color |
| `col.inactive_border` | background @ reduced alpha | Faded background |

### Gradient angles

- `45deg` — diagonal sweep (most common)
- `0deg` — horizontal left-to-right
- `90deg` — vertical top-to-bottom

### Solid border (no gradient)

```hyprlang
col.active_border = rgba(7ad4f0ee)
col.inactive_border = rgba(1c1e2a88)
```

---

## Rounding

**CRITICAL:** `rounding` lives in `decoration {}`, NOT `general {}`. Putting it in `general {}` causes: *"general:rounding does not exist"*.

```hyprlang
decoration {
    rounding = 0       # 0 = sharp corners, 6-12 = rounded
    
    blur {
        enabled = false   # disable if terminal transparency looks muddy
        size = 3
        passes = 1
    }

    shadow {
        enabled = true
        range = 8
        render_power = 2
        color = rgba(0c122066)
    }
}
```

### Blur + transparency interaction

If the user has a semi-transparent terminal (`background_opacity 0.85`) and compositor blur enabled, the result is muddy/distorted. Disable blur to fix:

```bash
hyprctl keyword decoration:blur:enabled false
```

---

## Gaps

```hyprlang
general {
    gaps_in = 4      # gap between tiled windows
    gaps_out = 8     # gap between windows and screen edge
}
```

Themed suggestions:
- **Minimal/game-UI:** `gaps_in = 2`, `gaps_out = 4`
- **Cozy/relaxed:** `gaps_in = 6`, `gaps_out = 12`
- **Zero-gap:** `gaps_in = 0`, `gaps_out = 0`

---

## Animation Curves

Custom bezier curves for themed feel. Snappy = game-like, floaty = ambient.

```hyprlang
animations {
    enabled = true

    # Game-UI snappy curves
    bezier = voidSnap,  0.05, 0.9,  0.1,  1.0
    bezier = voidSlide, 0.16, 1,    0.3,  1
    bezier = voidFade,  0.33, 1,    0.68, 1

    animation = windows,     1, 4, voidSnap,  slide
    animation = windowsOut,  1, 4, voidSnap,  slide
    animation = fade,        1, 5, voidFade
    animation = workspaces,  1, 4, voidSlide, slide
    animation = border,      1, 6, voidFade
    animation = borderangle, 1, 30, voidFade, loop
}
```

### Bezier curve cheat sheet

| Name | Character | Use Case |
|------|-----------|----------|
| `0.05, 0.9, 0.1, 1.0` | Snappy with slight overshoot | Window open/close |
| `0.16, 1, 0.3, 1` | Fast start, smooth stop | Workspace slide |
| `0.33, 1, 0.68, 1` | Linear-ish ease | Fades, border color |
| `0.68, -0.55, 0.265, 1.55` | Bounce | Playful/cartoon themes |
| `0.25, 0.1, 0.25, 1` | CSS ease equivalent | Generic smooth |

### Border angle animation

`borderangle` with `loop` creates a continuously rotating gradient on focused windows — effective for glowing accent borders:

```hyprlang
animation = borderangle, 1, 30, voidFade, loop
```

---

## Window Rules (Hyprland 0.54.x)

**CRITICAL:** `windowrulev2` is deprecated. Use `windowrule` instead.

```hyprlang
# Terminal transparency
windowrule = opacity 0.92 0.85, class:^(kitty)$

# Float specific apps
windowrule = float, class:^(rofi)$
windowrule = float, class:^(pavucontrol)$
windowrule = float, title:^(Picture-in-Picture)$

# Pin picture-in-picture
windowrule = pin, title:^(Picture-in-Picture)$
windowrule = size 480 270, title:^(Picture-in-Picture)$
windowrule = move 100%-490 100%-280, title:^(Picture-in-Picture)$

# File picker float
windowrule = float, title:^(Open File)$
windowrule = float, title:^(Save As)$

# Disable blur on specific apps (performance)
windowrule = noblur, class:^(firefox)$
```

### Opacity format

```
windowrule = opacity <active> <inactive>, <match>
```
- `0.92 0.85` = 92% when focused, 85% when unfocused
- `1.0 1.0` = fully opaque

### Frame overlay rules

For a fullscreen transparent overlay (advanced chrome):

```hyprlang
windowrule = float, class:frame-overlay
windowrule = size 100% 100%, class:frame-overlay
windowrule = move 0 0, class:frame-overlay
windowrule = pin, class:frame-overlay
windowrule = nofocus, class:frame-overlay
windowrule = noborder, class:frame-overlay
```

---

## Deprecated Settings (0.54.x Migration)

| Old | Status | Replacement |
|-----|--------|-------------|
| `windowrulev2` | Deprecated | `windowrule` |
| `dwindle:no_gaps_when_only` | Removed | No direct replacement |
| `force_default_wallpaper` | Removed | Use wallpaper daemon |
| `disable_splash_rendering` | Removed | N/A |
| `general:rounding` | Never existed here | Use `decoration { rounding }` |
