## SystemClock : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
enum

`import Quickshell `
SystemClock is a view into the system’s clock. It updates at hour, minute, or second intervals depending on [precision ](#precision).

# Examples

```
`SystemClock {
  id: clock
  precision: SystemClock.Seconds
}

[Text](https://doc.qt.io/qt-6/qml-qtquick-text.html) {
  text: Qt.formatDateTime(clock.date, "hh:mm:ss - yyyy-MM-dd")
}`
```

WARNING

Clock updates will trigger within 50ms of the system clock changing, however this can be either before or after the clock changes (+-50ms). If you need a date object, use [date ](#date)instead of constructing a new one, or the time of the constructed object could be off by up to a second.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* precision : [SystemClock ](/docs/v0.3.0/types/Quickshell/SystemClock)

The precision the clock should measure at. Defaults to `SystemClock.Seconds `.

* hours : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

The current hour.

* date : [date ](https://doc.qt.io/qt-6/qml-date.html)
readonly

The current date and time.

TIP

You can use [Qt.formatDateTime() ](https://doc.qt.io/qt-6/qml-qtqml-qt.html#formatDateTime-method)to get the time as a string in your format of choice.

* minutes : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

The current minute, or 0 if [precision ](#precision)is `SystemClock.Hours `.

* seconds : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

The current second, or 0 if [precision ](#precision)is `SystemClock.Hours `or `SystemClock.Minutes `.

* enabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the clock should update. Defaults to true.

Setting enabled to false pauses the clock.

## Variants

* Seconds

No details provided

* Hours

No details provided

* Minutes

No details provided

* [precision ](#precision)

* [hours ](#hours)

* [date ](#date)

* [minutes ](#minutes)

* [seconds ](#seconds)

* [enabled ](#enabled)

* [Seconds ](#Seconds)

* [Hours ](#Hours)

* [Minutes ](#Minutes)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
