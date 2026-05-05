## DesktopEntry : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell `
A desktop entry. See [DesktopEntries ](/docs/v0.3.0/types/Quickshell/DesktopEntries)for details.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* icon : [string ](https://doc.qt.io/qt-6/qml-string.html)

Name of the icon associated with this application. May be empty.

* noDisplay : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If true, this application should not be displayed in menus and launchers.

* command : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>

The parsed `Exec `command in the desktop entry.

The entry can be run with [execute() ](#execute), or by using this command in [Quickshell.execDetached() ](/docs/v0.3.0/types/Quickshell/Quickshell#execDetached)or [Process ](/docs/v0.3.0/types/Quickshell.Io/Process). If used in `execDetached `or a `Process `, [workingDirectory ](#workingDirectory)should also be passed to the invoked process. See [execute() ](#execute)for details.

NOTE

The provided command does not invoke a terminal even if [runInTerminal ](#runInTerminal)is true.

* categories : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>

No details provided

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)

No details provided

* runInTerminal : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the application should run in a terminal.

* actions : [list ](https://doc.qt.io/qt-6/qml-list.html)< [DesktopAction ](/docs/v0.3.0/types/Quickshell/DesktopAction)>
readonly

No details provided

* keywords : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>

No details provided

* id : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

* startupClass : [string ](https://doc.qt.io/qt-6/qml-string.html)

Initial class or app id the app intends to use. May be useful for matching running apps to desktop entries.

* execString : [string ](https://doc.qt.io/qt-6/qml-string.html)

The raw `Exec `string from the desktop entry.

WARNING

This cannot be reliably run as a command. See [command ](#command)for one you can run.

* genericName : [string ](https://doc.qt.io/qt-6/qml-string.html)

Short description of the application, such as “Web Browser”. May be empty.

* comment : [string ](https://doc.qt.io/qt-6/qml-string.html)

Long description of the application, such as “View websites on the internet”. May be empty.

* workingDirectory : [string ](https://doc.qt.io/qt-6/qml-string.html)

The working directory to execute from.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* execute ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Run the application. Currently ignores [runInTerminal ](#runInTerminal)and field codes.

This is equivalent to calling [Quickshell.execDetached() ](/docs/v0.3.0/types/Quickshell/Quickshell#execDetached)with [command ](#command)and [DesktopEntry.workingDirectory ](/docs/v0.3.0/types/Quickshell/DesktopEntry#workingDirectory)as shown below:

```
`Quickshell.execDetached({
  command: desktopEntry.command,
  workingDirectory: desktopEntry.workingDirectory,
});`
```

* [icon ](#icon)

* [noDisplay ](#noDisplay)

* [command ](#command)

* [categories ](#categories)

* [name ](#name)

* [runInTerminal ](#runInTerminal)

* [actions ](#actions)

* [keywords ](#keywords)

* [id ](#id)

* [startupClass ](#startupClass)

* [execString ](#execString)

* [genericName ](#genericName)

* [comment ](#comment)

* [workingDirectory ](#workingDirectory)

* [execute ](#execute)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
