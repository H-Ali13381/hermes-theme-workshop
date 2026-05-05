## IconImage : [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)

`import Quickshell.Widgets `
This is a specialization of [Image ](https://doc.qt.io/qt-6/qml-qtquick-image.html)configured for icon-style images, designed to make it easier to use correctly. If you need more control, use [Image ](https://doc.qt.io/qt-6/qml-qtquick-image.html)directly.

The image’s aspect raito is assumed to be 1:1. If it is not 1:1, padding will be added to make it 1:1. This is currently applied before the actual aspect ratio of the image is taken into account, and may change in a future release.

You should use it for:

* Icons for custom buttons

* Status indicator icons

* System tray icons

* Things similar to the above.

Do not use it for:

* Big images

* Images that change size frequently

* Anything that doesn’t feel like an icon.

NOTE

More information about many of these properties can be found in the documentation for [Image ](https://doc.qt.io/qt-6/qml-qtquick-image.html).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* backer : [Image ](https://doc.qt.io/qt-6/qml-qtquick-image.html)

The [Image ](https://doc.qt.io/qt-6/qml-qtquick-image.html)backing this object.

This is useful if you need to access more functionality than exposed by IconImage.

* source : [string ](https://doc.qt.io/qt-6/qml-string.html)

URL of the image. Defaults to an empty string. See [Image.source ](https://doc.qt.io/qt-6/qml-qtquick-image.html#source-prop).

* actualSize : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

The actual size the image will be displayed at.

* mipmap : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the image should be mipmap filtered. Defaults to false. See [Image.mipmap ](https://doc.qt.io/qt-6/qml-qtquick-image.html#mipmap-prop).

Try enabling this if your image is significantly scaled down and looks bad because of it.

* status : [unknown ](#unknown)

The load status of the image. See [Image.status ](https://doc.qt.io/qt-6/qml-qtquick-image.html#status-prop).

* implicitSize : [real ](https://doc.qt.io/qt-6/qml-real.html)

The suggested size of the image. This is used as a default for [Item.implicitWidth ](https://doc.qt.io/qt-6/qml-qtquick-item.html#implicitWidth-prop)and [Item.implicitHeight ](https://doc.qt.io/qt-6/qml-qtquick-item.html#implicitHeight-prop).

* asynchronous : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the image should be loaded asynchronously. Defaults to false. See [Image.asynchronous ](https://doc.qt.io/qt-6/qml-qtquick-image.html#asynchronous-prop).

* [backer ](#backer)

* [source ](#source)

* [actualSize ](#actualSize)

* [mipmap ](#mipmap)

* [status ](#status)

* [implicitSize ](#implicitSize)

* [asynchronous ](#asynchronous)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
