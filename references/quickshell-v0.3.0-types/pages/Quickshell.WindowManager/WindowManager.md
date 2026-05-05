## WindowManager : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
singleton

`import Quickshell.WindowManager `
Window management interfaces exposed by the window manager.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* windowsetProjections : [list ](https://doc.qt.io/qt-6/qml-list.html)< [WindowsetProjection ](/docs/v0.3.0/types/Quickshell.WindowManager/WindowsetProjection)>
readonly

All windowset projections tracked by the WM. Does not include internal projections from [screenProjection() ](#screenProjection).

* windowsets : [list ](https://doc.qt.io/qt-6/qml-list.html)< [Windowset ](/docs/v0.3.0/types/Quickshell.WindowManager/Windowset)>
readonly

All windowsets tracked by the WM across all projections.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* screenProjection ( screen ) : [ScreenProjection ](/docs/v0.3.0/types/Quickshell.WindowManager/ScreenProjection)

screen : [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)

Returns an internal WindowsetProjection that covers a single screen and contains all windowsets on that screen, regardless of the WM-specified projection. Depending on how the WM lays out its actual projections, multiple ScreenProjections may contain the same Windowsets.

* [windowsetProjections ](#windowsetProjections)

* [windowsets ](#windowsets)

* [screenProjection ](#screenProjection)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
