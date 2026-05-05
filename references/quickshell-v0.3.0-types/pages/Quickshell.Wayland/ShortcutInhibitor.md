## ShortcutInhibitor : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Wayland `
A shortcuts inhibitor prevents the compositor from processing its own keyboard shortcuts for the focused surface. This allows applications to receive key events for shortcuts that would normally be handled by the compositor.

The inhibitor only takes effect when the associated window is focused and the inhibitor is enabled. The compositor may choose to ignore inhibitor requests based on its policy.

NOTE

Using a shortcuts inhibitor requires the compositor support the [keyboard-shortcuts-inhibit-unstable-v1 ](https://wayland.app/protocols/keyboard-shortcuts-inhibit-unstable-v1)protocol.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* window : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

The window to associate the shortcuts inhibitor with. The inhibitor will only inhibit shortcuts pressed while this window has keyboard focus.

Must be set to a non null value to enable the inhibitor.

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Whether the inhibitor is currently active. The inhibitor is only active if [enabled ](#enabled)is true, [window ](#window)has keyboard focus, and the compositor grants the inhibit request.

The compositor may deactivate the inhibitor at any time (for example, if the user requests normal shortcuts to be restored). When deactivated by the compositor, the inhibitor cannot be programmatically reactivated.

* enabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the shortcuts inhibitor should be enabled. Defaults to false.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* cancelled ( ) [](/docs/configuration/qml-overview#-signals)

Sent if the compositor cancels the inhibitor while it is active.

* [window ](#window)

* [active ](#active)

* [enabled ](#enabled)

* [cancelled ](#cancelled)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
