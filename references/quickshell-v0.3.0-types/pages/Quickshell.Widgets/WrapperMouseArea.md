## WrapperMouseArea : WrapperMouseArea

`import Quickshell.Widgets `
This component is useful for wrapping a single component in a mouse area. It works the same as [WrapperItem ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperItem), but with a [MouseArea ](https://doc.qt.io/qt-6/qml-qtquick-mousearea.html).

NOTE

WrapperMouseArea is a [MarginWrapperManager ](/docs/v0.3.0/types/Quickshell.Widgets/MarginWrapperManager)based component. See its documentation for information on how margins and sizes are calculated.

NOTE

The child item can be specified by writing it inline in the wrapper, as in the example above, or by using the [child ](#child)property. See [WrapperManager.child ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager#child)for details.

WARNING

You should not set [Item.x ](/docs/v0.3.0/types/Quickshell.Widgets/Item#x), [Item.y ](/docs/v0.3.0/types/Quickshell.Widgets/Item#y), [Item.width ](/docs/v0.3.0/types/Quickshell.Widgets/Item#width), [Item.height ](/docs/v0.3.0/types/Quickshell.Widgets/Item#height)or [Item.anchors ](/docs/v0.3.0/types/Quickshell.Widgets/Item#anchors)on the child item, as they are used by WrapperItem to position it. Instead set [Item.implicitWidth ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitWidth)and [Item.implicitHeight ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitHeight).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* topMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested top margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* child : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

See [WrapperManager.child ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager#child)for details.

* leftMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested left margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* implicitHeight : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit height of the wrapper.

Defaults to the implicit width of the content item plus its top and bottom margin, and may be reset by assigning `undefined `.

* implicitWidth : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit width of the wrapper.

Defaults to the implicit width of the content item plus its left and right margin, and may be reset by assigning `undefined `.

* rightMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested right margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* margin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The default for [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin)and [rightMargin ](#rightMargin). Defaults to 0.

* extraMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

An extra margin applied in addition to [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin), and [rightMargin ](#rightMargin). Defaults to 0.

* resizeChild : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Determines if child item should be resized larger than its implicit size if the parent is resized larger than its implicit size. Defaults to true.

* bottomMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested bottom margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* [topMargin ](#topMargin)

* [child ](#child)

* [leftMargin ](#leftMargin)

* [implicitHeight ](#implicitHeight)

* [implicitWidth ](#implicitWidth)

* [rightMargin ](#rightMargin)

* [margin ](#margin)

* [extraMargin ](#extraMargin)

* [resizeChild ](#resizeChild)

* [bottomMargin ](#bottomMargin)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
