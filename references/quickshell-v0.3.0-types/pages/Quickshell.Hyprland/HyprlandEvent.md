## HyprlandEvent : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Hyprland `
Live Hyprland IPC event. Holding this object after the signal handler exits is undefined as the event instance is reused.

Emitted by [Hyprland.rawEvent() ](/docs/v0.3.0/types/Quickshell.Hyprland/Hyprland#rawEvent).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The name of the event.

See [Hyprland Wiki: IPC ](https://wiki.hyprland.org/IPC/)for a list of events.

* data : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The unparsed data of the event.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* parse ( argumentCount ) : [list ](https://doc.qt.io/qt-6/qml-list.html)

argumentCount : [int ](https://doc.qt.io/qt-6/qml-int.html)

Parse this event with a known number of arguments.

Argument count is required as some events can contain commas in the last argument, which can be ignored as long as the count is known.

* [name ](#name)

* [data ](#data)

* [parse ](#parse)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
