# Picom Theming

Picom is an X11 compositor providing shadows, transparency, fading, and blur. It reads `~/.config/picom/picom.conf` (or `~/.config/picom.conf`). The ricer writes a **fragment file** and sources it rather than rewriting the main config.

> **Hyprland users:** Picom is X11-only. Hyprland has its own built-in compositor — see `Hyprland/borders-animations.md`. Picom is only relevant on i3, Sway (XWayland), bspwm, openbox, or KDE with KWin disabled.

---

## How ricer.py Applies the Theme

1. Writes `~/.config/picom/hermes-picom.conf` from `templates/picom/hermes-picom.conf.template`
2. Sources it from the main config — injects `@include "hermes-picom.conf"` at the top if not present (picom supports `@include` directives)
3. Sends SIGHUP to reload: `pkill -SIGUSR1 picom` (or full restart)

**Template variables used:**

| Variable | Role |
|----------|------|
| `{{name}}` | Theme name — comment header |
| `{{shadow_color}}` | Drop shadow color (hex string, e.g. `"#000000"`) |

Most picom theming is structural (blur radius, opacity, fade timing) rather than palette-driven. The ricer controls the shadow color and opacity; blur and fade are fixed to sane defaults.

---

## What the Template Controls

```conf
shadow-color = "{{shadow_color}}";   ← from design_system
shadow = true;
shadow-radius = 14;
shadow-opacity = 0.65;
shadow-offset-x = -8;
shadow-offset-y = -8;

fading = true;
fade-delta = 5;
fade-in-step = 0.04;
fade-out-step = 0.04;

active-opacity = 1.0;
inactive-opacity = 0.92;
```

---

## Full Picom Config Structure

The main `~/.config/picom/picom.conf` should source the fragment:

```conf
@include "hermes-picom.conf"

# Backend — use glx for performance, xrender for compatibility
backend = "glx";
vsync = true;

# Per-app opacity rules
opacity-rule = [
    "100:class_g = 'i3lock'",
    "95:class_g = 'Rofi'"
];

# Blur (optional — expensive on low-end GPU)
blur-method = "dual_kawase";
blur-strength = 5;
blur-background = true;
blur-background-exclude = [
    "window_type = 'dock'",
    "class_g = 'slop'"
];
```

---

## Opacity Tuning by Theme

| Stance | Recommended inactive-opacity | Blur |
|--------|------------------------------|------|
| Ghost | 0.85–0.90 | Yes — frosted glass |
| Signal | 0.95–1.00 | No — full clarity |
| Blade | 0.88–0.92 | Subtle (strength 3) |
| Zen | 0.92–0.96 | Soft (strength 4) |
| Riot | 1.00 | No |
| Garden | 0.90–0.94 | Yes |
| Drift | 0.85–0.92 | Yes — heavy (strength 7) |

---

## Reload After Apply

```bash
# Graceful reload (SIGUSR1) — preferred
pkill -SIGUSR1 picom

# Hard restart if SIGUSR1 doesn't work:
pkill picom && picom --daemon
```

---

## Pitfalls

- **`@include` requires picom ≥ 9.1.** Older versions don't support it. Check: `picom --version`. If older, fall back to full config rewrite.
- **GLX backend + Nvidia:** may cause screen tearing without `nvidia-drm.modeset=1` in kernel params. If tearing is visible, switch to `backend = "xrender"`.
- **Shadow exclusions:** always exclude `window_type = 'dock'` (bars) and `window_type = 'desktop'` (wallpaper) from shadows.
- **`inactive-opacity` + terminals:** some terminal emulators fight picom's opacity with their own built-in transparency setting. Set terminal opacity to 1.0 and let picom handle it.
- **KDE + picom:** KDE uses KWin as compositor. Running picom alongside KWin will cause double-compositing artifacts. Disable KWin compositing first: `qdbus6 org.kde.KWin /Compositor suspend`.
