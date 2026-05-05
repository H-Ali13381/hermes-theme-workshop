## Process : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Io `
#### Example

```
`Process {
  running: true
  command: [ "some-command", "arg" ]
  stdout: [StdioCollector](/docs/v0.3.0/types/Quickshell.Io/StdioCollector) {
    onStreamFinished: console.log(`line read: ${this.text}`)
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* stdout : [DataStreamParser ](/docs/v0.3.0/types/Quickshell.Io/DataStreamParser)

The parser for stdout. If the parser is null the process’s stdout channel will be closed and no further data will be read, even if a new parser is attached.

* running : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the process is currently running. Defaults to false.

Setting this property to true will start the process if command has at least one element. Setting it to false will send SIGTERM. To immediately kill the process, use [signal() ](#signal)with SIGKILL. The process will be killed when quickshell dies.

If you want to run the process in a loop, use the onRunningChanged signal handler to restart the process.

```
`Process {
  running: true
  onRunningChanged: if (!running) running = true
}`
```

NOTE

See [startDetached() ](#startDetached)to prevent the process from being killed by Quickshell if Quickshell is killed or the configuration is reloaded.

* clearEnvironment : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the process’s environment should be cleared prior to applying [environment ](#environment). Defaults to false.

If true, all environment variables will be removed before the [environment ](#environment)object is applied, meaning the variables listed will be the only ones visible to the process. This changes the behavior of `null `to pass in the system value of the variable if present instead of removing it.

```
`clearEnvironment: true
environment: ({
  ADDED: "value",
  PASSED_FROM_SYSTEM: null,
})`
```

If the process is already running changing this property will affect the next started process. If the property has been changed after starting a process it will return the new value, not the one for the currently running process.

* command : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>

The command to execute. Each argument is its own string, which means you don’t have to deal with quoting anything.

If the process is already running changing this property will affect the next started process. If the property has been changed after starting a process it will return the new value, not the one for the currently running process.

WARNING

This does not run command in a shell. All arguments to the command must be in separate values in the list, e.g. `["echo", "hello"] `and not `["echo hello"] `.

Additionally, shell scripts must be run by your shell, e.g. `["sh", "script.sh"] `instead of `["script.sh"] `unless the script has a shebang.

NOTE

You can use `["sh", "-c", <your command>] `to execute your command with the system shell.

* processId : [variant ](https://doc.qt.io/qt-6/qml-variant.html)
readonly

The process ID of the running process or `null `if [running ](#running)is false.

* environment : [unknown ](#unknown)

Environment of the executed process.

This is a javascript object (json). Environment variables can be added by setting them to a string and removed by setting them to null (except when [clearEnvironment ](#clearEnvironment)is true, in which case this behavior is inverted, see [clearEnvironment ](#clearEnvironment)for details).

```
`environment: ({
  ADDED: "value",
  REMOVED: null,
  "i'm different": "value",
})`
```

NOTE

You need to wrap the returned object in () otherwise it won’t parse due to javascript ambiguity.

If the process is already running changing this property will affect the next started process. If the property has been changed after starting a process it will return the new value, not the one for the currently running process.

* stderr : [DataStreamParser ](/docs/v0.3.0/types/Quickshell.Io/DataStreamParser)

The parser for stderr. If the parser is null the process’s stdout channel will be closed and no further data will be read, even if a new parser is attached.

* stdinEnabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If stdin is enabled. Defaults to false. If this property is false the process’s stdin channel will be closed and [write() ](#write)will do nothing, even if set back to true.

* workingDirectory : [string ](https://doc.qt.io/qt-6/qml-string.html)

The working directory of the process. Defaults to [quickshell’s working directory ](../../quickshell/quickshell#prop.workingDirectory).

If the process is already running changing this property will affect the next started process. If the property has been changed after starting a process it will return the new value, not the one for the currently running process.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* exec ( context ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

context : [](#unknown)

Launch a process with the given arguments, stopping any currently running process.

The context parameter can either be a list of command arguments or a JS object with the following fields:

* `command `: A list containing the command and all its arguments. See [Process.command ](/docs/v0.3.0/types/Quickshell.Io/Process#command).

* `environment `: Changes to make to the process environment. See [Process.environment ](/docs/v0.3.0/types/Quickshell.Io/Process#environment).

* `clearEnvironment `: Removes all variables from the environment if true.

* `workingDirectory `: The working directory the command should run in.

Passed parameters will change the values currently set in the process.

WARNING

This does not run command in a shell. All arguments to the command must be in separate values in the list, e.g. `["echo", "hello"] `and not `["echo hello"] `.

Additionally, shell scripts must be run by your shell, e.g. `["sh", "script.sh"] `instead of `["script.sh"] `unless the script has a shebang.

NOTE

You can use `["sh", "-c", <your command>] `to execute your command with the system shell.

Calling this function is equivalent to running:

```
`process.running = false;
process.command = ...
process.environment = ...
process.clearEnvironment = ...
process.workingDirectory = ...
process.running = true;`
```

* signal ( signal ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

signal : [int ](https://doc.qt.io/qt-6/qml-int.html)

Sends a signal to the process if [running ](#running)is true, otherwise does nothing.

* startDetached ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Launches an instance of the process detached from Quickshell.

The subprocess will not be tracked, [running ](#running)will be false, and the subprocess will not be killed by Quickshell.

This function is equivalent to [Quickshell.execDetached() ](/docs/v0.3.0/types/Quickshell/Quickshell#execDetached).

* write ( data ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

data : [string ](https://doc.qt.io/qt-6/qml-string.html)

Writes to the process’s stdin. Does nothing if [running ](#running)is false.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* exited ( exitCode, exitStatus ) [](/docs/configuration/qml-overview#-signals)

exitCode : [int ](https://doc.qt.io/qt-6/qml-int.html)exitStatus : [](#unknown)
No details provided

* started ( ) [](/docs/configuration/qml-overview#-signals)

No details provided

* [stdout ](#stdout)

* [running ](#running)

* [clearEnvironment ](#clearEnvironment)

* [command ](#command)

* [processId ](#processId)

* [environment ](#environment)

* [stderr ](#stderr)

* [stdinEnabled ](#stdinEnabled)

* [workingDirectory ](#workingDirectory)

* [exec ](#exec)

* [signal ](#signal)

* [startDetached ](#startDetached)

* [write ](#write)

* [exited ](#exited)

* [started ](#started)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
