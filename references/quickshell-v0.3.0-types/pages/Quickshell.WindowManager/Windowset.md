## Windowset : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.WindowManager `
A Windowset is a generic type that encompasses both “Workspaces” and “Tags” in window managers. Because the definition encompasses both you may not necessarily need all features.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* coordinates : [list ](https://doc.qt.io/qt-6/qml-list.html)< [int ](https://doc.qt.io/qt-6/qml-int.html)>
readonly

Coordinates of the workspace, represented as an N-dimensional array. Most WMs will only expose one coordinate. If more than one is exposed, the first is conventionally X, the second Y, and the third Z.

* shouldDisplay : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If false, this windowset should generally be hidden from workspace pickers.

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

True if the windowset is currently active. In a workspace based WM, this means the represented workspace is current. In a tag based WM, this means the represented tag is active.

* urgent : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, a window in this windowset has been marked as urgent.

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Human readable name of the windowset.

* canSetProjection : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, the windowset can be moved to a different projection.

* canDeactivate : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, the windowset can be deactivated. In a workspace based WM, deactivation is usually implicit and based on activation of another workspace.

* id : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

A persistent internal identifier for the windowset. This property should be identical across restarts and destruction/recreation of a windowset.

* projection : [WindowsetProjection ](/docs/v0.3.0/types/Quickshell.WindowManager/WindowsetProjection)
readonly

The projection this windowset is a member of. A projection is the set of screens covered by a windowset.

* canActivate : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, the windowset can be activated. In a workspace based WM, this will make the workspace current, in a tag based wm, the tag will be activated.

* canRemove : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, the windowset can be removed. This may be done implicitly by the WM as well.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* activate ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Activate the windowset, making it the current workspace on a workspace based WM, or activating the tag on a tag based WM. Requires [canActivate ](#canActivate).

* deactivate ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Deactivate the windowset, hiding it. Requires [canDeactivate ](#canDeactivate).

* remove ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Remove or destroy the windowset. Requires [canRemove ](#canRemove).

* setProjection ( projection ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

projection : [WindowsetProjection ](/docs/v0.3.0/types/Quickshell.WindowManager/WindowsetProjection)

Move the windowset to a different projection. A projection represents the set of screens a workspace spans. Requires [canSetProjection ](#canSetProjection).

* [coordinates ](#coordinates)

* [shouldDisplay ](#shouldDisplay)

* [active ](#active)

* [urgent ](#urgent)

* [name ](#name)

* [canSetProjection ](#canSetProjection)

* [canDeactivate ](#canDeactivate)

* [id ](#id)

* [projection ](#projection)

* [canActivate ](#canActivate)

* [canRemove ](#canRemove)

* [activate ](#activate)

* [deactivate ](#deactivate)

* [remove ](#remove)

* [setProjection ](#setProjection)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
