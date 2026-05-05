## QsMenuEntry : [QsMenuHandle ](/docs/v0.3.0/types/Quickshell/QsMenuHandle)
uncreatable

`import Quickshell `
## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* buttonType : [QsMenuButtonType ](/docs/v0.3.0/types/Quickshell/QsMenuButtonType)
readonly

If this menu item has an associated checkbox or radiobutton.

* isSeparator : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this menu item should be rendered as a separator between other items.

No other properties have a meaningful value when [isSeparator ](#isSeparator)is true.

* enabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* text : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Text of the menu item.

* checkState : [unknown ](#unknown)
readonly

The check state of the checkbox or radiobutton if applicable, as a [Qt.CheckState ](https://doc.qt.io/qt-6/qt.html#CheckState-enum).

* icon : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Url of the menu item’s icon or `"" `if it doesn’t have one.

This can be passed to [Image.source ](https://doc.qt.io/qt-6/qml-qtquick-image.html#source-prop)as shown below.

```
`Image {
  source: menuItem.icon
  // To get the best image quality, set the image source size to the same size
  // as the rendered image.
  sourceSize.width: width
  sourceSize.height: height
}`
```

* hasChildren : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this menu item has children that can be accessed through a [QsMenuOpener ](/docs/v0.3.0/types/Quickshell/QsMenuOpener).

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* display ( parentWindow, relativeX, relativeY ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

parentWindow : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)relativeX : [int ](https://doc.qt.io/qt-6/qml-int.html)relativeY : [int ](https://doc.qt.io/qt-6/qml-int.html)

Display a platform menu at the given location relative to the parent window.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* triggered ( ) [](/docs/configuration/qml-overview#-signals)

Send a trigger/click signal to the menu entry.

* [buttonType ](#buttonType)

* [isSeparator ](#isSeparator)

* [enabled ](#enabled)

* [text ](#text)

* [checkState ](#checkState)

* [icon ](#icon)

* [hasChildren ](#hasChildren)

* [display ](#display)

* [triggered ](#triggered)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
