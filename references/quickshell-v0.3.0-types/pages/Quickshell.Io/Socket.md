## Socket : [DataStream ](/docs/v0.3.0/types/Quickshell.Io/DataStream)

`import Quickshell.Io `
Unix socket listener.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* connected : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Returns if the socket is currently connected.

Writing to this property will set the target connection state and will not update the property immediately. Setting the property to false will begin disconnecting the socket, and setting it to true will begin connecting the socket if path is not empty.

* path : [string ](https://doc.qt.io/qt-6/qml-string.html)

The path to connect this socket to when [connected ](#connected)is set to true.

Changing this property will have no effect while the connection is active.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* flush ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Flush any queued writes to the socket.

* write ( data ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

data : [string ](https://doc.qt.io/qt-6/qml-string.html)

Write data to the socket. Does nothing if not connected.

Remember to call flush after your last write.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* error ( error ) [](/docs/configuration/qml-overview#-signals)

error : [](#unknown)

This signal is sent whenever a socket error is encountered.

* [connected ](#connected)

* [path ](#path)

* [flush ](#flush)

* [write ](#write)

* [error ](#error)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
