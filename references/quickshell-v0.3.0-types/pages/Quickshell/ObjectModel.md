## ObjectModel : ObjectModel
uncreatable

`import Quickshell `
Typed view into a list of objects.

An ObjectModel works as a QML [Data Model ](https://doc.qt.io/qt-6/qtquick-modelviewsdata-modelview.html#qml-data-models), allowing efficient interaction with components that act on models. It has a single role named `modelData `, to match the behavior of lists. The same information contained in the list model is available as a normal list via the `values `property.

#### Differences from a list

Unlike with a list, the following property binding will never be updated when `model[3] `changes.

```
`// will not update reactively
property var foo: model[3]`
```

You can work around this limitation using the [values ](#values)property of the model to view it as a list.

```
`// will update reactively
property var foo: model.values[3]`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* values : [list ](https://doc.qt.io/qt-6/qml-list.html)< [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)>
readonly

The content of the object model, as a QML list. The values of this property will always be of the type of the model.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* indexOf ( ) : [int ](https://doc.qt.io/qt-6/qml-int.html)

No details provided

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* objectInsertedPost ( object, index ) [](/docs/configuration/qml-overview#-signals)

object : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)index : [int ](https://doc.qt.io/qt-6/qml-int.html)

Sent immediately after an object is inserted into the list.

* objectInsertedPre ( object, index ) [](/docs/configuration/qml-overview#-signals)

object : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)index : [int ](https://doc.qt.io/qt-6/qml-int.html)

Sent immediately before an object is inserted into the list.

* objectRemovedPre ( object, index ) [](/docs/configuration/qml-overview#-signals)

object : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)index : [int ](https://doc.qt.io/qt-6/qml-int.html)

Sent immediately before an object is removed from the list.

* objectRemovedPost ( object, index ) [](/docs/configuration/qml-overview#-signals)

object : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)index : [int ](https://doc.qt.io/qt-6/qml-int.html)

Sent immediately after an object is removed from the list.

* [values ](#values)

* [indexOf ](#indexOf)

* [objectInsertedPost ](#objectInsertedPost)

* [objectInsertedPre ](#objectInsertedPre)

* [objectRemovedPre ](#objectRemovedPre)

* [objectRemovedPost ](#objectRemovedPost)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
