## HyprlandToplevel : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Hyprland `
Represents a window as Hyprland exposes it. Can also be used as an attached object of a [Toplevel ](/docs/v0.3.0/types/Quickshell.Wayland/Toplevel), to resolve a handle to an Hyprland toplevel.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* handle : [HyprlandToplevel ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandToplevel)
readonly

The toplevel handle, exposing the Hyprland toplevel. Will be null until the address is reported

* title : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The title of the toplevel

* address : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Hexadecimal Hyprland window address. Will be an empty string until the address is reported.

* lastIpcObject : [unknown ](#unknown)
readonly

Last json returned for this toplevel, as a javascript object.

WARNING

This is not updated unless the toplevel object is fetched again from Hyprland. If you need a value that is subject to change and does not have a dedicated property, run [Hyprland.refreshToplevels() ](/docs/v0.3.0/types/Quickshell.Hyprland/Hyprland#refreshToplevels)and wait for this property to update.

* workspace : [HyprlandWorkspace ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandWorkspace)
readonly

The current workspace of the toplevel (might be null)

* monitor : [HyprlandMonitor ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandMonitor)
readonly

The current monitor of the toplevel (might be null)

* activated : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Whether the toplevel is active or not

* urgent : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Whether the client is urgent or not

* wayland : [Toplevel ](/docs/v0.3.0/types/Quickshell.Wayland/Toplevel)
readonly

The wayland toplevel handle. Will be null intil the address is reported

* [handle ](#handle)

* [title ](#title)

* [address ](#address)

* [lastIpcObject ](#lastIpcObject)

* [workspace ](#workspace)

* [monitor ](#monitor)

* [activated ](#activated)

* [urgent ](#urgent)

* [wayland ](#wayland)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
