## DesktopAction : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell `
An action of a [DesktopEntry ](/docs/v0.3.0/types/Quickshell/DesktopEntry).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)

No details provided

* icon : [string ](https://doc.qt.io/qt-6/qml-string.html)

No details provided

* execString : [string ](https://doc.qt.io/qt-6/qml-string.html)

The raw `Exec `string from the action.

WARNING

This cannot be reliably run as a command. See [command ](#command)for one you can run.

* command : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>

The parsed `Exec `command in the action.

The entry can be run with [execute() ](#execute), or by using this command in [Quickshell.execDetached() ](/docs/v0.3.0/types/Quickshell/Quickshell#execDetached)or [Process ](/docs/v0.3.0/types/Quickshell.Io/Process). If used in `execDetached `or a `Process `, [DesktopEntry.workingDirectory ](/docs/v0.3.0/types/Quickshell/DesktopEntry#workingDirectory)should also be passed to the invoked process.

NOTE

The provided command does not invoke a terminal even if [runInTerminal ](#runInTerminal)is true.

* id : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* execute ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Run the application. Currently ignores [DesktopEntry.runInTerminal ](/docs/v0.3.0/types/Quickshell/DesktopEntry#runInTerminal)and field codes.

This is equivalent to calling [Quickshell.execDetached() ](/docs/v0.3.0/types/Quickshell/Quickshell#execDetached)with [command ](#command)and [DesktopEntry.workingDirectory ](/docs/v0.3.0/types/Quickshell/DesktopEntry#workingDirectory).

* [name ](#name)

* [icon ](#icon)

* [execString ](#execString)

* [command ](#command)

* [id ](#id)

* [execute ](#execute)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
