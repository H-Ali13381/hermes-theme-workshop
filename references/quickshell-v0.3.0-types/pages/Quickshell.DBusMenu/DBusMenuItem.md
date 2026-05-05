## DBusMenuItem : [QsMenuEntry ](/docs/v0.3.0/types/Quickshell/QsMenuEntry)
uncreatable

`import Quickshell.DBusMenu `
Menu item shared by an external program via the [DBusMenu specification ](https://github.com/AyatanaIndicators/libdbusmenu/blob/master/libdbusmenu-glib/dbus-menu.xml).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* menuHandle : [DBusMenuHandle ](/docs/v0.3.0/types/Quickshell.DBusMenu/DBusMenuHandle)
readonly

Handle to the root of this menu.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* updateLayout ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Refreshes the menu contents.

Usually you shouldn’t need to call this manually but some applications providing menus do not update them correctly. Call this if menus don’t update their state.

The [layoutUpdated() ](#layoutUpdated)signal will be sent when a response is received.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* layoutUpdated ( ) [](/docs/configuration/qml-overview#-signals)

No details provided

* [menuHandle ](#menuHandle)

* [updateLayout ](#updateLayout)

* [layoutUpdated ](#layoutUpdated)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
