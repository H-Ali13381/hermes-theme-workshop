## ClippingWrapperRectangle : ClippingWrapperRectangle

`import Quickshell.Widgets `
This component is useful for adding a clipping border or background rectangle to a child item. If you don’t need clipping, use [WrapperRectangle ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperRectangle).

NOTE

ClippingWrapperRectangle is a [MarginWrapperManager ](/docs/v0.3.0/types/Quickshell.Widgets/MarginWrapperManager)based component. See its documentation for information on how margins and sizes are calculated.

WARNING

You should not set [Item.x ](/docs/v0.3.0/types/Quickshell.Widgets/Item#x), [Item.y ](/docs/v0.3.0/types/Quickshell.Widgets/Item#y), [Item.width ](/docs/v0.3.0/types/Quickshell.Widgets/Item#width), [Item.height ](/docs/v0.3.0/types/Quickshell.Widgets/Item#height)or [Item.anchors ](/docs/v0.3.0/types/Quickshell.Widgets/Item#anchors)on the child item, as they are used by WrapperItem to position it. Instead set [Item.implicitWidth ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitWidth)and [Item.implicitHeight ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitHeight).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* extraMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

An extra margin applied in addition to [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin), and [rightMargin ](#rightMargin). If [contentInsideBorder ](#contentInsideBorder)is true, the rectangle’s border width will be added to this property. Defaults to 0.

* implicitHeight : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit height of the wrapper.

Defaults to the implicit width of the content item plus its top and bottom margin, and may be reset by assigning `undefined `.

* bottomMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested bottom margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* leftMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested left margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* margin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The default for [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin)and [rightMargin ](#rightMargin). Defaults to 0.

* resizeChild : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Determines if child item should be resized larger than its implicit size if the parent is resized larger than its implicit size. Defaults to true.

* rightMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested right margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* topMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested top margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* child : [unknown ](#unknown)

See [WrapperManager.child ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager#child)for details.

* implicitWidth : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit width of the wrapper.

Defaults to the implicit width of the content item plus its left and right margin, and may be reset by assigning `undefined `.

* [extraMargin ](#extraMargin)

* [implicitHeight ](#implicitHeight)

* [bottomMargin ](#bottomMargin)

* [leftMargin ](#leftMargin)

* [margin ](#margin)

* [resizeChild ](#resizeChild)

* [rightMargin ](#rightMargin)

* [topMargin ](#topMargin)

* [child ](#child)

* [implicitWidth ](#implicitWidth)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
