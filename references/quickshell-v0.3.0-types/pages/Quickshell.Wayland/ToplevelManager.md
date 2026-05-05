## ToplevelManager : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
singleton

`import Quickshell.Wayland `
Exposes a list of windows from other applications as [Toplevel ](/docs/v0.3.0/types/Quickshell.Wayland/Toplevel)s via the [zwlr-foreign-toplevel-management-v1 ](https://wayland.app/protocols/wlr-foreign-toplevel-management-unstable-v1)wayland protocol.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* activeToplevel : [Toplevel ](/docs/v0.3.0/types/Quickshell.Wayland/Toplevel)
readonly

Active toplevel or null.

NOTE

If multiple are active, this will be the most recently activated one. Usually compositors will not report more than one toplevel as active at a time.

* toplevels : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [Toplevel ](/docs/v0.3.0/types/Quickshell.Wayland/Toplevel)>
readonly

All toplevel windows exposed by the compositor.

* [activeToplevel ](#activeToplevel)

* [toplevels ](#toplevels)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
