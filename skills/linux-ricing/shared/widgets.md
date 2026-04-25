# Custom Widgets — EWW (ElKowars Wacky Widgets)

## 1. Overview

The AI-designed widget pipeline turns a text description into a fully functional desktop widget:

```
describe UI element → generate mockup image → iterate visually →
slice into components → build EWW widget (Yuck + SCSS) →
configure layer-shell positioning → wire to live system data
```

**Why EWW?** It's the r/unixporn standard for custom widgets:
- **Yuck** markup for layout (Lisp-like, declarative)
- **SCSS** for styling (supports `background-image`, gradients, transparency)
- **GTK Layer Shell** for Wayland compositors (Hyprland, Sway, KDE Wayland)
- **GDK X11** fallback for X11 sessions
- Massive ricing community with examples and inspiration

---

## 2. EWW Installation

### Arch Linux (AUR)
```bash
yay -S eww          # or: paru -S eww
```

### Other distros — build from source
```bash
# Requires Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

git clone https://github.com/elkowar/eww.git
cd eww
cargo build --release --no-default-features --features=wayland
# For X11: cargo build --release --no-default-features --features=x11

sudo cp target/release/eww /usr/local/bin/
```

### Verify
```bash
eww --version
```

---

## 3. EWW Basics

### Config location
```
~/.config/eww/
├── eww.yuck       ← layout & widget definitions
├── eww.scss       ← styles (SCSS, not raw CSS)
├── scripts/       ← polling/listener scripts
└── images/        ← sliced textures, icons, backgrounds
```

### Core concepts

| Concept | Purpose |
|---------|---------|
| `defwindow` | Top-level window with geometry, stacking, and monitor config |
| `defwidget` | Reusable widget component with properties |
| `defvar` | Static variable |
| `defpoll` | Variable updated on interval (runs a shell command) |
| `deflisten` | Variable updated by streaming script (stdout lines) |

### Simple example — styled clock with background image

**eww.yuck:**
```lisp
(defpoll clock-time :interval "1s" "date '+%H:%M'")
(defpoll clock-date :interval "60s" "date '+%A, %B %d'")

(defwindow clock-widget
  :monitor 0
  :geometry (geometry :x "20px" :y "20px" :width "200px" :height "80px" :anchor "top right")
  :stacking "overlay"
  :exclusive false
  :focusable false
  (clock-display))

(defwidget clock-display []
  (box :class "clock-container" :orientation "v" :space-evenly false
    (label :class "clock-time" :text clock-time)
    (label :class "clock-date" :text clock-date)))
```

**eww.scss:**
```scss
.clock-container {
  background-image: url("images/clock-bg.png");
  background-size: cover;
  border-radius: 12px;
  padding: 10px 16px;
}
.clock-time {
  font-size: 28px;
  font-weight: bold;
  color: #e4f0ff;
}
.clock-date {
  font-size: 12px;
  color: rgba(228, 240, 255, 0.7);
}
```

**Launch:** `eww daemon && eww open clock-widget`

---

## 4. AI Image → Widget Pipeline

### Step 1: Describe the UI element
User provides a description:
> "MapleStory inventory bar, wooden texture, gold trim, 8 item slots, HP and MP bars at the bottom"

### Step 2: Generate mockup via image_gen
AI generates a visual mockup image. The mockup should be:
- The exact intended size or proportional
- Clean edges suitable for slicing
- Distinct visual regions for each component

### Step 3: Iterate visually
User reviews and refines: "make buttons rounder", "add glow effect to active slot", "HP bar should be red gradient". Re-generate until satisfied.

### Step 4: Slice image into components

Using **ImageMagick** to crop regions:
```bash
# Background texture (full width)
convert mockup.png -crop 800x60+0+0 bar-background.png

# Individual button states
convert mockup.png -crop 48x48+10+6 slot-normal.png
convert mockup.png -crop 48x48+70+6 slot-hover.png

# Decorative elements
convert mockup.png -crop 20x60+0+0 border-left.png
convert mockup.png -crop 20x60+780+0 border-right.png

# HP/MP bar backgrounds
convert mockup.png -crop 200x12+300+44 hp-bar-bg.png
convert mockup.png -crop 200x12+510+44 mp-bar-bg.png
```

