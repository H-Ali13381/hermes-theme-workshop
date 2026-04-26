# Hyprland — Custom Widgets (EWW)

> For EWW basics, the AI→widget pipeline, image slicing, and hover patterns, see [`shared/widgets.md`](../shared/widgets.md).

This document covers Hyprland-specific EWW widget configuration.

---

## 1. Layer Rules

Hyprland layer rules control how EWW windows animate, blur, and render. Add these to `hyprland.conf`:

```ini
# Trigger bars: no animation (instant show/hide)
layerrule = noanim, eww-trigger-*

# Main bars: slide in from the anchored edge
layerrule = animation slide top, eww-bar-*

# Apply blur behind the bar (requires Hyprland blur enabled)
layerrule = blur, eww-bar-*

# Don't blur fully transparent pixels (important for non-rectangular shapes)
layerrule = ignorezero, eww-bar-*
```

| Rule | Effect |
|------|--------|
| `noanim` | Disables open/close animation — essential for trigger zones that should be invisible |
| `animation slide top` | Bar slides in from the top edge; change `top` to match your anchor |
| `blur` | Applies Hyprland's background blur to the window — requires `decoration:blur` enabled |
| `ignorezero` | Transparent pixels (alpha=0) are excluded from blur — prevents blur halo around shaped widgets |

**Namespace matching:** The `eww-trigger-*` and `eww-bar-*` patterns match the `namespace` attribute in your EWW `defwindow`. Set `:namespace "eww-trigger-bar"` in Yuck to match.

---

## 2. Autostart

Add to `hyprland.conf`:
```ini
# Start EWW daemon and open the trigger bar
exec-once = eww daemon && eww open trigger-bar
```

### Order considerations
- If **coexisting with waybar**: start EWW after waybar to avoid exclusive_zone conflicts
  ```ini
  exec-once = waybar
  exec-once = sleep 1 && eww daemon && eww open trigger-bar
  ```
- If **replacing waybar**: remove/comment out the waybar exec-once line entirely

---

## 3. Workspace Integration

### Live workspace listener
Use `socat` to listen for Hyprland IPC events and `hyprctl` to query state:

```lisp
(deflisten workspaces
  "scripts/get-workspaces.sh")

(defwidget workspace-module []
  (box :class "workspaces" :orientation "h" :spacing 4
    (for ws in workspaces
      (button
        :class {ws.active ? "ws-active" : "ws-inactive"}
        :onclick "hyprctl dispatch workspace ${ws.id}"
        "${ws.id}"))))
```

**scripts/get-workspaces.sh:**
```bash
#!/bin/bash
# Outputs JSON array of workspaces on every change
get_workspaces() {
  active=$(hyprctl activeworkspace -j | jq '.id')
  hyprctl workspaces -j | jq -c --argjson active "$active" \
    '[.[] | {id: .id, name: .name, active: (.id == $active)}] | sort_by(.id)'
}

# Initial state
get_workspaces

# Listen for changes
socat -U - UNIX-CONNECT:"$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock" | while read -r line; do
  case $line in
    workspace*|createworkspace*|destroyworkspace*|moveworkspace*)
      get_workspaces
      ;;
  esac
done
```

### Active window title
```lisp
(deflisten active-window
  "scripts/get-active-window.sh")

;; scripts/get-active-window.sh:
;; hyprctl activewindow -j | jq -r '.title // "Desktop"'
;; socat ... | while read; do hyprctl activewindow -j | jq -r '.title // "Desktop"'; done
```

---

## 4. Replacing Waybar

To fully replace waybar with a custom EWW bar:

1. **Remove waybar autostart** from `hyprland.conf`:
   ```ini
   # exec-once = waybar   ← comment out or delete
   ```

2. **Set exclusive_zone** on your EWW bar to push windows down:
   ```lisp
   (defwindow main-bar
     :monitor 0
     :geometry (geometry :x "0%" :y "0px" :width "100%" :height "40px" :anchor "top center")
     :stacking "overlay"
     :exclusive true          ;; ← reserves screen space like waybar does
     :focusable false
     :namespace "eww-bar-main"
     (bar-content))
   ```

3. **Autostart the EWW bar**:
   ```ini
   exec-once = eww daemon && eww open main-bar
   ```

4. **Verify**: windows should not overlap the bar region when `:exclusive true` is set.

---

## 5. Multi-Monitor

### Per-monitor windows
Use the `:monitor` attribute in `defwindow`:
```lisp
(defwindow bar-monitor-0
  :monitor 0
  :geometry (geometry :x "0%" :y "0px" :width "100%" :height "40px" :anchor "top center")
  :exclusive true
  (bar-content))

(defwindow bar-monitor-1
  :monitor 1
  :geometry (geometry :x "0%" :y "0px" :width "100%" :height "40px" :anchor "top center")
  :exclusive true
  (bar-content))
```

### Detecting monitors
```bash
# List monitors as JSON
hyprctl monitors -j | jq '.[].name'

# Open bar on all monitors dynamically
for monitor in $(hyprctl monitors -j | jq -r '.[].id'); do
  eww open "bar-monitor-$monitor"
done
```

### Dynamic monitor script
```bash
#!/bin/bash
# scripts/open-bars.sh — open a bar on each connected monitor
eww daemon 2>/dev/null
monitor_count=$(hyprctl monitors -j | jq 'length')
for ((i=0; i<monitor_count; i++)); do
  eww open "bar-monitor-$i" 2>/dev/null
done
```

Autostart: `exec-once = ~/.config/eww/scripts/open-bars.sh`
