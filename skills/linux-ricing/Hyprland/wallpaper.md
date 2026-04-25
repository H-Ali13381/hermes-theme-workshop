# Wallpaper — awww Daemon

Use `awww` for wallpapers on Hyprland. **Not hyprpaper** — v0.8.3 (Arch repos, April 2026) is broken.

---

## Why Not hyprpaper

hyprpaper v0.8.3 silently fails — starts fine, no errors, desktop stays black. Config parsing fails with *"Monitor X has no target: no wp will be created"* regardless of config format. `hyprctl hyprpaper listloaded` returns "invalid hyprpaper request".

**Use `awww` instead** — the swww rename (v0.12.0+), available in Arch repos.

---

## Package

```bash
sudo pacman -S awww
```

---

## Basic Usage

### Start the daemon

```bash
awww-daemon &
sleep 2    # daemon must be ready before setting wallpaper
```

### Set wallpaper

```bash
awww img /path/to/wallpaper.png
```

### Verify

```bash
awww query
```

### awww subcommands

| Command | Description |
|---------|-------------|
| `awww-daemon` | Start the daemon (must run first) |
| `awww img <path>` | Set wallpaper on all monitors |
| `awww query` | Show what's displayed on each monitor |
| `awww clear` | Clear wallpaper |
| `awww restore` | Restore last image |

---

## Multi-Monitor Setup

awww handles multi-monitor automatically — no per-monitor config needed. `awww img` sets the wallpaper on all connected monitors.

---

## Hyprland Autostart

```hyprlang
exec-once = awww-daemon
exec-once = awww img /home/user/Pictures/wallpaper.png
```

**PITFALL:** awww-daemon must be running before `awww img`. In exec-once, Hyprland processes lines sequentially with slight delays — this usually works. For manual restart, add an explicit sleep:

```bash
awww-daemon &
sleep 2
awww img /path/to/wallpaper.png
```

**PITFALL:** `awww img` panics with *"failed to connect to socket"* if awww-daemon is not running. Always check first:

```bash
pgrep awww-daemon || hyprctl dispatch exec awww-daemon
sleep 2
awww img /path/to/wallpaper.png
```

---

## HDMI DPMS Fix

Some HDMI monitors (especially TVs) go dark whenever display-related processes (awww-daemon, waybar, plasmashell) are killed or restarted. The monitor shows as detected in `hyprctl monitors` but the screen is physically black.

### Fix every time

```bash
hyprctl keyword monitor "HDMI-A-1,1920x1080@60,1920x0,1"
hyprctl dispatch dpms on HDMI-A-1
```

### Fix on login (add to autostart with delay)

```hyprlang
exec-once = sleep 2 && hyprctl dispatch dpms on HDMI-A-1
```

### Full wallpaper + DPMS recovery

```bash
pkill awww-daemon; sleep 1
awww-daemon &
sleep 2
awww img /path/to/wallpaper.png
hyprctl keyword monitor "HDMI-A-1,1920x1080@60,1920x0,1"
hyprctl dispatch dpms on HDMI-A-1
```

---

## Palette Extraction Integration

Extract a color palette from your wallpaper to theme the entire desktop:

### Using ricer CLI

```bash
ricer extract --image ~/Pictures/wallpaper.png --out design.json --name my-theme
ricer apply --design design.json
```

### Using ricer extract + apply in one step

```bash
ricer apply --wallpaper ~/Pictures/wallpaper.png --extract
```

### How extraction works

1. Loads the image, composites alpha over `#808080`
2. Downsamples to 400×400 for speed
3. Quantizes to 12 colors via MAXCOVERAGE
4. Classifies swatches into buckets (Vibrant, DarkMuted, LightVibrant, etc.)
5. Assigns 10 semantic palette keys with fallback cascades
6. Validates contrast (≥4.5:1 bg/fg) and slot uniqueness
7. Infers mood tags (dark/light, warm/cool, vibrant/muted)

### Python API

```python
from palette_extractor import extract_palette
design = extract_palette("/path/to/wallpaper.jpg", name="my-theme")
# Returns: {"name": ..., "palette": {...}, "mood_tags": [...]}
```

### Preview in kitty

```bash
kitty +kitten icat ~/Pictures/wallpaper.png
```

---

## Wallpaper Change Workflow

When switching wallpapers mid-session:

```bash
# Set the new wallpaper
awww img /path/to/new-wallpaper.png

# Fix HDMI if it went dark
hyprctl dispatch dpms on HDMI-A-1

# Optionally extract palette and re-theme everything
ricer apply --wallpaper /path/to/new-wallpaper.png --extract

# Update hyprlock background
sed -i "s|path = .*|path = /path/to/new-wallpaper.png|" ~/.config/hypr/hyprlock.conf
```
