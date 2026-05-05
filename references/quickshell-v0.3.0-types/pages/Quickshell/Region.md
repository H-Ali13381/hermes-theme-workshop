## Region : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell `
See [QsWindow.mask ](/docs/v0.3.0/types/Quickshell/QsWindow#mask).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* x : [int ](https://doc.qt.io/qt-6/qml-int.html)

Defaults to 0. Does nothing if [item ](#item)is set.

* radius : [int ](https://doc.qt.io/qt-6/qml-int.html)

Corner radius for rounded rectangles. Only applies when [shape ](#shape)is `Rect `. Defaults to 0.

Acts as the default for [topLeftRadius ](#topLeftRadius), [topRightRadius ](#topRightRadius), [bottomLeftRadius ](#bottomLeftRadius), and [bottomRightRadius ](#bottomRightRadius).

* item : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

The item that determines the geometry of the region. `item `overrides [x ](#x), [y ](#y), [width ](#width)and [height ](#height).

* regions : [list ](https://doc.qt.io/qt-6/qml-list.html)< [Region ](/docs/v0.3.0/types/Quickshell/Region)>
default readonly

Regions to apply on top of this region.

Regions can be nested to create a more complex region. For example this will create a square region with a cutout in the middle.

```
`Region {
  width: 100; height: 100;

  Region {
    x: 50; y: 50;
    width: 50; height: 50;
    intersection: Intersection.Subtract
  }
}`
```

* shape : [RegionShape ](/docs/v0.3.0/types/Quickshell/RegionShape)

Defaults to `Rect `.

* height : [int ](https://doc.qt.io/qt-6/qml-int.html)

Defaults to 0. Does nothing if [item ](#item)is set.

* intersection : [Intersection ](/docs/v0.3.0/types/Quickshell/Intersection)

The way this region interacts with its parent region. Defaults to `Combine `.

* bottomLeftRadius : [int ](https://doc.qt.io/qt-6/qml-int.html)

Bottom-left corner radius. Only applies when [shape ](#shape)is `Rect `.

Defaults to [radius ](#radius), and may be reset by assigning `undefined `.

* topLeftRadius : [int ](https://doc.qt.io/qt-6/qml-int.html)

Top-left corner radius. Only applies when [shape ](#shape)is `Rect `.

Defaults to [radius ](#radius), and may be reset by assigning `undefined `.

* width : [int ](https://doc.qt.io/qt-6/qml-int.html)

Defaults to 0. Does nothing if [item ](#item)is set.

* topRightRadius : [int ](https://doc.qt.io/qt-6/qml-int.html)

Top-right corner radius. Only applies when [shape ](#shape)is `Rect `.

Defaults to [radius ](#radius), and may be reset by assigning `undefined `.

* bottomRightRadius : [int ](https://doc.qt.io/qt-6/qml-int.html)

Bottom-right corner radius. Only applies when [shape ](#shape)is `Rect `.

Defaults to [radius ](#radius), and may be reset by assigning `undefined `.

* y : [int ](https://doc.qt.io/qt-6/qml-int.html)

Defaults to 0. Does nothing if [item ](#item)is set.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* childrenChanged ( ) [](/docs/configuration/qml-overview#-signals)

No details provided

* changed ( ) [](/docs/configuration/qml-overview#-signals)

Triggered when the region’s geometry changes.

In some cases the region does not update automatically. In those cases you can emit this signal manually.

* [x ](#x)

* [radius ](#radius)

* [item ](#item)

* [regions ](#regions)

* [shape ](#shape)

* [height ](#height)

* [intersection ](#intersection)

* [bottomLeftRadius ](#bottomLeftRadius)

* [topLeftRadius ](#topLeftRadius)

* [width ](#width)

* [topRightRadius ](#topRightRadius)

* [bottomRightRadius ](#bottomRightRadius)

* [y ](#y)

* [childrenChanged ](#childrenChanged)

* [changed ](#changed)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
