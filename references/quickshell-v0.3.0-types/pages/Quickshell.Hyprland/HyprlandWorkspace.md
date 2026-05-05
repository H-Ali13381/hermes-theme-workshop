## HyprlandWorkspace : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Hyprland `
## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this workspace is currently active on its monitor. See also [focused ](#focused).

* id : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

No details provided

* lastIpcObject : [unknown ](#unknown)
readonly

Last json returned for this workspace, as a javascript object.

WARNING

This is not updated unless the workspace object is fetched again from Hyprland. If you need a value that is subject to change and does not have a dedicated property, run [Hyprland.refreshWorkspaces() ](/docs/v0.3.0/types/Quickshell.Hyprland/Hyprland#refreshWorkspaces)and wait for this property to update.

* hasFullscreen : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this workspace currently has a fullscreen client.

* monitor : [HyprlandMonitor ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandMonitor)
readonly

No details provided

* urgent : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this workspace has a window that is urgent. Becomes always falsed after the workspace is [focused ](#focused).

* focused : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this workspace is currently active on a monitor and that monitor is currently focused. See also [active ](#active).

* toplevels : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)
readonly

List of toplevels on this workspace.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* activate ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Activate the workspace.

NOTE

This is equivalent to running

```
`HyprlandIpc.dispatch(`workspace ${workspace.name}`);`
```

* [name ](#name)

* [active ](#active)

* [id ](#id)

* [lastIpcObject ](#lastIpcObject)

* [hasFullscreen ](#hasFullscreen)

* [monitor ](#monitor)

* [urgent ](#urgent)

* [focused ](#focused)

* [toplevels ](#toplevels)

* [activate ](#activate)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
