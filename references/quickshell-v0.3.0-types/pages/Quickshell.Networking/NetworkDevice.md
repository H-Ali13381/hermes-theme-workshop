## NetworkDevice : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Networking `
The [type ](#type)property may be used to determine if this device is a [WifiDevice ](/docs/v0.3.0/types/Quickshell.Networking/WifiDevice)or [WiredDevice ](/docs/v0.3.0/types/Quickshell.Networking/WiredDevice).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* networks : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [Network ](/docs/v0.3.0/types/Quickshell.Networking/Network)>
readonly

A list of available or connected networks for this device.

When the device type is ‘Wifi’, this model will only contain [WifiNetwork ](/docs/v0.3.0/types/Quickshell.Networking/WifiNetwork).

* state : [ConnectionState ](/docs/v0.3.0/types/Quickshell.Networking/ConnectionState)
readonly

Connection state of the device.

* type : [DeviceType ](/docs/v0.3.0/types/Quickshell.Networking/DeviceType)
readonly

The device type.

When the device type is `Wifi `, the device object is a [WifiDevice ](/docs/v0.3.0/types/Quickshell.Networking/WifiDevice). When the device type is `Wired `, the device object is a [WiredDevice ](/docs/v0.3.0/types/Quickshell.Networking/WiredDevice). connection and scanning.

* autoconnect : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

True if the device is allowed to autoconnect to a network.

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The name of the device’s control interface.

* address : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The hardware address of the device in the XX:XX:XX:XX:XX:XX format.

* connected : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

True if the device is connected.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* disconnect ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Disconnects the device and prevents it from automatically activating further connections.

* [networks ](#networks)

* [state ](#state)

* [type ](#type)

* [autoconnect ](#autoconnect)

* [name ](#name)

* [address ](#address)

* [connected ](#connected)

* [disconnect ](#disconnect)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
