## SystemTrayItem : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.SystemTray `
A system tray item, roughly conforming to the [kde/freedesktop spec ](https://www.freedesktop.org/wiki/Specifications/StatusNotifierItem/StatusNotifierItem/)(there is no real spec, we just implemented whatever seemed to actually be used).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* status : [Status ](/docs/v0.3.0/types/Quickshell.Services.SystemTray/Status)
readonly

No details provided

* tooltipDescription : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

* title : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Text that describes the application.

* category : [Category ](/docs/v0.3.0/types/Quickshell.Services.SystemTray/Category)
readonly

No details provided

* tooltipTitle : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

* icon : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Icon source string, usable as an Image source.

* hasMenu : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this tray item has an associated menu accessible via [display() ](#display)or [menu ](#menu).

* onlyMenu : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this tray item only offers a menu and activation will do nothing.

* menu : [unknown ](#unknown)
readonly

A handle to the menu associated with this tray item, if any.

Can be displayed with [QsMenuAnchor ](/docs/v0.3.0/types/Quickshell/QsMenuAnchor)or [QsMenuOpener ](/docs/v0.3.0/types/Quickshell/QsMenuOpener).

* id : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

A name unique to the application, such as its name.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* activate ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Primary activation action, generally triggered via a left click.

* display ( parentWindow, relativeX, relativeY ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

parentWindow : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)relativeX : [int ](https://doc.qt.io/qt-6/qml-int.html)relativeY : [int ](https://doc.qt.io/qt-6/qml-int.html)

Display a platform menu at the given location relative to the parent window.

* scroll ( delta, horizontal ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

delta : [int ](https://doc.qt.io/qt-6/qml-int.html)horizontal : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Scroll action, such as changing volume on a mixer.

* secondaryActivate ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Secondary activation action, generally triggered via a middle click.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* ready ( ) [](/docs/configuration/qml-overview#-signals)

No details provided

* [status ](#status)

* [tooltipDescription ](#tooltipDescription)

* [title ](#title)

* [category ](#category)

* [tooltipTitle ](#tooltipTitle)

* [icon ](#icon)

* [hasMenu ](#hasMenu)

* [onlyMenu ](#onlyMenu)

* [menu ](#menu)

* [id ](#id)

* [activate ](#activate)

* [display ](#display)

* [scroll ](#scroll)

* [secondaryActivate ](#secondaryActivate)

* [ready ](#ready)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
