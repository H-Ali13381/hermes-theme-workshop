## WrapperItem : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

`import Quickshell.Widgets `
This component is useful when you need to wrap a single component in an item, or give a single component a margin. See [QtQuick.Layouts ](https://doc.qt.io/qt-6/qtquicklayouts-index.html)for positioning multiple items.

NOTE

WrapperItem is a [MarginWrapperManager ](/docs/v0.3.0/types/Quickshell.Widgets/MarginWrapperManager)based component. See its documentation for information on how margins and sizes are calculated.

### Example: Adding a margin to an item

The snippet below adds a 10px margin to all sides of the [Text ](https://doc.qt.io/qt-6/qml-qtquick-text.html)item.

```
`WrapperItem {
  margin: 10

  [Text](https://doc.qt.io/qt-6/qml-qtquick-text.html) { text: "Hello!" }
}`
```

NOTE

The child item can be specified by writing it inline in the wrapper, as in the example above, or by using the [child ](#child)property. See [WrapperManager.child ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager#child)for details.

WARNING

You should not set [Item.x ](/docs/v0.3.0/types/Quickshell.Widgets/Item#x), [Item.y ](/docs/v0.3.0/types/Quickshell.Widgets/Item#y), [Item.width ](/docs/v0.3.0/types/Quickshell.Widgets/Item#width), [Item.height ](/docs/v0.3.0/types/Quickshell.Widgets/Item#height)or [Item.anchors ](/docs/v0.3.0/types/Quickshell.Widgets/Item#anchors)on the child item, as they are used by WrapperItem to position it. Instead set [Item.implicitWidth ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitWidth)and [Item.implicitHeight ](/docs/v0.3.0/types/Quickshell.Widgets/Item#implicitHeight).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* implicitHeight : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit height of the wrapper.

Defaults to the implicit width of the content item plus its top and bottom margin, and may be reset by assigning `undefined `.

* topMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested top margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* implicitWidth : [real ](https://doc.qt.io/qt-6/qml-real.html)

Overrides the implicit width of the wrapper.

Defaults to the implicit width of the content item plus its left and right margin, and may be reset by assigning `undefined `.

* leftMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested left margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* resizeChild : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Determines if child item should be resized larger than its implicit size if the parent is resized larger than its implicit size. Defaults to true.

* margin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The default for [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin)and [rightMargin ](#rightMargin). Defaults to 0.

* bottomMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested bottom margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* rightMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

The requested right margin of the content item, not counting [extraMargin ](#extraMargin).

Defaults to [margin ](#margin), and may be reset by assigning `undefined `.

* child : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

See [WrapperManager.child ](/docs/v0.3.0/types/Quickshell.Widgets/WrapperManager#child)for details.

* extraMargin : [real ](https://doc.qt.io/qt-6/qml-real.html)

An extra margin applied in addition to [topMargin ](#topMargin), [bottomMargin ](#bottomMargin), [leftMargin ](#leftMargin), and [rightMargin ](#rightMargin). Defaults to 0.

* [implicitHeight ](#implicitHeight)

* [topMargin ](#topMargin)

* [implicitWidth ](#implicitWidth)

* [leftMargin ](#leftMargin)

* [resizeChild ](#resizeChild)

* [margin ](#margin)

* [bottomMargin ](#bottomMargin)

* [rightMargin ](#rightMargin)

* [child ](#child)

* [extraMargin ](#extraMargin)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
