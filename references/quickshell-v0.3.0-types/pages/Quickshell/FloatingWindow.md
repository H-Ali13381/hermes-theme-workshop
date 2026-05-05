## FloatingWindow : [QsWindow ](/docs/v0.3.0/types/Quickshell/QsWindow)

`import Quickshell `
Standard toplevel operating system window that looks like any other application.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* maximized : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Whether the window is currently maximized.

* maximumSize : [size ](https://doc.qt.io/qt-6/qml-size.html)

Maximum window size given to the window system.

* fullscreen : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Whether the window is currently fullscreen.

* parentWindow : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

The parent window of this window. Setting this makes the window a child of the parent, which affects window stacking behavior.

NOTE

This property cannot be changed after the window is visible.

* minimized : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Whether the window is currently minimized.

* minimumSize : [size ](https://doc.qt.io/qt-6/qml-size.html)

Minimum window size given to the window system.

* title : [string ](https://doc.qt.io/qt-6/qml-string.html)

Window title.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* startSystemMove ( ) : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Start a system move operation. Must be called during a pointer press/drag.

* startSystemResize ( edges ) : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

edges : [](#unknown)

Start a system resize operation. Must be called during a pointer press/drag.

* [maximized ](#maximized)

* [maximumSize ](#maximumSize)

* [fullscreen ](#fullscreen)

* [parentWindow ](#parentWindow)

* [minimized ](#minimized)

* [minimumSize ](#minimumSize)

* [title ](#title)

* [startSystemMove ](#startSystemMove)

* [startSystemResize ](#startSystemResize)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
