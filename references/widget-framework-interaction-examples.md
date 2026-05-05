# Widget Framework Interaction Examples

Use this reference when building Step 6 custom widgets/dashboards with Quickshell, EWW, AGS, or Fabric. It records research gathered after a failed Quickshell widget replay where action hitboxes were misaligned, only the power button produced a visible result, workspace controls looked inert, and the power control opened KRunner search instead of a real menu.

## Framework mapping: same game-UI contract, different runtime

The desired architecture is the same logic a C++ game UI system would use, but emitted into the selected Linux widget runtime:

| Game UI concept | Quickshell | EWW | AGS | Fabric |
|---|---|---|---|---|
| Root HUD/layer | `PanelWindow` / `PopupWindow` | `defwindow` | `Widget.Window` | `WaylandWindow` |
| Component tree | nested `Item` / reusable `.qml` components | nested widgets / `defwidget` | JS/TS widget functions/classes | Python widget objects/classes |
| Button primitive | `MouseArea` / `TapHandler` around `GameButton` | `(button)` or `(eventbox)` + SCSS | `Widget.Button` | `Button` / `EventBox` |
| State machine | QML `states`, properties, bindings | class toggles + `:hover` / `:active` | JS state/services/signals | Python state + CSS classes |
| 9-slice frame | `BorderImage` | CSS border images / background slices where possible | GTK/CSS image assets | GTK/CSS image assets |
| Data binding | QML `Timer`, services, `Process` | `defpoll`, `deflisten`, variables | services/signals | Python callbacks/services |
| Popup/menu | `PopupWindow` / visible child surface | extra `defwindow` / revealer pattern | popup window pattern | overlay/window stack |
| Dispatch | argv arrays / `execDetached` / safe `Process` | curated commands/callback scripts | JS callbacks/services | Python callbacks/subprocess argv |

Adapters must lower the same framework-neutral component model into their native primitives. They must not paste preview crops as final widgets, redefine hover/pressed as invisible cursor-only regions, or turn internal state transitions such as `open_power_menu` into shell commands.

## Root-cause lessons from the failed replay

- The generated preview-texture QML emitted `MouseArea` overlays, but those overlays had no visible hover/pressed state, so the user could not tell what was clickable.
- Workspace buttons logged clicks, but the KDE session only had one virtual desktop. Commands like `qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 4` are no-ops unless the target desktop exists. Functional validation must check action preconditions, not just command presence.
- The power action used `qdbus6 org.kde.krunner /App org.kde.krunner.App.query power`, which opens a search bar. That is not an acceptable power menu implementation for the RPG dashboard workflow.
- Hitboxes were estimated from a contract crop with generic fractions. They must instead come from segmented per-control `action_regions`, with debug overlays and overlap scoring against visible button art.
- Same-artifact validation must test the exact QML artifact that is visually inspected. Do not validate an invisible surrogate while visually approving a copied preview texture.
- Preview-texture mode can now score highly by copying target crops into QML `Image` nodes and overlaying controls; this proves plumbing, not product quality. It must stay a labelled upper-bound test and be blocked from promotion.
- Good feel requires a component tree with real button/menu/meter components, state-specific visual layers, data bindings, and callbacks in Quickshell/EWW/AGS/Fabric — the same design logic as a game UI, just lowered into shell-widget runtimes.

## Gold-standard interaction contract

Every non-decorative control must define these fields before framework codegen:

```yaml
id: workspace-1
role: button
label: Workspace 1
visual_bbox: [x, y, w, h]          # visible control art in the local widget crop
interactive_bbox: [x, y, w, h]     # actual click/hover region; must overlap visual_bbox
min_hitbox: [32, 32]
cursor: pointer
states:
  normal: { brightness: 1.0, inset_px: 0, border: muted-gold }
  hover: { brightness: 1.12, glow: warm-gold, scale: 1.03 }
  pressed: { brightness: 0.82, inset_px: 2, scale: 0.96 }
  focus: { outline: thin-gold }
  disabled: { opacity: 0.45 }
action:
  type: compositor_dispatch | command | state_toggle | open_panel | close_panel | service_call
  argv: [qdbus6, org.kde.KWin, /KWin, org.kde.KWin.setCurrentDesktop, "1"]
  precondition: kde_virtual_desktop_count >= 1
  expected_effect: currentDesktop becomes 1
```

