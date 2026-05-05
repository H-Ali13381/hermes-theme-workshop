## I3IpcListener : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.I3 `
#### Example

```
`I3IpcListener {
  subscriptions: ["input"]
  onIpcEvent: function (event) {
    handleInputEvent(event.data)
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* subscriptions : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>

List of [I3/Sway events ](https://man.archlinux.org/man/sway-ipc.7.en#EVENTS)to subscribe to.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* ipcEvent ( event ) [](/docs/configuration/qml-overview#-signals)

event : [I3Event ](/docs/v0.3.0/types/Quickshell.I3/I3Event)
No details provided

* [subscriptions ](#subscriptions)

* [ipcEvent ](#ipcEvent)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
