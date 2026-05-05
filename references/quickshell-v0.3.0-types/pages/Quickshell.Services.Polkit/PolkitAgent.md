## PolkitAgent : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Services.Polkit `
## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* isRegistered : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates whether the agent registered successfully and is in use.

* path : [string ](https://doc.qt.io/qt-6/qml-string.html)

The D-Bus path that this agent listener will use.

If not set, a default of /org/quickshell/Polkit will be used.

* flow : [AuthFlow ](/docs/v0.3.0/types/Quickshell.Services.Polkit/AuthFlow)
readonly

The current authentication state if an authentication request is active.

Null when no authentication request is active.

* isActive : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates an ongoing authentication request.

If this is true, other properties such as [message ](#message)and [iconName ](#iconName)will also be populated with relevant information.

* [isRegistered ](#isRegistered)

* [path ](#path)

* [flow ](#flow)

* [isActive ](#isActive)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
