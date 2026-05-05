## Network : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Networking `
A network. Networks derived from a [WifiDevice ](/docs/v0.3.0/types/Quickshell.Networking/WifiDevice)are [WifiNetwork ](/docs/v0.3.0/types/Quickshell.Networking/WifiNetwork)instances.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* stateChanging : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the network is currently connecting or disconnecting. Shorthand for checking [state ](#state).

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The name of the network.

* connected : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

True if the network is connected.

* device : [NetworkDevice ](/docs/v0.3.0/types/Quickshell.Networking/NetworkDevice)
readonly

The device this network belongs to.

* nmSettings : [list ](https://doc.qt.io/qt-6/qml-list.html)< [NMSettings ](/docs/v0.3.0/types/Quickshell.Networking/NMSettings)>
readonly

A list of NetworkManager connection settings profiles for this network.

WARNING

Only valid for the NetworkManager backend.

* known : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

True if the wifi network has known connection settings saved.

* state : [ConnectionState ](/docs/v0.3.0/types/Quickshell.Networking/ConnectionState)
readonly

The connectivity state of the network.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* connect ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Attempt to connect to the network.

NOTE

If the network is a [WifiNetwork ](/docs/v0.3.0/types/Quickshell.Networking/WifiNetwork)and requires secrets, a [connectionFailed() ](#connectionFailed)signal will be emitted with `NoSecrets `. [WifiNetwork.connectWithPsk() ](/docs/v0.3.0/types/Quickshell.Networking/WifiNetwork#connectWithPsk)can be used to provide secrets.

* connectWithSettings ( settings ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

settings : [NMSettings ](/docs/v0.3.0/types/Quickshell.Networking/NMSettings)

Attempt to connect to the network with a specific [nmSettings ](#nmSettings)entry.

WARNING

Only valid for the NetworkManager backend.

* disconnect ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Disconnect from the network.

* forget ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Forget all connection settings for this network.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* connectionFailed ( reason ) [](/docs/configuration/qml-overview#-signals)

reason : [ConnectionFailReason ](/docs/v0.3.0/types/Quickshell.Networking/ConnectionFailReason)

Signals that a connection to the network has failed because of the given [ConnectionFailReason ](/docs/v0.3.0/types/Quickshell.Networking/ConnectionFailReason).

* [stateChanging ](#stateChanging)

* [name ](#name)

* [connected ](#connected)

* [device ](#device)

* [nmSettings ](#nmSettings)

* [known ](#known)

* [state ](#state)

* [connect ](#connect)

* [connectWithSettings ](#connectWithSettings)

* [disconnect ](#disconnect)

* [forget ](#forget)

* [connectionFailed ](#connectionFailed)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
