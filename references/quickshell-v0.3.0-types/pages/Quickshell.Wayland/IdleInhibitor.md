## IdleInhibitor : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Wayland `
If an idle daemon is running, it may perform actions such as locking the screen or putting the computer to sleep.

An idle inhibitor prevents a wayland session from being marked as idle, if compositor defined heuristics determine the window the inhibitor is attached to is important.

A compositor will usually consider a [PanelWindow ](/docs/v0.3.0/types/Quickshell/PanelWindow)or a focused [FloatingWindow ](/docs/v0.3.0/types/Quickshell/FloatingWindow)to be important.

NOTE

Using an idle inhibitor requires the compositor support the [idle-inhibit-unstable-v1 ](https://wayland.app/protocols/idle-inhibit-unstable-v1)protocol.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* window : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

The window to associate the idle inhibitor with. This may be used by the compositor to determine if the inhibitor should be respected.

Must be set to a non null value to enable the inhibitor.

* enabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the idle inhibitor should be enabled. Defaults to false.

* [window ](#window)

* [enabled ](#enabled)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
