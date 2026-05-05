## RetainableLock : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell `
A RetainableLock provides extra safety and ease of use for locking [Retainable ](/docs/v0.3.0/types/Quickshell/Retainable)objects. A retainable object can be locked by multiple locks at once, and each lock re-exposes relevant properties of the retained objects.

#### Example

The code below will keep a retainable object alive for as long as the RetainableLock exists.

```
`RetainableLock {
  object: aRetainableObject
  locked: true
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* object : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

The object to lock. Must be [Retainable ](/docs/v0.3.0/types/Quickshell/Retainable).

* locked : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the object should be locked.

* retained : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the object is currently in a retained state.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* aboutToDestroy ( ) [](/docs/configuration/qml-overview#-signals)

Rebroadcast of the object’s [Retainable.aboutToDestroy() ](/docs/v0.3.0/types/Quickshell/Retainable#aboutToDestroy).

* dropped ( ) [](/docs/configuration/qml-overview#-signals)

Rebroadcast of the object’s [Retainable.dropped() ](/docs/v0.3.0/types/Quickshell/Retainable#dropped).

* [object ](#object)

* [locked ](#locked)

* [retained ](#retained)

* [aboutToDestroy ](#aboutToDestroy)

* [dropped ](#dropped)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
