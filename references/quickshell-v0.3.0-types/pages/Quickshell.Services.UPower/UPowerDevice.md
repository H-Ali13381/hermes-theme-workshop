## UPowerDevice : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.UPower `
A device exposed through the UPower system service.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* isLaptopBattery : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the device is a laptop battery or not. Use this to check if your device is a valid battery.

This will be equivalent to [type ](#type)== Battery && [powerSupply ](#powerSupply)== true.

* ready : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If device statistics have been queried for this device yet. This will be true for all devices returned from [UPower.devices ](/docs/v0.3.0/types/Quickshell.Services.UPower/UPower#devices), but not the default device, which may be returned before it is ready to avoid returning null.

* timeToEmpty : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Estimated time until the device is fully discharged, in seconds.

Will be set to `0 `if charging.

* nativePath : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Native path of the device specific to your OS.

* type : [DeviceType ](/docs/v0.3.0/types/Quickshell.Networking/DeviceType)
readonly

The type of device.

* powerSupply : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the device is a power supply for your computer and can provide charge.

* healthSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* timeToFull : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Estimated time until the device is fully charged, in seconds.

Will be set to `0 `if discharging.

* energyCapacity : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Maximum energy capacity of the device in watt-hours

* state : [UPowerDeviceState ](/docs/v0.3.0/types/Quickshell.Services.UPower/UPowerDeviceState)
readonly

Current state of the device.

* iconName : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Name of the icon representing the current state of the device, or an empty string if not provided.

* model : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Model name of the device. Unlikely to be useful for internal devices.

* isPresent : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the power source is present in the bay or slot, useful for hot-removable batteries.

If the device `type `is not `Battery `, then the property will be invalid.

* percentage : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Current charge level as a percentage.

This would be equivalent to [energy ](#energy)/ [energyCapacity ](#energyCapacity).

* energy : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Current energy level of the device in watt-hours.

* changeRate : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Rate of energy change in watts (positive when charging, negative when discharging).

* healthPercentage : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Health of the device as a percentage of its original health.

* [isLaptopBattery ](#isLaptopBattery)

* [ready ](#ready)

* [timeToEmpty ](#timeToEmpty)

* [nativePath ](#nativePath)

* [type ](#type)

* [powerSupply ](#powerSupply)

* [healthSupported ](#healthSupported)

* [timeToFull ](#timeToFull)

* [energyCapacity ](#energyCapacity)

* [state ](#state)

* [iconName ](#iconName)

* [model ](#model)

* [isPresent ](#isPresent)

* [percentage ](#percentage)

* [energy ](#energy)

* [changeRate ](#changeRate)

* [healthPercentage ](#healthPercentage)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
