## BoundComponent : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

`import Quickshell `
Component loader that allows setting initial properties, primarily useful for escaping cyclic dependency errors.

Properties defined on the BoundComponent will be applied to its loaded component, including required properties, and will remain reactive. Functions created with the names of signal handlers will also be attached to signals of the loaded component.

```
`MouseArea {
  required property color color;
  width: 100
  height: 100

  Rectangle {
    anchors.fill: parent
    color: parent.color
  }
}`
```

```
`BoundComponent {
  source: "MyComponent.qml"

  // this is the same as assigning to `color` on MyComponent if loaded normally.
  property color color: "red";

  // this will be triggered when the `clicked` signal from the MouseArea is sent.
  function onClicked() {
    color = "blue";
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* sourceComponent : [Component ](https://doc.qt.io/qt-6/qml-qtqml-component.html)

The source to load, as a Component.

* source : [string ](https://doc.qt.io/qt-6/qml-string.html)

The source to load, as a Url.

* implicitHeight : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

No details provided

* item : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
readonly

The loaded component. Will be null until it has finished loading.

* bindValues : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If property values should be bound after they are initially set. Defaults to `true `.

* implicitWidth : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

No details provided

* [sourceComponent ](#sourceComponent)

* [source ](#source)

* [implicitHeight ](#implicitHeight)

* [item ](#item)

* [bindValues ](#bindValues)

* [implicitWidth ](#implicitWidth)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
