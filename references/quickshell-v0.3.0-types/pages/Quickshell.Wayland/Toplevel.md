## Toplevel : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Wayland `
A window/toplevel from another application, retrievable from the [ToplevelManager ](/docs/v0.3.0/types/Quickshell.Wayland/ToplevelManager).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* maximized : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the window is currently maximized.

Maximization can be requested by setting this property, though it may be ignored by the compositor.

* minimized : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the window is currently minimized.

Minimization can be requested by setting this property, though it may be ignored by the compositor.

* appId : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

* fullscreen : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the window is currently fullscreen.

Fullscreen can be requested by setting this property, though it may be ignored by the compositor. Fullscreen can be requested on a specific screen with the [fullscreenOn() ](#fullscreenOn)function.

* activated : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the window is currently activated or focused.

Activation can be requested with the [activate() ](#activate)function.

* title : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

* parent : [Toplevel ](/docs/v0.3.0/types/Quickshell.Wayland/Toplevel)
readonly

Parent toplevel if this toplevel is a modal/dialog, otherwise null.

* screens : [list ](https://doc.qt.io/qt-6/qml-list.html)< [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)>
readonly

Screens the toplevel is currently visible on. Screens are listed in the order they have been added by the compositor.

NOTE

Some compositors only list a single screen, even if a window is visible on multiple.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* activate ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Request that this toplevel is activated. The request may be ignored by the compositor.

* close ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Request that this toplevel is closed. The request may be ignored by the compositor or the application.

* fullscreenOn ( screen ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

screen : [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)

Request that this toplevel is fullscreened on a specific screen. The request may be ignored by the compositor.

* setRectangle ( window, rect ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

window : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)rect : [rect ](https://doc.qt.io/qt-6/qml-rect.html)

Provide a hint to the compositor where the visual representation of this toplevel is relative to a quickshell window. This hint can be used visually in operations like minimization.

* unsetRectangle ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

No details provided

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* closed ( ) [](/docs/configuration/qml-overview#-signals)

No details provided

* [maximized ](#maximized)

* [minimized ](#minimized)

* [appId ](#appId)

* [fullscreen ](#fullscreen)

* [activated ](#activated)

* [title ](#title)

* [parent ](#parent)

* [screens ](#screens)

* [activate ](#activate)

* [close ](#close)

* [fullscreenOn ](#fullscreenOn)

* [setRectangle ](#setRectangle)

* [unsetRectangle ](#unsetRectangle)

* [closed ](#closed)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