A control fails validation when it has an action but no hover/pressed visual state, or it has hover styling but no real action.

## Quickshell references

### Sources

- Official Quickshell docs: PanelWindow, PopupWindow, Process, Quickshell.execDetached, DesktopEntry, QsMenuAnchor, SystemTrayItem: https://quickshell.org/docs/v0.3.0/
- Qt MouseArea docs: https://doc.qt.io/qt-6/qml-qtquick-mousearea.html
- Qt TapHandler docs: https://doc.qt.io/qt-6/qml-qtquick-taphandler.html
- Rivendell Hyprdots by zacoons: https://codeberg.org/zacoons/rivendell-hyprdots
- Rivendell commit inspected: `2a8e15576f367e36630f6ff71e0f945c8e8c00e1`
- Rivendell custom image-border plugin: https://codeberg.org/zacoons/imgborders

### Rivendell patterns worth copying

Relevant repo paths:

- `.config/quickshell/bar/BarButton.qml`: reusable button wrapper. Pressed darkens; hover brightens; pressed state adds margins so content appears physically inset.
- `.config/quickshell/bar/ClickableIcon.qml`: icon wrapper with hover scale animation.
- `.config/quickshell/bar/Launcher.qml`: open-state scale and glow.
- `.config/quickshell/bar/Workspaces.qml`: per-workspace click regions and active-state glow.
- `.config/quickshell/bar/Volume.qml`: PopupWindow slider with thick carved track and diamond handle.
- `.config/quickshell/bar/mpris/PlayersPopup.qml`: hanging wooden panel with rope physics.
- `.config/quickshell/components/Rope.qml`: Verlet-style decorative rope component.
- `.config/quickshell/notifs/Notif.qml`: draggable/flingable physical notification cards.
- `.config/quickshell/screenshot/Overlay.qml`: rope-bound selection rectangle.
- `.config/quickshell/lock/Surface.qml`: lock screen as animated chest.
- `.config/hypr/style.conf`: uses `imgborders` with 9-slice image borders.

Lessons:

- Game UI feel comes from layers, tiny reusable assets, masks, nearest-neighbor art, physical motion, and shared button wrappers — not palette swaps.
- Buttons need at least three visual states: hover brighten/glow, pressed inset/shrink, disabled opacity.
- System meters can look diegetic by using custom masks: battery as vial, workspaces as rune slots, volume as carved slider.
- For generated desktops, parameterize asset paths. Rivendell hardcodes `/home/zac/...`; linux-ricing generated configs must use sandbox-local or install-root-relative paths.

### Minimal Quickshell clicky button

```qml
// GameButton.qml
import QtQuick

Rectangle {
  id: button
  property string label: "Button"
  signal clicked()

  implicitWidth: Math.max(150, text.implicitWidth + 36)
  implicitHeight: 42
  radius: 8

  color: mouse.containsPress ? "#3b235f"
       : mouse.containsMouse ? "#4c35a3"
       : "#201832"
  border.color: mouse.containsPress ? "#fff2a8"
              : mouse.containsMouse ? "#ffd75e"
              : "#7b5cff"
  border.width: mouse.containsMouse ? 2 : 1
  scale: mouse.containsPress ? 0.97 : mouse.containsMouse ? 1.03 : 1.0

  Behavior on color { ColorAnimation { duration: 90 } }
  Behavior on border.color { ColorAnimation { duration: 90 } }
  Behavior on scale { NumberAnimation { duration: 80; easing.type: Easing.OutQuad } }

  Text {
    id: text
    anchors.centerIn: parent
    text: button.label
    color: mouse.containsPress ? "#fff7cf" : "#f0eaff"
    font.pixelSize: 15
    font.bold: mouse.containsMouse
  }

  MouseArea {
    id: mouse
    anchors.fill: parent
    hoverEnabled: true
    cursorShape: Qt.PointingHandCursor
    acceptedButtons: Qt.LeftButton
    onClicked: button.clicked()
  }
}
```

### Quickshell command execution rules

Quickshell `Process.command` and `Quickshell.execDetached` take argv arrays. Generated code must prefer argv arrays over shell strings.

Good:

```qml
Quickshell.execDetached(["qdbus6", "org.kde.KWin", "/KWin", "org.kde.KWin.setCurrentDesktop", "1"])
```

