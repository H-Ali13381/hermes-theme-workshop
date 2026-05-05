## Networking : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
singleton

`import Quickshell.Networking `
An interface to a network backend (currently only NetworkManager), which can be used to view, configure, and connect to various networks.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* wifiHardwareEnabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

State of the rfkill hardware block of all wireless devices.

* wifiEnabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Switch for the rfkill software block of all wireless devices.

* canCheckConnectivity : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

True if the [backend ](#backend)supports connectivity checks.

* connectivityCheckEnabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

True if connectivity checking is enabled.

* backend : [NetworkBackendType ](/docs/v0.3.0/types/Quickshell.Networking/NetworkBackendType)
readonly

The backend being used to power the Network service.

* devices : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [NetworkDevice ](/docs/v0.3.0/types/Quickshell.Networking/NetworkDevice)>
readonly

A list of all network devices. Networks are exposed through their respective devices.

* connectivity : [NetworkConnectivity ](/docs/v0.3.0/types/Quickshell.Networking/NetworkConnectivity)
readonly

The result of the last connectivity check.

Connectivity checks may require additional configuration depending on your distro.

NOTE

This property can be used to determine if network access is restricted or gated behind a captive portal.

If checking for captive portals, [checkConnectivity() ](#checkConnectivity)should be called after the portal is dismissed to update this property.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* checkConnectivity ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Re-check the network connectivity state immediately.

NOTE

This should be invoked after a user dismisses a web browser that was opened to authenticate via a captive portal.

* [wifiHardwareEnabled ](#wifiHardwareEnabled)

* [wifiEnabled ](#wifiEnabled)

* [canCheckConnectivity ](#canCheckConnectivity)

* [connectivityCheckEnabled ](#connectivityCheckEnabled)

* [backend ](#backend)

* [devices ](#devices)

* [connectivity ](#connectivity)

* [checkConnectivity ](#checkConnectivity)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
