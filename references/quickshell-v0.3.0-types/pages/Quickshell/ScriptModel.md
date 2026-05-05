## ScriptModel : ScriptModel

`import Quickshell `
ScriptModel is a QML [Data Model ](https://doc.qt.io/qt-6/qtquick-modelviewsdata-modelview.html#qml-data-models)that generates model operations based on changes to a javascript expression attached to [values ](#values).

### When should I use this

ScriptModel should be used when you would otherwise use a javascript expression as a model, [QAbstractItemModel ](https://doc.qt.io/qt-6/qabstractitemmodel.html)is accepted, and the data is likely to change over the lifetime of the program.

When directly using a javascript expression as a model, types like [Repeater ](https://doc.qt.io/qt-6/qml-qtquick-repeater.html)or [ListView ](https://doc.qt.io/qt-6/qml-qtquick-listview.html)will destroy all created delegates, and re-create the entire list. In the case of [ListView ](https://doc.qt.io/qt-6/qml-qtquick-listview.html)this will also prevent animations from working. If you wrap your expression with ScriptModel, only new items will be created, and ListView animations will work as expected.

### Example

```
`// Will cause all delegates to be re-created every time filterText changes.
[Repeater](https://doc.qt.io/qt-6/qml-qtquick-repeater.html) {
  model: myList.filter(entry => entry.name.startsWith(filterText))
  delegate: // ...
}

// Will add and remove delegates only when required.
[Repeater](https://doc.qt.io/qt-6/qml-qtquick-repeater.html) {
  model: ScriptModel {
    values: myList.filter(entry => entry.name.startsWith(filterText))
  }

  delegate: // ...
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* values : [unknown ](#unknown)

The list of values to reflect in the model.

WARNING

ScriptModel currently only works with lists of unique values. There must not be any duplicates in the given list, or behavior of the model is undefined.

TIP

[ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)s supplied by Quickshell types will only contain unique values, and can be used like so:

```
`ScriptModel {
  values: DesktopEntries.applications.values.filter(...)
}`
```

Note that we are using [ObjectModel.values ](/docs/v0.3.0/types/Quickshell/ObjectModel#values)because it will cause [ScriptModel.values ](/docs/v0.3.0/types/Quickshell/ScriptModel#values)to receive an update on change.

TIP

Most lists exposed by Quickshell are read-only. Some operations like `sort() `act on a list in-place and cannot be used directly on a list exposed by Quickshell. You can copy a list using spread syntax: `[...variable] `instead of `variable `.

For example:

```
`ScriptModel {
  values: [...DesktopEntries.applications.values].sort(...)
}`
```

* objectProp : [string ](https://doc.qt.io/qt-6/qml-string.html)

The property that javascript objects passed into the model will be compared with.

For example, if `objectProp `is `"myprop" `then `{ myprop: "a", other: "y" } `and `{ myprop: "a", other: "z" } `will be considered equal.

Defaults to `"" `, meaning no key.

* [values ](#values)

* [objectProp ](#objectProp)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