Bad:

```qml
command: ["qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 1"]
command: ["sh", "-c", generatedUserText]
```

Only use `sh -lc` for curated, static commands that cannot be represented safely as argv; generated/user-controlled commands must not enter the shell.

### Quickshell power menu rule

A power glyph should toggle a custom menu or confirmation surface. It must not open KRunner search for `power`.

A safe scaffold is:

```qml
property bool powerOpen: false

GameButton {
  label: "Power"
  onClicked: powerOpen = !powerOpen
}

PopupWindow {
  visible: powerOpen
  grabFocus: true
  // child contains Lock, Suspend, Reboot, Power Off rows.
  // destructive rows require a confirm step before command execution.
}
```

## EWW references

Sources:

- Official EWW repo: https://github.com/elkowar/eww
- adi1090x widgets: https://github.com/adi1090x/widgets
- gh0stzk dotfiles: https://github.com/gh0stzk/dotfiles

Patterns:

- Use native `(button :onclick "...")` for true buttons.
- Use `(eventbox :cursor "pointer" ...)` around custom art/hitboxes.
- EWW eventbox supports CSS `:hover` and `:active`; generated widgets must define both.
- Window geometry is separate from widget content via `defwindow :geometry`; do not infer hitbox geometry from the window surface.

Example:

```lisp
(defwidget closebtn []
  (eventbox :cursor "pointer"
    (button :class "game-button" :onclick "eww open --toggle launcher" "Quest Log")))
```

```scss
.game-button {
  border: 1px solid $gold;
  background: $dark-panel;
  transition: all 90ms ease;
}
.game-button:hover {
  background: lighten($dark-panel, 8%);
  box-shadow: 0 0 8px rgba($gold, .45);
}
.game-button:active {
  background: darken($dark-panel, 8%);
  transform: translateY(2px);
}
```

## AGS references

Sources:

- AGS v1 repo: https://github.com/Aylur/ags/tree/v1
- Aylur pre-Astal dotfiles: https://github.com/Aylur/dotfiles/tree/pre-astal

Patterns:

- `Widget.Button({ on_clicked, on_hover, on_hover_lost })` maps cleanly to control contracts.
- Layer-shell windows expose `layer`, `anchor`, `exclusivity`, and `keymode`.
- Aylur's PopupWindow pattern uses a full-screen surface plus transparent EventBox padding regions for click-away dismissal.
- Power/session menu is separate from verification popup; destructive intent is not immediate execution.

Contract fields to preserve for AGS:

```ts
Widget.Window({
  name,
  layer: "top",
  anchor: ["top", "bottom", "right", "left"],
  keymode: "on-demand",
  child: Layout(name, child),
})
```

## Fabric references

Sources:

- Fabric: https://github.com/Fabric-Development/fabric
- Ax-Shell: https://github.com/Axenide/Ax-Shell

Patterns:

- `Button(on_clicked=lambda *_: ...)` is the default true-control primitive.
- `EventBox(events=..., on_button_press_event=...)` is used for custom hitboxes.
- `WaylandWindow(layer=..., anchor=..., margin=..., exclusivity=..., keyboard_mode=...)` maps to shell geometry.
- Ax-Shell has strong examples of pointer cursors, minimum hitbox sizes, hover/focus/active CSS transitions, dashboard stack navigation, and close-after-action behavior.

Example CSS:

```css
#power-menu-button {
  min-width: 52px;
  min-height: 52px;
  border-radius: 40px;
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
#power-menu-button:hover,
#power-menu-button:focus {
  border-radius: 20px;
  background-color: var(--surface-bright);
}
#power-menu-button:active {
  transform: translateY(2px) scale(0.96);
}
```

## Validation checklist

Before promoting a widget to the real desktop:

1. Segmentation produced one `action_region` per visible control.
2. Each action region has visual and interactive bboxes with sufficient overlap.
3. Hover and pressed states are visible in the same generated artifact.
4. Command actions are argv arrays or framework-native callbacks, not raw generated shell strings.
5. The current desktop environment supports every command target. For KDE workspaces, check `/VirtualDesktopManager count` before declaring workspace buttons functional.
6. Power glyph opens a custom power menu/confirmation, never KRunner search.
7. Destructive power/session actions require a confirm step.
8. Visual validation, action validation, and manual review use the same artifact path and SHA-256.
