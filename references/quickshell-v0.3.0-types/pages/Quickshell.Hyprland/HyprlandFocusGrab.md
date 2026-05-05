## HyprlandFocusGrab : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Hyprland `
Object for managing input focus grabs via the [hyprland_focus_grab_v1 ](https://github.com/hyprwm/hyprland-protocols/blob/main/protocols/hyprland-global-shortcuts-v1.xml)wayland protocol.

When enabled, all of the windows listed in the `windows `property will receive input normally, and will retain keyboard focus even if the mouse is moved off of them. When areas of the screen that are not part of a listed window are clicked or touched, the grab will become inactive and emit the cleared signal.

This is useful for implementing dismissal of popup type windows.

```
`import Quickshell
import Quickshell.Hyprland
import QtQuick.Controls

ShellRoot {
  FloatingWindow {
    id: window

    Button {
      anchors.centerIn: parent
      text: grab.active ? "Remove exclusive focus" : "Take exclusive focus"
      onClicked: grab.active = !grab.active
    }

    HyprlandFocusGrab {
      id: grab
      windows: [ window ]
    }
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the focus grab is active. Defaults to false.

When set to true, an input grab will be created for the listed windows.

This property will change to false once the grab is dismissed. It will not change to true until the grab begins, which requires at least one visible window.

* windows : [list ](https://doc.qt.io/qt-6/qml-list.html)< [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)>

The list of windows to whitelist for input.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* cleared ( ) [](/docs/configuration/qml-overview#-signals)

Sent whenever the compositor clears the focus grab.

This may be in response to all windows being removed from the list or simultaneously hidden, in addition to a normal clear.

* [active ](#active)

* [windows ](#windows)

* [cleared ](#cleared)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