Using **Pillow** (Python) for programmatic slicing:
```python
from PIL import Image
img = Image.open("mockup.png")
# crop((left, upper, right, lower))
bg = img.crop((0, 0, 800, 60))
bg.save("bar-background.png")
```

Components to extract:
- **Background texture** — 9-slice or full-width stretch
- **Button states** — normal, hover, active (3 images per button type)
- **Decorative elements** — borders, corners, dividers, icons
- **Progress bar backgrounds** — empty and fill textures

### Step 5: Build EWW widget using sliced images as CSS backgrounds
Map each sliced image to an EWW widget element with SCSS `background-image`.

### Step 6: Configure positioning and behavior
Set `defwindow` geometry, stacking order, exclusive zone, and monitor placement.

---

## 5. Hover-to-Reveal Pattern

A common pattern: an invisible trigger zone at a screen edge that reveals a styled bar on mouse hover.

### Architecture — Two EWW windows

1. **Trigger bar** — 2px tall, transparent, always visible, anchored to screen edge
2. **Main widget** — the actual styled bar, toggled via `eww open/close`

### Complete working example

**eww.yuck:**
```lisp
;; Invisible trigger zone
(defwindow trigger-bar
  :monitor 0
  :geometry (geometry :x "0%" :y "0px" :width "100%" :height "2px" :anchor "top center")
  :stacking "overlay"
  :exclusive false
  :focusable false
  :namespace "eww-trigger-bar"
  (box :class "trigger-zone"))

;; Actual styled bar
(defwindow main-bar
  :monitor 0
  :geometry (geometry :x "0%" :y "0px" :width "100%" :height "48px" :anchor "top center")
  :stacking "overlay"
  :exclusive false
  :focusable false
  :namespace "eww-bar-main"
  (bar-content))

(defwidget bar-content []
  (box :class "bar-container" :orientation "h" :space-evenly false
    (label :class "bar-text" :text "AI-designed bar content here")))
```

**eww.scss:**
```scss
.trigger-zone {
  background-color: transparent;
}
.bar-container {
  background-image: url("images/bar-background.png");
  background-size: cover;
  min-height: 48px;
  padding: 0 16px;
}
.bar-text {
  color: #e4f0ff;
  font-size: 14px;
}
```

**scripts/toggle-bar.sh:**
```bash
#!/bin/bash
# Run this script with the trigger bar's window events
# Usage: eww daemon && eww open trigger-bar
# The trigger bar's enter/leave events toggle the main bar

LOCK_FILE="/tmp/eww-bar-lock"
BAR_NAME="main-bar"

show_bar() {
  touch "$LOCK_FILE"
  eww open "$BAR_NAME" 2>/dev/null
}

hide_bar() {
  rm -f "$LOCK_FILE"
  sleep 0.3  # grace period for mouse to reach main bar
  [ ! -f "$LOCK_FILE" ] && eww close "$BAR_NAME" 2>/dev/null
}

case "$1" in
  show) show_bar ;;
  hide) hide_bar ;;
esac
```

---

## 6. Image Textures in SCSS

### Basic background image
```scss
.widget {
  background-image: url("images/texture.png");
  background-size: cover;        // stretch to fill
  background-repeat: no-repeat;
}
```

### 9-slice technique for resizable textures
```scss
.resizable-panel {
  border-image: url("images/panel-9slice.png") 12 12 12 12 fill stretch;
  // 12px borders on all sides, fill center, stretch to fit
}
```

### Transparent windows
```scss
window {
  background-color: transparent;  // MUST set on the window itself
}
```

### Layering multiple images
```scss
.layered {
  background-image:
    url("images/overlay-pattern.png"),
    url("images/base-texture.png");
  background-size: 100% 100%, cover;
}
```

