## UPower : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
singleton

`import Quickshell.Services.UPower `
An interface to the [UPower daemon ](https://upower.freedesktop.org), which can be used to view battery and power statistics for your computer and connected devices.

NOTE

The UPower daemon must be installed to use this service.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* devices : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [UPowerDevice ](/docs/v0.3.0/types/Quickshell.Services.UPower/UPowerDevice)>
readonly

All connected UPower devices.

* displayDevice : [UPowerDevice ](/docs/v0.3.0/types/Quickshell.Services.UPower/UPowerDevice)
readonly

UPower’s DisplayDevice for your system. Cannot be null, but might not be initialized (check [UPowerDevice.ready ](/docs/v0.3.0/types/Quickshell.Services.UPower/UPowerDevice#ready)if you need to know).

This is an aggregate device and not a physical one, meaning you will not find it in [devices ](#devices). It is typically the device that is used for displaying information in desktop environments.

* onBattery : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the system is currently running on battery power, or discharging.

* [devices ](#devices)

* [displayDevice ](#displayDevice)

* [onBattery ](#onBattery)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
