## TransformWatcher : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell `
The TransformWatcher monitors all properties that affect the geometry of two [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)s relative to eachother.

NOTE

The algorithm responsible for determining the relationship between `a `and `b `is biased towards `a `being a parent of `b `, or `a `being closer to the common parent of `a `and `b `than `b `.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* a : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

No details provided

* b : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

No details provided

* commonParent : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

Known common parent of both `a `and `b `. Defaults to `null `.

This property can be used to optimize the algorithm that figures out the relationship between `a `and `b `. Setting it to something that is not a common parent of both `a `and `b `will prevent the path from being determined correctly, and setting it to `null `will disable the optimization.

* transform : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
readonly

This property is updated whenever the geometry of any item in the path from `a `to `b `changes.

Its value is undefined, and is intended to trigger an expression update.

* [a ](#a)

* [b ](#b)

* [commonParent ](#commonParent)

* [transform ](#transform)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