### Image path rules
- Paths are relative to `~/.config/eww/`
- Absolute paths also work: `/home/user/.config/eww/images/bg.png`
- PNG with alpha channel for transparency

---

## 7. Wiring to System Data

### Polling variables (periodic updates)
```lisp
(defpoll volume :interval "1s" "wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2*100)}'")
(defpoll battery :interval "30s" "cat /sys/class/power_supply/BAT0/capacity")
(defpoll clock :interval "1s" "date '+%H:%M'")
(defpoll network :interval "5s" "nmcli -t -f NAME connection show --active | head -1")
```

### Listener variables (streaming/event-driven)
```lisp
(deflisten media-title "playerctl --follow metadata title 2>/dev/null || echo ''")
(deflisten media-artist "playerctl --follow metadata artist 2>/dev/null || echo ''")
```

### Environment-specific data sources

| Data | Hyprland | KDE | Generic |
|------|----------|-----|---------|
| Workspaces | `hyprctl` + `socat` | `qdbus6` | `wmctrl -d` |
| Active window | `hyprctl activewindow` | `qdbus6 org.kde.KWin` | `xdotool getactivewindow` |
| Volume | `wpctl` / `pamixer` | `qdbus6` | `pamixer` / `pactl` |
| Media | `playerctl` | `playerctl` | `playerctl` |
| Brightness | `brightnessctl` | `qdbus6` | `brightnessctl` |

---

## 8. Materializer Contract

How `ricer.py` should generate EWW configs from a design system:

### SCSS palette variables
```scss
// Auto-generated by ricer.py from design_system.json
$background: #0c1220;
$foreground: #e4f0ff;
$primary:    #7ad4f0;
$secondary:  #0d2e32;
$accent:     #d4a012;
$surface:    #1c1e2a;
$muted:      #3d2214;
$danger:     #cc3090;
$success:    #2a8060;
$warning:    #c87820;
```

### Template location
Templates at `templates/eww/` — Jinja2 files for `eww.yuck` and `eww.scss`.

### Activation commands
```bash
eww daemon && eww open <window-name>   # start and show
eww reload                              # hot-reload SCSS changes
eww kill && eww daemon && eww open <window>  # full restart (for Yuck changes)
```

---

## 9. Widget Framework Comparison

| Framework | Language | Wayland | X11 | Image Textures | Community |
|-----------|----------|---------|-----|----------------|-----------|
| **EWW** | Yuck + SCSS | Yes (layer-shell) | Yes (GDK) | Native CSS | Large (r/unixporn standard) |
| **AGS** | TypeScript | Yes | No | Yes | Medium |
| **Fabric** | Python | Yes | No | Yes | Small |
| **Plasmoid** | QML/JS | KDE only | KDE only | Yes | KDE community |

**EWW is the recommended default** for the AI pipeline — widest compatibility, most community examples, native image texture support.

---

## 10. Known Pitfalls

- **EWW daemon must be running** before `eww open` — add to autostart before any `eww open` calls
- **SCSS not CSS** — EWW compiles SCSS internally; raw CSS syntax will fail silently or error
- **`exclusive: false`** means the widget doesn't reserve screen space — important for overlays, but means windows render behind/over it
- **Hot-reload limitations** — `eww reload` picks up SCSS changes but NOT Yuck structural changes; for those: `eww kill && eww daemon`
- **GTK Layer Shell varies by compositor**:
  - Works great on Hyprland/Sway
  - Works on KDE Wayland but may fight with Plasma panels at the same edge
  - Not available on X11 (falls back to GDK X11)
- **X11 z-ordering** — use `stacking: bg` or `wmctrl -r 'eww' -b add,sticky,above` for reliable layering
- **Image paths in SCSS** must be absolute or relative to `~/.config/eww/` — relative to the SCSS file does NOT work
- **Large images** — use optimized PNGs; uncompressed 4K textures cause noticeable lag on lower-end GPUs
