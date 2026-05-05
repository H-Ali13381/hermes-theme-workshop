## ShellScreen : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell `
Monitor object useful for setting the monitor for a [QsWindow ](/docs/v0.3.0/types/Quickshell/QsWindow)or querying information about the monitor.

WARNING

If the monitor is disconnected, then any stored copies of its ShellMonitor will be marked as dangling and all properties will return default values. Reconnecting the monitor will not reconnect it to the ShellMonitor object.

Due to some technical limitations, it was not possible to reuse the native qml [Screen ](https://doc.qt.io/qt-6/qml-qtquick-screen.html)type.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* y : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

No details provided

* logicalPixelDensity : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

The number of device-independent (scaled) pixels per millimeter.

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The name of the screen as seen by the operating system.

Usually something like `DP-1 `, `HDMI-1 `, `eDP-1 `.

* primaryOrientation : [unknown ](#unknown)
readonly

No details provided

* height : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

No details provided

* orientation : [unknown ](#unknown)
readonly

No details provided

* model : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The model of the screen as seen by the operating system.

* devicePixelRatio : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

The ratio between physical pixels and device-independent (scaled) pixels.

* physicalPixelDensity : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

The number of physical pixels per millimeter.

* serialNumber : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The serial number of the screen as seen by the operating system.

* x : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

No details provided

* width : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

No details provided

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* toString ( ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

No details provided

* [y ](#y)

* [logicalPixelDensity ](#logicalPixelDensity)

* [name ](#name)

* [primaryOrientation ](#primaryOrientation)

* [height ](#height)

* [orientation ](#orientation)

* [model ](#model)

* [devicePixelRatio ](#devicePixelRatio)

* [physicalPixelDensity ](#physicalPixelDensity)

* [serialNumber ](#serialNumber)

* [x ](#x)

* [width ](#width)

* [toString ](#toString)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
