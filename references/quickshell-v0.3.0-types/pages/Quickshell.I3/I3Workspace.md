## I3Workspace : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.I3 `
I3/Sway workspaces

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* id : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

The ID of this workspace, it is unique for i3/Sway launch

* focused : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this workspace is currently active on a monitor and that monitor is currently focused. See also [active ](#active).

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The name of this workspace

* num : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

Deprecated: use [number ](#number)

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this workspace is currently active on its monitor. See also [focused ](#focused).

* urgent : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If a window in this workspace has an urgent notification

* number : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

The number of this workspace

* lastIpcObject : [unknown ](#unknown)
readonly

Last JSON returned for this workspace, as a JavaScript object.

This updates every time we receive a `workspace `event from i3/Sway

* monitor : [I3Monitor ](/docs/v0.3.0/types/Quickshell.I3/I3Monitor)
readonly

The monitor this workspace is being displayed on

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* activate ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Activate the workspace.

NOTE

This is equivalent to running

```
`I3.dispatch(`workspace number ${workspace.number}`);`
```

* [id ](#id)

* [focused ](#focused)

* [name ](#name)

* [num ](#num)

* [active ](#active)

* [urgent ](#urgent)

* [number ](#number)

* [lastIpcObject ](#lastIpcObject)

* [monitor ](#monitor)

* [activate ](#activate)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
