## QsMenuAnchor : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell `
Display anchor for platform menus.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* anchor : [PopupAnchor ](/docs/v0.3.0/types/Quickshell/PopupAnchor)
readonly

The menu’s anchor / positioner relative to another window. The menu will not be shown until it has a valid anchor.

NOTE

The following is subject to change and NOT a guarantee of future behavior.

A snapshot of the anchor at the time [opened() ](#opened)is emitted will be used to position the menu. Additional changes to the anchor after this point will not affect the placement of the menu.

You can set properties of the anchor like so:

```
`QsMenuAnchor {
  anchor.window: parentwindow
  // or
  anchor {
    window: parentwindow
  }
}`
```

* visible : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the menu is currently open and visible.

See also: [open() ](#open), [close() ](#close).

* menu : [QsMenuHandle ](/docs/v0.3.0/types/Quickshell/QsMenuHandle)

The menu that should be displayed on this anchor.

See also: [SystemTrayItem.menu ](/docs/v0.3.0/types/Quickshell.Services.SystemTray/SystemTrayItem#menu).

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* close ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Close the open menu.

* open ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Open the given menu on this menu Requires that [anchor ](#anchor)is valid.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* closed ( ) [](/docs/configuration/qml-overview#-signals)

Sent when the menu is closed.

* opened ( ) [](/docs/configuration/qml-overview#-signals)

Sent when the menu is displayed onscreen which may be after [visible ](#visible)becomes true.

* [anchor ](#anchor)

* [visible ](#visible)

* [menu ](#menu)

* [close ](#close)

* [open ](#open)

* [closed ](#closed)

* [opened ](#opened)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
