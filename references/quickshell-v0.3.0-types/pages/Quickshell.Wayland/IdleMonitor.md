## IdleMonitor : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Wayland `
An idle monitor detects when the user stops providing input for a period of time.

NOTE

Using an idle monitor requires the compositor support the [ext-idle-notify-v1 ](https://wayland.app/protocols/ext-idle-notify-v1)protocol.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* respectInhibitors : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

When set to true, [isIdle ](#isIdle)will depend on both user interaction and active idle inhibitors. When false, the value will depend solely on user interaction. Defaults to true.

* timeout : [real ](https://doc.qt.io/qt-6/qml-real.html)

The amount of time in seconds the idle monitor should wait before reporting an idle state.

Defaults to zero, which reports idle status immediately.

* isIdle : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

This property is true if the user has been idle for at least [timeout ](#timeout). What is considered to be idle is influenced by [respectInhibitors ](#respectInhibitors).

* enabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the idle monitor should be enabled. Defaults to true.

* [respectInhibitors ](#respectInhibitors)

* [timeout ](#timeout)

* [isIdle ](#isIdle)

* [enabled ](#enabled)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
