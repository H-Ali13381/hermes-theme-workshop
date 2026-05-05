## MarginWrapperManager : [WrapperManager ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager)

`import Quickshell.Widgets `
NOTE

MarginWrapperManager is an extension of [WrapperManager ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager). You should read its documentation to understand wrapper types.

MarginWrapperManager can be used to apply margins to a child item, in addition to handling the size / implicit size relationship between the parent and the child. [WrapperItem ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperItem)and [WrapperRectangle ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperRectangle)exist for Item and Rectangle implementations respectively.

WARNING

MarginWrapperManager based types set the child item’s [Item.x ](https://doc.qt.io/qt-6/qml-qtquick-item.html#x-prop), [Item.y ](https://doc.qt.io/qt-6/qml-qtquick-item.html#y-prop), [Item.width ](https://doc.qt.io/qt-6/qml-qtquick-item.html#width-prop), [Item.height ](https://doc.qt.io/qt-6/qml-qtquick-item.html#height-prop)or [Item.anchors ](https://doc.qt.io/qt-6/qml-qtquick-item.html#anchors-prop)properties. Do not set them yourself, instead set [Item.implicitWidth ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitWidth)and [Item.implicitHeight ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitHeight).

### Implementing a margin wrapper type

Follow the directions in [WrapperManager ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager)’s documentation, and or alias the [margin ](#margin)property if you wish to expose it.

## Margin calculation

The margin of the content item is calculated based on [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin), [rightMargin ](#rightMargin), [extraMargin ](#extraMargin)and [resizeChild ](#resizeChild).

If [resizeChild ](#resizeChild)is `true `, each side’s margin will be the value of `<side>Margin `plus [extraMargin ](#extraMargin), and the content item will be stretched to match the given margin if the wrapper is not at its implicit size.

If [resizeChild ](#resizeChild)is `false `, the `<side>Margin `properties will be interpreted as a ratio and the content item will not be stretched if the wrapper is not at its implicit side.

The implicit size of the wrapper is the implicit size of the content item plus all margins.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* bottomMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested bottom margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* implicitHeight : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit height of the wrapper.

Defaults to the implicit width of the content item plus its top and bottom margin, and may be reset by assigning `undefined `.

* leftMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested left margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* rightMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested right margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* implicitWidth : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit width of the wrapper.

Defaults to the implicit width of the content item plus its left and right margin, and may be reset by assigning `undefined `.

* topMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested top margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* margin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The default for [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin)and [rightMargin ](#rightMargin). Defaults to 0.

* resizeChild : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Determines if child item should be resized larger than its implicit size if the parent is resized larger than its implicit size. Defaults to true.

* extraMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

An extra margin applied in addition to [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin), and [rightMargin ](#rightMargin). Defaults to 0.

* [bottomMargin ](#bottomMargin)

* [implicitHeight ](#implicitHeight)

* [leftMargin ](#leftMargin)

* [rightMargin ](#rightMargin)

* [implicitWidth ](#implicitWidth)

* [topMargin ](#topMargin)

* [margin ](#margin)

* [resizeChild ](#resizeChild)

* [extraMargin ](#extraMargin)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
