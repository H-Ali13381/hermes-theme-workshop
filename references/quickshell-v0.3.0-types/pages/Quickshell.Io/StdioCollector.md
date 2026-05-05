## StdioCollector : [DataStreamParser ](/docs/v0.3.0/types/Quickshell.Io/DataStreamParser)

`import Quickshell.Io `
StdioCollector collects all process output into a buffer exposed as [text ](#text)or [data ](#data).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* data : [unknown ](#unknown)
readonly

The stdio buffer exposed as an [ArrayBuffer ](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer). if [waitForEnd ](#waitForEnd)is true, this will not change until the stream ends.

* waitForEnd : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If true, [text ](#text)and [data ](#data)will not be updated until the stream ends. Defaults to true.

* text : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The stdio buffer exposed as text. if [waitForEnd ](#waitForEnd)is true, this will not change until the stream ends.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* streamFinished ( ) [](/docs/configuration/qml-overview#-signals)

No details provided

* [data ](#data)

* [waitForEnd ](#waitForEnd)

* [text ](#text)

* [streamFinished ](#streamFinished)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
