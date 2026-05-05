## PanelWindow : [QsWindow ](/docs/v0.3.0/types/Quickshell/QsWindow)

`import Quickshell `
Decorationless window attached to screen edges by anchors.

#### Example

The following snippet creates a white bar attached to the bottom of the screen.

```
`PanelWindow {
  anchors {
    left: true
    bottom: true
    right: true
  }

  Text {
    anchors.centerIn: parent
    text: "Hello!"
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* focusable : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the panel should accept keyboard focus. Defaults to false.

Note: On Wayland this property corresponds to [WlrLayershell.keyboardFocus ](/docs/v0.3.0/types/Quickshell.Wayland/WlrLayershell#keyboardFocus).

* margins : [[right,top,left,bottom] ](#)

right: [int ](https://doc.qt.io/qt-6/qml-int.html)top: [int ](https://doc.qt.io/qt-6/qml-int.html)left: [int ](https://doc.qt.io/qt-6/qml-int.html)bottom: [int ](https://doc.qt.io/qt-6/qml-int.html)

Offsets from the sides of the screen.

NOTE

Only applies to edges with anchors

* anchors : [[bottom,top,right,left] ](#)

bottom: [bool ](https://doc.qt.io/qt-6/qml-bool.html)top: [bool ](https://doc.qt.io/qt-6/qml-bool.html)right: [bool ](https://doc.qt.io/qt-6/qml-bool.html)left: [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Anchors attach a shell window to the sides of the screen. By default all anchors are disabled to avoid blocking the entire screen due to a misconfiguration.

NOTE

When two opposite anchors are attached at the same time, the corresponding dimension (width or height) will be forced to equal the screen width/height. Margins can be used to create anchored windows that are also disconnected from the monitor sides.

* exclusiveZone : [int ](https://doc.qt.io/qt-6/qml-int.html)

The amount of space reserved for the shell layer relative to its anchors. Setting this property sets [exclusionMode ](#exclusionMode)to `ExclusionMode.Normal `.

NOTE

Either 1 or 3 anchors are required for the zone to take effect.

* aboveWindows : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the panel should render above standard windows. Defaults to true.

Note: On Wayland this property corresponds to [WlrLayershell.layer ](/docs/v0.3.0/types/Quickshell.Wayland/WlrLayershell#layer).

* exclusionMode : [ExclusionMode ](/docs/v0.3.0/types/Quickshell/ExclusionMode)

Defaults to `ExclusionMode.Auto `.

* [focusable ](#focusable)

* [margins ](#margins)

* [anchors ](#anchors)

* [exclusiveZone ](#exclusiveZone)

* [aboveWindows ](#aboveWindows)

* [exclusionMode ](#exclusionMode)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
