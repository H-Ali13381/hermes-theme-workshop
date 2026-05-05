## WindowsetProjection : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.WindowManager `
A WindowsetProjection represents a space that can be occupied by one or more [Windowset ](/docs/v0.3.0/types/Quickshell.WindowManager/Windowset)s. The space is one or more screens. Multiple projections may occupy the same screens.

[WindowManager.screenProjection() ](/docs/v0.3.0/types/Quickshell.WindowManager/WindowManager#screenProjection)can be used to get a projection representing all [Windowset ](/docs/v0.3.0/types/Quickshell.WindowManager/Windowset)s on a given screen regardless of the WM’s actual projection layout.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* windowsets : [list ](https://doc.qt.io/qt-6/qml-list.html)< [Windowset ](/docs/v0.3.0/types/Quickshell.WindowManager/Windowset)>
readonly

Windowsets that are currently present on the projection.

* screens : [list ](https://doc.qt.io/qt-6/qml-list.html)< [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)>
readonly

Screens the windowset projection spans, often a single screen or all screens.

* [windowsets ](#windowsets)

* [screens ](#screens)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
