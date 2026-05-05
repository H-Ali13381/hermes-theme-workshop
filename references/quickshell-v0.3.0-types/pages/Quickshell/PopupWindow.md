## PopupWindow : [QsWindow ](/docs/v0.3.0/types/Quickshell/QsWindow)

`import Quickshell `
Popup window that can display in a position relative to a floating or panel window.

#### Example

The following snippet creates a panel with a popup centered over it.

```
`PanelWindow {
  id: toplevel

  anchors {
    bottom: true
    left: true
    right: true
  }

  PopupWindow {
    anchor.window: toplevel
    anchor.rect.x: parentWindow.width / 2 - width / 2
    anchor.rect.y: parentWindow.height
    width: 500
    height: 500
    visible: true
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* parentWindow : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

[!ERROR] Deprecated in favor of `anchor.window `.

The parent window of this popup.

Changing this property reparents the popup.

* relativeY : [int ](https://doc.qt.io/qt-6/qml-int.html)

[!ERROR] Deprecated in favor of `anchor.rect.y `.

The Y position of the popup relative to the parent window.

* screen : [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)
readonly

The screen that the window currently occupies.

This may be modified to move the window to the given screen.

* visible : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the window is shown or hidden. Defaults to false.

The popup will not be shown until [anchor ](#anchor)is valid, regardless of this property.

* grabFocus : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If true, the popup window will be dismissed and [visible ](#visible)will change to false if the user clicks outside of the popup or it is otherwise closed.

WARNING

Changes to this property while the window is open will only take effect after the window is hidden and shown again.

NOTE

Under Hyprland, [HyprlandFocusGrab ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandFocusGrab)provides more advanced functionality such as detecting clicks outside without closing the popup.

* relativeX : [int ](https://doc.qt.io/qt-6/qml-int.html)

[!ERROR] Deprecated in favor of `anchor.rect.x `.

The X position of the popup relative to the parent window.

* anchor : [PopupAnchor ](/docs/v0.3.0/types/Quickshell/PopupAnchor)
readonly

The popup’s anchor / positioner relative to another item or window. The popup will not be shown until it has a valid anchor relative to a window and [visible ](#visible)is true.

You can set properties of the anchor like so:

```
`PopupWindow {
  anchor.window: parentwindow
  // or
  anchor {
    window: parentwindow
  }
}`
```

* [parentWindow ](#parentWindow)

* [relativeY ](#relativeY)

* [screen ](#screen)

* [visible ](#visible)

* [grabFocus ](#grabFocus)

* [relativeX ](#relativeX)

* [anchor ](#anchor)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
