## HyprlandWindow : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Hyprland `
Allows setting hyprland specific window properties on a [QsWindow ](/docs/v0.3.0/types/Quickshell/QsWindow)or subclass, as an attached object.

#### Example

```
`[PopupWindow](/docs/v0.3.0/types/Quickshell/PopupWindow) {
  // ...
  HyprlandWindow.opacity: 0.6 // any number or binding
}`
```

NOTE

Requires at least hyprland 0.47.0, or [hyprland-surface-v1 ](https://github.com/hyprwm/hyprland-protocols/blob/main/protocols/hyprland-surface-v1.xml)support.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* opacity : [real ](https://doc.qt.io/qt-6/qml-real.html)

A multiplier for the window’s overall opacity, ranging from 1.0 to 0.0. Overall opacity includes the opacity of both the window content and visual effects such as blur that apply to it.

Default: 1.0

* visibleMask : [Region ](/docs/v0.3.0/types/Quickshell/Region)

A hint to the compositor that only certain regions of the surface should be rendered. This can be used to avoid rendering large empty regions of a window which can increase performance, especially if the window is blurred. The mask should include all pixels of the window that do not have an alpha value of 0.

* [opacity ](#opacity)

* [visibleMask ](#visibleMask)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
