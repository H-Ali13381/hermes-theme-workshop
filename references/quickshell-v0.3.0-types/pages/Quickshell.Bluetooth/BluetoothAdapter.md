## BluetoothAdapter : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Bluetooth `
A Bluetooth adapter

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* dbusPath : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

DBus path of the adapter under the `org.bluez `system service.

* adapterId : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The internal ID of the adapter (e.g., “hci0”).

* devices : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [BluetoothDevice ](/docs/v0.3.0/types/Quickshell.Bluetooth/BluetoothDevice)>
readonly

Bluetooth devices connected to this adapter.

* pairable : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

True if the adapter is accepting incoming pairing requests.

This only affects incoming pairing requests and should typically only be changed by system settings applications. Defaults to true.

* pairableTimeout : [int ](https://doc.qt.io/qt-6/qml-int.html)

Timeout in seconds for how long the adapter stays pairable after [pairable ](#pairable)is set to true. A value of 0 means the adapter stays pairable forever. Defaults to 0.

* discoverable : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

True if the adapter can be discovered by other bluetooth devices.

* discovering : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

True if the adapter is scanning for new devices.

* discoverableTimeout : [int ](https://doc.qt.io/qt-6/qml-int.html)

Timeout in seconds for how long the adapter stays discoverable after [discoverable ](#discoverable)is set to true. A value of 0 means the adapter stays discoverable forever.

* enabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

True if the adapter is currently enabled. More detailed state is available from [state ](#state).

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

System provided name of the adapter. See [adapterId ](#adapterId)for the internal identifier.

* state : [BluetoothAdapterState ](/docs/v0.3.0/types/Quickshell.Bluetooth/BluetoothAdapterState)
readonly

Detailed power state of the adapter.

* [dbusPath ](#dbusPath)

* [adapterId ](#adapterId)

* [devices ](#devices)

* [pairable ](#pairable)

* [pairableTimeout ](#pairableTimeout)

* [discoverable ](#discoverable)

* [discovering ](#discovering)

* [discoverableTimeout ](#discoverableTimeout)

* [enabled ](#enabled)

* [name ](#name)

* [state ](#state)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
