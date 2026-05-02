# Custom Widgets — Quickshell (default) & EWW (fallback)

## 0. Framework Selection

The skill picks one of two widget frameworks automatically based on the running compositor.

| Compositor / session | Default | Why |
|----------------------|---------|-----|
| Hyprland (Wayland) | **Quickshell** | Native `wlr-layer-shell`; QML hot-reload; rich built-in services |
| KDE Plasma (Wayland) | **Quickshell** | KWin supports `wlr-layer-shell`; QML matches Plasma's own toolkit |
| KDE Plasma (X11) | **EWW** | No layer-shell on X11; EWW falls back to GDK X11 windowing |
| GNOME / other | **EWW** | Mutter has no layer-shell; EWW is the broadest-compatibility option |

The selection logic lives in `workflow/nodes/refine.py:_default_widget_element()` and is mirrored
in `workflow/nodes/install/resolver.py:_widget_framework_for()`. A design that explicitly names
`widgets:eww` or `widgets:quickshell` in `chrome_strategy.implementation_targets` overrides the
default.

> **Panel-interference caveat (both frameworks).** Quickshell and EWW both render via
> `wlr-layer-shell` on Wayland. When their windows are anchored to the same screen edge as a
> compositor-native panel (Plasma's panel, Hyprland's `waybar`), they compete for the exclusive
> zone — you'll see a doubled gap, or one of the bars rendering on top of the other. Either
> anchor the custom widget to a different edge, drop `exclusive_zone` (set `exclusive: false` /
> `exclusionMode: ExclusionMode.Ignore`), or hide the native panel. See
> [`KDE/widgets.md`](../KDE/widgets.md#1-eww-on-kde-wayland) for the KDE-specific patterns.

This document covers EWW in depth (the fallback). Quickshell-specific QML patterns live in the
craft-pipeline knowledge base at `workflow/nodes/craft/frameworks.py`.

### Layer-shell client lifecycle (under the hood)

Every Wayland widget (Quickshell, EWW, waybar) is a layer-shell *client*; the compositor is
the *server*. Per-window steps:

1. Connect via `$WAYLAND_DISPLAY` socket.
2. Request **surface** + **buffer** handles.
3. (Optional) Request a **seat** for keyboard/pointer input.
4. **layer-shell** protocol (`wlr-layer-shell`, or GTK Layer Shell wrapping it on EWW): anchor,
   exclusive zone, layer (`background`/`bottom`/`top`/`overlay`).
5. Request **frame callback** → render into buffer when it fires → attach buffer to surface.
6. Compositor composites.

Consequences:

- **Exclusive zone causes panel interference.** Two clients (waybar + Quickshell bar) on the
  same edge with non-zero exclusive zone double the gap. Set `exclusionMode: ExclusionMode.Ignore`
  (Quickshell) or `:exclusive false` (EWW) for overlay widgets.
- **Frame callbacks fire only on redraw.** A "dead" widget is almost always one whose data
  source (Quickshell binding, EWW `defpoll`/`deflisten`) isn't emitting.

---

## 1. Pipeline & Why EWW

```
describe UI element → generate mockup image → iterate visually →
slice into components → build widget (Quickshell QML or EWW Yuck+SCSS) →
configure layer-shell positioning → wire to live system data
```

**EWW** (fallback): Yuck (Lisp-like markup) + SCSS, GTK Layer Shell on Wayland, GDK on X11.
r/unixporn standard with extensive community examples.

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
├── eww.yuck          ← layout & widget definitions (can split with `include`)
├── eww.scss          ← styles (SCSS compiled internally — not raw CSS)
├── scripts/          ← polling/listener scripts
└── images/           ← sliced textures, icons, backgrounds
```

### Splitting configs
```lisp
(include "./widgets/bar.yuck")
(include "./widgets/panel.yuck")
```

### Core variable types

| Concept | Purpose |
|---------|---------|
| `defwindow` | Top-level window with geometry, stacking, and monitor config |
| `defwidget` | Reusable widget component with optional (`?param`) and required params |
| `defvar` | Static variable — update externally with `eww update foo="value"` |
| `defpoll` | Runs a shell command on `:interval`; supports `:initial` and `:run-while` |
| `deflisten` | Runs a script once and reads stdout lines continuously (event-driven) |

### Magic built-in variables (EWW_*)

| Variable | Contents |
|----------|----------|
| `EWW_RAM` | `{total_mem, used_mem, available_mem, used_mem_perc}` |
| `EWW_CPU` | `{cores: [{core, usage}], avg}` |
| `EWW_DISK["/"]` | `{total, used, free, used_perc}` |
| `EWW_NET["eth0"]` | `{NET_UP, NET_DOWN}` |
| `EWW_BATTERY` | `{BAT0: {status, capacity}}` |
| `EWW_TIME` | Current time as string |

```lisp
; Usage examples
(label :text "${EWW_RAM.used_mem_perc}%")
(label :text "${round(EWW_CPU.avg, 0)}%")
(progress :value {EWW_CPU.avg})
```

### Window arguments (parameterized windows)
Defwindow can accept arguments — essential for multi-monitor bars:
```lisp
(defwindow my_bar [screen ?size]
  :monitor screen
  :geometry (geometry :width "100%" :height {size ?: "40px"} :anchor "top center")
  :stacking "overlay" :exclusive true
  (bar-content))
```
```bash
eww open my_bar --id bar-0 --arg screen=0 --arg size=48px
eww open my_bar --id bar-1 --arg screen=1
```

### Simple example — styled clock with background image

**eww.yuck:**
```lisp
(defpoll clock-time :interval "1s" "date '+%H:%M'")
(defpoll clock-date :interval "60s" "date '+%A, %B %d'")

(defwindow clock-widget
  :monitor 0
  :geometry (geometry :x "20px" :y "20px" :width "200px" :height "80px" :anchor "top right")
  :stacking "overlay"   ; Wayland: "overlay" | X11/X.Org: "fg" | background: "bg"
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

## 4. Full Widget Reference

### Layout widgets

**`box`** — primary layout container
```lisp
(box :orientation "h"   ; or "v"
     :spacing 8
     :space-evenly false
     :halign "start"    ; fill | baseline | center | start | end
     :valign "center"
     :hexpand true
     (label :text "left")
     (label :text "right"))
```

**`centerbox`** — exactly 3 children, placed at start / center / end
```lisp
(centerbox :orientation "h"
  (workspaces)   ; left
  (clock)        ; center
  (tray))        ; right
```

**`overlay`** — stacks children on top of each other; takes the size of the **first** child
```lisp
(overlay
  (box :class "panel-bg" :width 300 :height 80)   ; ← sets the size
  (image :path "images/ornament.png" :image-width 300 :image-height 80)
  (label :class "panel-text" :text "HP 450"))
```
> ⚠️ **The first child defines the overlay's dimensions.** All subsequent children are layered on top. Use explicit `:width`/`:height` on the first child.

**`scroll`**
```lisp
(scroll :vscroll true :hscroll false
  (box :orientation "v" (label :text "item 1") (label :text "item 2")))
```

**`stack`** — shows exactly one child at a time with optional transition
```lisp
(defvar active-tab 0)
(stack :selected active-tab :transition "slideright"
  (inventory-panel)
  (stats-panel)
  (map-panel))
```

### Interactive widgets

**`button`** — wraps any widget; events fire on release
```lisp
(button :onclick "notify-send 'clicked'"
        :onrightclick "eww open context-menu"
        :onmiddleclick "eww close panel"
  (label :text "⚔ Attack"))
```

**`eventbox`** — hover/scroll events without visual appearance; use for hot zones
```lisp
(eventbox :onhover "eww update panel-visible=true"
          :onhoverlost "eww update panel-visible=false"
          :onscroll "scripts/handle-scroll.sh {}"  ; {} = "up" or "down"
          :cursor "pointer"
  (box :class "slot" (image :path "images/item.png" :image-width 48 :image-height 48)))
```
> Supports `:onclick`, `:onmiddleclick`, `:onrightclick`, `:ondropped`, `:dragvalue`, `:dragtype`.

**`scale`** — slider (use for volume controls, not styled HP bars — use `progress` for those)
```lisp
(scale :min 0 :max 100 :value volume
       :orientation "h"
       :onchange "wpctl set-volume @DEFAULT_AUDIO_SINK@ {}%")
```

**`revealer`** — animated show/hide; transitions: `slideright slideleft slideup slidedown crossfade none`
```lisp
(defvar inv-open false)
(revealer :reveal inv-open
          :transition "slidedown"
          :duration "300ms"
  (inventory-widget))
```
> ⚠️ **Known issue**: a `button` inside a `revealer` inside an `overlay` may not receive clicks. Workaround: avoid nesting `revealer` inside `overlay`; use separate windows instead.

**`expander`** — built-in expand/collapse
```lisp
(expander :name "Stats" :expanded false
  (stats-content))
```

### Display widgets

**`label`** — rich text display
```lisp
(label :text "HP: ${hp_val}"
       :markup "<span foreground='#ff4444'><b>DANGER</b></span>"
       :angle 45.0          ; rotate text
       :wrap true
       :limit-width 20      ; truncate at N chars
       :xalign 0.0)         ; 0=left 0.5=center 1=right
```

**`image`** — renders PNG, SVG, animated GIF
```lisp
(image :path "images/hero-portrait.png"
       :image-width 64      ; ⚠️ INTEGER, not "64px"
       :image-height 64
       :preserve-aspect-ratio true)
; For dynamic paths:
(defpoll album-art :interval "2s" "scripts/get-art.sh")
(image :path album-art :image-width 50 :image-height 50)
; Animated GIFs auto-play — no extra configuration needed
(image :path "images/maple-sparkle.gif" :image-width 32 :image-height 32)
```
> ⚠️ **`image-width`/`image-height` must be plain integers**, not strings like `"64px"`. The widget will silently fail to display if you pass a px string.

**`progress`** — HP/MP/XP bars
```lisp
(progress :class "hp-bar"
          :value {hp_current}
          :min 0 :max {hp_max}   ; wait — min/max are NOT properties
          :orientation "h"
          :flipped false)
; Note: progress only has :value (0-100). To show a fraction, compute it:
(progress :value {round(hp / hp_max * 100, 0)})
```
CSS node path for styling:
```scss
.hp-bar {
  background-color: transparent;           // trough (empty portion)
  background-image: url("images/hp-bar-bg.png");
  background-size: cover;
  min-height: 16px;
  min-width: 200px;                        // required or bar collapses
}
.hp-bar > trough {
  background-color: transparent;
  border-radius: 0;
}
.hp-bar > trough > progress {
  background-color: transparent;
  background-image: url("images/hp-bar-fill.png");
  background-size: cover;                  // fill image clips with bar value
}
```

**`circular-progress`** — circular stat ring
```lisp
(circular-progress :class "cpu-ring"
                   :value {EWW_CPU.avg}
                   :start-at 75          ; 0=right, 25=bottom, 50=left, 75=top
                   :thickness 8
                   :clockwise true)
```
```scss
.cpu-ring {
  color: #7ad4f0;          // fill color
  background-color: rgba(0,0,0,0.3);   // track color
  min-width: 60px;
  min-height: 60px;
}
```

**`graph`** — time-series sparkline
```lisp
(graph :class "net-graph"
       :value {EWW_NET["eth0"].NET_DOWN}
       :time-range "60s"
       :thickness 2
       :line-style "round"
       :dynamic true)
```

**`transform`** — rotate / scale / translate any widget
```lisp
(transform :rotate 45
           :scale-x "1.2" :scale-y "1.2"
           :translate-x "10px" :translate-y "0px"
  (image :path "images/star.png" :image-width 32 :image-height 32))
```

**`literal`** — render a Yuck string as a widget (for fully dynamic widget trees)
```lisp
(defvar slot-widgets "(box (label :text 'empty'))")
(literal :content slot-widgets)
; Update from a script: eww update slot-widgets="$(scripts/gen-slots.sh)"
```

### `for` loop — generate grids from JSON
```lisp
(defpoll inventory :interval "1s" "scripts/get-inventory.sh")
; Script outputs: [{"icon":"sword.png","qty":1},{"icon":"potion.png","qty":5}]

(box :class "inventory-grid" :orientation "h" :space-evenly false :wrap true
  (for item in inventory
    (eventbox :class "item-slot"
              :onrightclick "scripts/use-item.sh ${item.icon}"
      (overlay
        (box :class "slot-bg" :width 48 :height 48)
        (image :path "images/${item.icon}" :image-width 40 :image-height 40)
        (label :class "item-qty" :text "${item.qty}" :valign "end" :halign "end")))))
```

### `children` — reusable wrapper widgets
```lisp
(defwidget game-panel [title]
  (box :class "panel-frame" :orientation "v"
    (label :class "panel-title" :text title)
    (children)))

(game-panel :title "Inventory"
  (inventory-grid)
  (equip-slots))
```

---

## 5. AI Image → Widget Pipeline

1. **Describe** the UI element (e.g. "wooden inventory bar, gold trim, 8 slots, HP/MP bars").
2. **Generate** mockup via `image_gen` — proportional size, clean edges, distinct regions.
3. **Iterate** visually until satisfied.
4. **Slice** components from the mockup (ImageMagick or Pillow).
5. **Build** the widget — map each slice to a Quickshell `BorderImage` / EWW SCSS `background-image`.
6. **Configure** layer-shell positioning (geometry, anchor, stacking, exclusive zone, monitor).

### Slicing — ImageMagick
```bash
convert mockup.png -crop 800x60+0+0   bar-background.png   # full-width background
convert mockup.png -crop 48x48+10+6   slot-normal.png      # button state
convert mockup.png -crop 20x60+0+0    border-left.png      # decorative edge
convert mockup.png -crop 200x12+300+44 hp-bar-bg.png       # progress bar bg
```

### Slicing — Pillow
```python
from PIL import Image
img = Image.open("mockup.png")
img.crop((0, 0, 800, 60)).save("bar-background.png")    # (left, upper, right, lower)
```

**Components to extract:** background texture (9-slice or stretch), button states (normal /
hover / active), decorative borders/corners, progress-bar empty + fill textures.

---

## 6. Hover-to-Reveal Pattern

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

## 7. GTK CSS for Game-Style Textures

EWW uses **GTK's CSS engine**, not a browser engine. Most CSS works, but some critical web CSS is absent.

### What GTK CSS supports ✅
`background-color`, `background-image`, `background-size`, `background-repeat`, `background-position`, `border-image` (full 9-slice), `border-radius`, `box-shadow`, `text-shadow`, `color`, `font-*`, `margin`, `padding`, `min-width`, `min-height`, `transition` (state-based only), `opacity`

### What GTK CSS does NOT support ❌
| Property | Status | Alternative |
|---|---|---|
| `@keyframes` / `animation` | ❌ not supported | `defpoll`-driven state toggling; `eww update` |
| `position: absolute` | ❌ not supported | `overlay` widget |
| `clip-path` | ❌ not supported | Alpha-channel PNG masks |
| `flexbox` | ❌ not supported | `box` widget with `:halign`/`:valign` |
| `float` | ❌ not supported | `box` widget |
| `width`/`height` in CSS | ⚠️ unreliable | Use `:width`/`:height` widget attrs or `min-width`/`min-height` in CSS |
| Remote `url()` images | ❌ (needs gvfs) | Download to `/tmp` in a script, use local path |

### Basic background image
```scss
.widget {
  background-image: url("images/texture.png");
  background-size: cover;        // stretch to fill
  background-repeat: no-repeat;
}
```

### 9-slice border-image — scalable ornate panel borders ✅ (fully supported in GTK)
This is the correct technique for MapleStory-style resizable wooden/gold panel borders:
```scss
.maple-panel {
  // border must be set to match the slice widths
  border-style: solid;
  border-color: transparent;
  border-width: 16px 20px 16px 20px;  // top right bottom left — match slice values

  // The 9-slice image: corners=fixed, edges=stretch or repeat, center=fill
  border-image: url("images/panel-9slice.png") 16 20 16 20 fill stretch;
  //            ↑source                         ↑slice (px)   ↑center ↑edge mode
}
```
Slice values in px (not %) are the pixel offsets from each edge where the image is cut:
```
┌──────┬──────────────┬──────┐
│  TL  │  top-edge    │  TR  │  ← top 16px
├──────┼──────────────┼──────┤
│ left │    center    │right │  ← center (fill)
├──────┼──────────────┼──────┤
│  BL  │ bottom-edge  │  BR  │  ← bottom 16px
└──────┴──────────────┴──────┘
 ←20px→                ←20px→
```
Edge repeat modes: `stretch` (default), `repeat`, `round`, `space`

### Transparent windows
```scss
window {
  background-color: transparent;  // MUST set on the eww window itself
}
.my-widget {
  background-color: transparent;  // also clear widget containers
}
```

### Layering multiple images (panel + ornament overlay)
```scss
.layered-panel {
  background-image:
    url("images/gold-ornament.png"),   // drawn on top (closest to user)
    url("images/wood-texture.png");    // drawn underneath
  background-size: auto, cover;
  background-repeat: no-repeat, no-repeat;
  background-position: center, center;
}
```

### Glow effects via box-shadow and text-shadow
```scss
.active-slot {
  box-shadow:
    0 0 8px 3px rgba(255, 200, 50, 0.8),   // outer glow (gold)
    inset 0 0 4px rgba(255, 200, 50, 0.4); // inner glow
}
.hp-label {
  text-shadow: 0 0 6px #ff2222, 1px 1px 0 #000;
}
```

### GTK CSS transitions (state-based only — no keyframes)
GTK supports `transition` for state changes (`:hover`, `:active`, `:focused`), not time-based loops:
```scss
.item-slot {
  transition: 150ms ease-in-out;
  background-color: rgba(0,0,0,0.4);
}
.item-slot:hover {
  background-color: rgba(255, 200, 50, 0.3);
  box-shadow: 0 0 8px rgba(255, 200, 50, 0.7);
}
```
> EWW `eventbox` supports `:hover` CSS selectors. `button` supports `:hover` and `:active`.

### Image path rules
- Paths are relative to `~/.config/eww/`
- Absolute paths also work: `/home/user/.config/eww/images/bg.png`
- PNG with alpha channel for non-rectangular shapes
- Remote URLs do NOT work without gvfs installed (download to `/tmp` instead)

---

## 8. Animation Patterns

GTK CSS has no `@keyframes`. All animation in EWW must be driven by **state changes** (via `defvar`/`defpoll`/`eww update`) or use GIF files.

### Animated GIFs — simplest approach
GTK natively auto-plays animated GIFs in the `image` widget. No configuration needed:
```lisp
(image :path "images/maple-sparkle.gif" :image-width 32 :image-height 32)
(image :path "images/fire-effect.gif" :image-width 64 :image-height 64)
```

### `defpoll`-driven sprite sheet animation
Cycle through frame images at a fixed interval — simulates a sprite animation:
```lisp
(defpoll sprite-frame :interval "80ms"
  "scripts/next-frame.sh")   ; outputs 0..7 cyclically
; scripts/next-frame.sh:
;   STATE_FILE=/tmp/sprite-frame
;   echo $(( ($(cat $STATE_FILE 2>/dev/null || echo -1) + 1) % 8 )) | tee $STATE_FILE

(defwidget sprite-anim []
  (image :path "images/hero-walk-${sprite-frame}.png"
         :image-width 64 :image-height 64))
```

### `eww update` + CSS transition — hover reveal with smooth slide
```lisp
(defvar panel-open false)

(eventbox :onhover "eww update panel-open=true"
          :onhoverlost "eww update panel-open=false"
  (box
    (label :text "⚔")
    (revealer :reveal panel-open
              :transition "slideright"
              :duration "250ms"
      (label :text " Attack"))))
```

### `defpoll`-driven background image swap (idle/combat state)
```lisp
(defpoll game-state :interval "2s" "scripts/check-state.sh")
; script outputs "idle" or "combat"

(box :class "status-bar"
     :style "background-image: url('images/bar-${game-state}.png'); background-size: cover;")
```

### Blinking effect via defpoll boolean toggle
```lisp
(defpoll blink :interval "500ms" "scripts/toggle.sh")
; scripts/toggle.sh: [ "$(cat /tmp/blink)" = "1" ] && echo 0 > /tmp/blink && echo 0 || echo 1 > /tmp/blink && echo 1

(label :class "warning-label"
       :style "opacity: ${blink == '1' ? '1.0' : '0.3'};"
       :text "⚠ LOW HP")
```

---

## 9. Wiring to System Data

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

### D-Bus daemon backend → `deflisten` + `literal` pipeline

For notification daemons, music daemons, or any long-running backend that pushes events: the script runs **once**, owns a D-Bus name, and `flush`es Yuck syntax strings to stdout on every event. `deflisten` picks up each flushed line; `literal` renders it as a live widget tree.

```
Python daemon ──stdout──▶ deflisten ──▶ literal (renders Yuck string as widget)
```

**eww.yuck:**
```lisp
(deflisten notifications "scripts/notification-daemon.py")

(defwindow notif-window
  :monitor 0
  :geometry (geometry :x "20px" :y "20px" :anchor "top right")
  :stacking "overlay" :exclusive false
  (literal :content notifications))
```

**scripts/notification-daemon.py** (skeleton):
```python
import dbus, dbus.service, dbus.mainloop.glib, gi, threading, sys
from gi.repository import GLib

class NotifServer(dbus.service.Object):
    def __init__(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        bus.request_name("org.freedesktop.Notifications")
        super().__init__(bus, "/org/freedesktop/Notifications")
        self.notifications = []

    @dbus.service.method("org.freedesktop.Notifications",
                         in_signature="susssasa{sv}i", out_signature="u")
    def Notify(self, app_name, replaces_id, icon, summary, body, actions, hints, timeout):
        n = {"summary": str(summary), "body": str(body), "icon": str(icon)}
        self.notifications.insert(0, n)
        threading.Timer(10, lambda: self.dismiss(n)).start()
        self.flush()
        return replaces_id or 1

    def dismiss(self, n):
        self.notifications = [x for x in self.notifications if x is not n]
        self.flush()

    def flush(self):
        # Output a Yuck string — eww deflisten captures each print() as a new value
        items = "".join(
            f'(box :class "notif" (label :text "{n["summary"]}: {n["body"]}"))'
            for n in self.notifications
        )
        print(f'(box :orientation "v" {items})', flush=True)

NotifServer()
GLib.MainLoop().run()
```

**Required packages:** `dbus-python`, `python-gobject` (PyGObject)

> **Key insight:** Every `print(..., flush=True)` call replaces the entire `deflisten` variable. `literal` re-renders the new Yuck tree instantly. This pattern works for any daemon (music, hotkey, game state monitor) — not just notifications.

### Launcher toggle pattern

Prevent double-opening an app launcher from both a keybind and a widget button:

```bash
# Shell one-liner: close if open, open if closed
pkill wofi || wofi --show drun
pkill rofi || rofi -show drun
```

The EWW equivalent for toggling a panel window:
```bash
eww open --toggle my-panel-window
```

Use `eww open --toggle` in widget `:onclick` handlers:
```lisp
(button :onclick "eww open --toggle inventory-panel"
  (label :text "🎒 Inventory"))
```

---

## 10. Debugging

### GTK Inspector (essential for CSS issues)
```bash
eww inspector
```
Opens GTK's visual inspector. Click the crosshair icon → hover a widget to see its CSS node path, computed properties, and the full GTK widget tree. This is how you discover undocumented node paths like `.my-bar > trough > progress`.

### eww logs
```bash
eww logs    # tail the eww daemon log
```

### Shell test for scripts
```bash
# Test a defpoll command directly
bash -c "date '+%H:%M'"
bash -c "scripts/get-workspaces.sh"
```

### Common debug pattern
```lisp
; Add a debug label to see live variable values
(label :text "cpu=${EWW_CPU.avg} | ram=${EWW_RAM.used_mem_perc}")
```

---

## 11. Materializer Contract

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

## 12. Widget Framework Comparison

| Framework | Language | Wayland | X11 | Image Textures | Community |
|-----------|----------|---------|-----|----------------|-----------|
| **Quickshell** | QML | Yes (layer-shell) | Windowing only (no layer-shell) | Yes (`BorderImage`) | Large (active 2025+; supersedes AGS in most rices) |
| **EWW** | Yuck + SCSS | Yes (layer-shell) | Yes (GDK) | Native CSS | Large (r/unixporn standard) |
| **Fabric** | Python | Yes | No | Yes | Small |
| **Plasmoid** | QML/JS | KDE only | KDE only | Yes | KDE community |

**Quickshell is the default** on Hyprland and KDE Wayland (best LLM ergonomics: QML matches Qt
training data, no Yuck DSL, hot-reload on save). **EWW is the fallback** for X11 and any session
without `wlr-layer-shell` support — it remains the broadest-compatibility option and is fully
supported by this pipeline.

---

## 13. Known Pitfalls

### General
- **EWW daemon must be running** before `eww open` — add to autostart before any `eww open` calls
- **SCSS not CSS** — EWW compiles SCSS internally; raw CSS syntax will fail silently or error
- **`exclusive: false`** means the widget doesn't reserve screen space — important for overlays, but windows will render behind/over it
- **Hot-reload**: `eww reload` picks up SCSS changes but NOT Yuck structural changes; for those: `eww kill && eww daemon`
- **GTK Layer Shell varies by compositor**: works great on Hyprland/Sway; on KDE Wayland may fight with Plasma panels; not available on X11 (falls back to GDK X11)
- **X11 stacking values differ** — on X.Org use `stacking: "fg"` (foreground) or `stacking: "bg"` (background). On Wayland (Hyprland/Sway) use `stacking: "overlay"`. Using `"overlay"` on X11 silently falls back but behavior is unpredictable — always match to the compositor.
- **Image paths in SCSS** must be absolute or relative to `~/.config/eww/` — relative to the SCSS file does NOT work
- **Large images** — use optimized PNGs; uncompressed 4K textures cause noticeable lag on lower-end GPUs

### Game-UI specific pitfalls
- **`image` widget width/height** — must be plain integers (`48`), NOT strings (`"48px"`). Passing a px string causes the image to silently not render while the widget box is still present.
- **`overlay` size** — the overlay takes the size of its **first child**. If you put a decorative image as the first child, the container will be that image's size. Always put a sized `box` first.
- **`progress` bar CSS** — to style the fill portion, you must target the sub-node: `.my-bar > trough > progress { }`. Targeting `.my-bar > progress` has no effect. Use `eww inspector` to verify node paths.
- **`progress` value** — the value is always 0–100. There is no `:min`/`:max` attribute. Compute the percentage yourself: `{round(hp / hp_max * 100, 0)}`.
- **`border-image` requires `border-width`** — GTK CSS will not render `border-image` if `border-width` is `0` or unset. Always set matching `border-width` and `border-style: solid; border-color: transparent;`.
- **No `clip-path`** — GTK CSS does not support `clip-path`. For non-rectangular panels, use alpha-channel PNGs as the background; transparent pixels will show through without blur.
- **No `@keyframes`** — looping CSS animations are not supported. Use `defpoll` to swap image paths or toggle CSS classes for animations.
- **`revealer` + `overlay` + `button` bug** — a clickable `button` inside a `revealer` that is itself inside an `overlay` may not receive mouse events. Workaround: restructure to avoid this triple-nesting; use separate `defwindow` for panels instead.
- **`for` loop re-renders** — every time the polled JSON changes, the entire `for` loop re-renders. Keep the poll interval reasonable (≥ 500ms) to avoid flicker on large grids.
- **`literal` performance** — `literal` re-parses and re-renders the entire Yuck tree on every change. Use `for` loops instead where possible; reserve `literal` for truly dynamic structures.
