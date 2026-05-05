## ClippingRectangle : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

`import Quickshell.Widgets `
WARNING

This type requires at least Qt 6.7.

This is a specialized version of [Rectangle ](https://doc.qt.io/qt-6/qml-qtquick-rectangle.html)that clips content inside of its border, including rounded rectangles. It costs more than [Rectangle ](https://doc.qt.io/qt-6/qml-qtquick-rectangle.html), so it should not be used unless you need to clip items inside of it to the border.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* antialiasing : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the rectangle should be antialiased.

Defaults to true if any corner has a non-zero radius, otherwise false.

* topRightRadius : [real ](https://doc.qt.io/qt-6/qml-real.html)

Radius of the top right corner. Defaults to [radius ](#radius).

* color : [color ](https://doc.qt.io/qt-6/qml-color.html)

The background color of the rectangle, which goes under its content.

* contentItem : [unknown ](#unknown)
readonly

The item containing the rectangle’s content. There is usually no reason to use this directly.

* bottomRightRadius : [real ](https://doc.qt.io/qt-6/qml-real.html)

Radius of the bottom right corner. Defaults to [radius ](#radius).

* border : [unknown ](#unknown)

See [Rectangle.border ](https://doc.qt.io/qt-6/qml-qtquick-rectangle.html#border-prop).

* children : [unknown ](#unknown)

Visual children of the ClippingRectangle’s [contentItem ](#contentItem). ( `list<Item> `).

See [Item.children ](https://doc.qt.io/qt-6/qml-qtquick-item.html#children-prop)for details.

* bottomLeftRadius : [real ](https://doc.qt.io/qt-6/qml-real.html)

Radius of the bottom left corner. Defaults to [radius ](#radius).

* contentInsideBorder : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the content item should be resized to fit inside the border.

Defaults to `!contentUnderBorder `. Most useful when combined with `anchors.fill: parent `on an item passed to the ClippingRectangle.

* contentUnderBorder : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If content should be displayed underneath the border.

Defaults to false, does nothing if the border is opaque.

* data : [unknown ](#unknown)
default

Data of the ClippingRectangle’s [contentItem ](#contentItem). ( `list<QtObject> `).

See [Item.data ](https://doc.qt.io/qt-6/qml-qtquick-item.html#data-prop)for details.

* radius : [real ](https://doc.qt.io/qt-6/qml-real.html)

Radius of all corners. Defaults to 0.

* topLeftRadius : [real ](https://doc.qt.io/qt-6/qml-real.html)

Radius of the top left corner. Defaults to [radius ](#radius).

* [antialiasing ](#antialiasing)

* [topRightRadius ](#topRightRadius)

* [color ](#color)

* [contentItem ](#contentItem)

* [bottomRightRadius ](#bottomRightRadius)

* [border ](#border)

* [children ](#children)

* [bottomLeftRadius ](#bottomLeftRadius)

* [contentInsideBorder ](#contentInsideBorder)

* [contentUnderBorder ](#contentUnderBorder)

* [data ](#data)

* [radius ](#radius)

* [topLeftRadius ](#topLeftRadius)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
