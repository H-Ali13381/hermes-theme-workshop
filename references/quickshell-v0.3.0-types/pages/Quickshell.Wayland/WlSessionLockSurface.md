## WlSessionLockSurface : [Reloadable ](/docs/v0.3.0/types/Quickshell/Reloadable)

`import Quickshell.Wayland `
Surface displayed by a [WlSessionLock ](/docs/v0.3.0/types/Quickshell.Wayland/WlSessionLock)when it is locked.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* visible : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the surface has been made visible.

Note: SessionLockSurfaces will never become invisible, they will only be destroyed.

* color : [color ](https://doc.qt.io/qt-6/qml-color.html)

The background color of the window. Defaults to white.

WARNING

This seems to behave weirdly when using transparent colors on some systems. Using a colored content item over a transparent window is the recommended way to work around this:

```
`ProxyWindow {
  Rectangle {
    anchors.fill: parent
    color: "#20ffffff"

    // your content here
  }
}`
```

… but you probably shouldn’t make a transparent lock, and most compositors will ignore an attempt to do so.

* height : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

No details provided

* data : [list ](https://doc.qt.io/qt-6/qml-list.html)< [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)>
default readonly

No details provided

* contentItem : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)
readonly

No details provided

* screen : [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)
readonly

The screen that the surface is displayed on.

* width : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

No details provided

* [visible ](#visible)

* [color ](#color)

* [height ](#height)

* [data ](#data)

* [contentItem ](#contentItem)

* [screen ](#screen)

* [width ](#width)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
