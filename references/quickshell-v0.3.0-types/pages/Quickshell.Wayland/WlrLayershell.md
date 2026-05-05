## WlrLayershell : [PanelWindow ](/docs/v0.3.0/types/Quickshell/PanelWindow)

`import Quickshell.Wayland `
Decorationless window that can be attached to the screen edges using the [zwlr_layer_shell_v1 ](https://wayland.app/protocols/wlr-layer-shell-unstable-v1)protocol.

#### Attached object

`WlrLayershell `works as an attached object of [PanelWindow ](/docs/v0.3.0/types/Quickshell/PanelWindow)which you should use instead if you can, as it is platform independent.

```
`PanelWindow {
  // When PanelWindow is backed with WlrLayershell this will work
  WlrLayershell.layer: WlrLayer.Bottom
}`
```

To maintain platform compatibility you can dynamically set layershell specific properties.

```
`PanelWindow {
  Component.onCompleted: {
    if (this.WlrLayershell != null) {
      this.WlrLayershell.layer = WlrLayer.Bottom;
    }
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* keyboardFocus : [WlrKeyboardFocus ](/docs/v0.3.0/types/Quickshell.Wayland/WlrKeyboardFocus)

The degree of keyboard focus taken. Defaults to `KeyboardFocus.None `.

* layer : [WlrLayer ](/docs/v0.3.0/types/Quickshell.Wayland/WlrLayer)

The shell layer the window sits in. Defaults to `WlrLayer.Top `.

* namespace : [string ](https://doc.qt.io/qt-6/qml-string.html)

Similar to the class property of windows. Can be used to identify the window to external tools.

Cannot be set after windowConnected.

* [keyboardFocus ](#keyboardFocus)

* [layer ](#layer)

* [namespace ](#namespace)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
