## SocketServer : [Reloadable ](/docs/v0.3.0/types/Quickshell/Reloadable)

`import Quickshell.Io `
#### Example

```
`SocketServer {
  active: true
  path: "/path/too/socket.sock"
  handler: Socket {
    onConnectedChanged: {
      console.log(connected ? "new connection!" : "connection dropped!")
    }
    parser: SplitParser {
      onRead: message => console.log(`read message from socket: ${message}`)
    }
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* path : [string ](https://doc.qt.io/qt-6/qml-string.html)

The path to create the socket server at.

Setting this property while the server is active will have no effect.

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the socket server is currently active. Defaults to false.

Setting this to false will destroy all active connections and delete the socket file on disk.

If path is empty setting this property will have no effect.

* handler : [Component ](https://doc.qt.io/qt-6/qml-qtqml-component.html)

Connection handler component. Must create a [Socket ](/docs/v0.3.0/types/Quickshell.Io/Socket).

The created socket should not set [connected ](#connected)or [path ](#path)or the incoming socket connection will be dropped (they will be set by the socket server.) Setting `connected `to false on the created socket after connection will close and delete it.

* [path ](#path)

* [active ](#active)

* [handler ](#handler)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
