## NetworkConnectivity : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
enum

`import Quickshell.Networking `
The degree to which the host can reach the internet.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* toString ( conn ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

conn : [NetworkConnectivity ](/docs/v0.3.0/types/Quickshell.Networking/NetworkConnectivity)
No details provided

## Variants

* Portal

The internet connection is hijacked by a captive portal gateway. This indicates the shell should open a sandboxed web browser window for the purpose of authenticating to a gateway.

* Full

The host is connected to a network and appears to be able to reach the full internet.

* Limited

The host is connected to a network but does not appear to be able to reach the full internet.

* Unknown

Network connectivity is unknown. This means the connectivity checks are disabled or have not run yet.

* None

The host is not connected to any network.

* [toString ](#toString)

* [Portal ](#Portal)

* [Full ](#Full)

* [Limited ](#Limited)

* [Unknown ](#Unknown)

* [None ](#None)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
