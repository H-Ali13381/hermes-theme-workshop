# KDE Plasma — Custom Widgets (EWW & Plasmoids)

> For EWW basics, the AI→widget pipeline, image slicing, and hover patterns, see [`shared/widgets.md`](../shared/widgets.md).

This document covers KDE-specific widget configuration — both EWW on KDE and native Plasmoid alternatives.

---

## 1. EWW on KDE Wayland

EWW works on KDE Wayland via GTK Layer Shell. Key considerations:

### Panel edge conflicts
EWW windows anchored to the same edge as a Plasma panel will compete for space:
- If both use exclusive zone, windows get pushed twice (double gap)
- If EWW uses `exclusive: false`, it renders behind/over the Plasma panel

**Solutions:**
- Anchor EWW to a different edge than Plasma panels
- Hide the Plasma panel (see §4 below)
- Use `exclusive: false` and ensure EWW stacking is `"overlay"` to render above

### exclusive_zone interaction
```lisp
(defwindow kde-eww-bar
  :monitor 0
  :geometry (geometry :x "0%" :y "0px" :width "100%" :height "48px" :anchor "bottom center")
  :stacking "overlay"
  :exclusive false    ;; don't fight with Plasma panel's space reservation
  :focusable false
  :namespace "eww-bar-kde"
  (bar-content))
```

### Blur
KDE Wayland does support GTK Layer Shell blur requests, but behavior may vary by KDE Plasma version. Test with a simple translucent background first before adding blur layer rules.

---

## 2. EWW on KDE X11

EWW uses the GDK X11 backend on X11 sessions. Layer shell is NOT available.

### Window management
Since there's no layer-shell protocol on X11, EWW windows are regular X11 windows. Use `wmctrl` for z-ordering:

```bash
# Make EWW window sticky (visible on all desktops) and always-on-top
wmctrl -r 'eww' -b add,sticky,above

# Make it appear below other windows (desktop widget style)
wmctrl -r 'eww' -b add,sticky,below
```

### Limitations on X11
- No reliable `exclusive_zone` — other windows won't avoid the EWW bar
- Z-ordering depends on KWin's window rules and may be unreliable
- No blur support through EWW (KWin blur is controlled separately)
- Consider using KWin window rules for specific EWW windows:
  ```bash
  # Via kwriteconfig6 or System Settings → Window Rules
  # Match by window title containing "eww"
  ```

### Recommendation
For KDE X11, EWW works for **desktop overlay widgets** (clocks, system monitors, sidebars) but is less reliable for **panel replacements**. Use the native Plasma panel on X11.

---

## 3. Native Alternative: Custom Plasmoids (QML)

Plasmoids are KDE's native widget format — deeply integrated with Plasma but harder to auto-generate.

### Overview
- Written in **QML + JavaScript**
- Full access to KDE/Plasma APIs
- Support auto-hide via Plasma panel containment settings
- Consistent theming with KDE's color scheme

### Package structure
```
my-plasmoid/
├── metadata.json              ← plugin metadata (name, version, API)
└── contents/
    └── ui/
        └── main.qml           ← widget UI and logic
```

### Image textures in QML
```qml
import QtQuick 2.15

Item {
    width: 200; height: 80

    Image {
        anchors.fill: parent
        source: "images/widget-bg.png"
        fillMode: Image.Stretch
    }

    Text {
        anchors.centerIn: parent
        text: "12:34"
        color: "#e4f0ff"
        font.pixelSize: 28
    }
}
```

### Why NOT recommended for the AI pipeline
- QML is complex to generate reliably — layout engine is imperative + declarative mix
- Error handling is poor (silent failures, cryptic QML warnings)
- Testing requires Plasma running — can't preview standalone easily
- EWW + SCSS is much simpler to template and auto-generate
- **Verdict:** Use Plasmoids only when the user specifically wants deep KDE integration

---

## 4. Coexistence with Plasma Panel

### Running EWW alongside Plasma
EWW can serve as **supplementary widgets** while keeping KDE's panel:
- Desktop overlay stats (CPU, RAM, disk usage)
- Floating music player widget
- Corner clock with custom texture
- Side panel with quick actions

### Hiding the Plasma panel
To replace the Plasma panel with EWW:

```bash
# Set all Plasma panels to auto-hide
qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript \
  'panels().forEach(p => p.hiding = "autohide")'

# To fully hide (Windows-can-cover mode):
qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript \
  'panels().forEach(p => p.hiding = "windowscancover")'

# To restore normal visibility:
qdbus6 org.kde.plasmashell /PlasmaShell evaluateScript \
  'panels().forEach(p => p.hiding = "none")'
```

### Recommended approach for KDE
1. Keep the Plasma panel for system tray (network, bluetooth, battery notifications)
2. Use EWW for **custom decorative widgets** that Plasma panels can't do:
   - Textured bars with game/anime aesthetics
   - Shaped widgets (non-rectangular)
   - Image-heavy UI elements from the AI pipeline
3. Position EWW widgets on edges or corners not occupied by Plasma panels
