## WifiNetwork : [Network ](/docs/v0.3.0/types/Quickshell.Networking/Network)
uncreatable

`import Quickshell.Networking `
WiFi subtype of [Network ](/docs/v0.3.0/types/Quickshell.Networking/Network).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* security : [WifiSecurityType ](/docs/v0.3.0/types/Quickshell.Networking/WifiSecurityType)
readonly

The security type of the wifi network.

* signalStrength : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

The current signal strength of the network, from 0.0 to 1.0.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* connectWithPsk ( psk ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

psk : [string ](https://doc.qt.io/qt-6/qml-string.html)

Attempt to connect to the network with the given PSK. If the PSK is wrong, a [Network.connectionFailed() ](/docs/v0.3.0/types/Quickshell.Networking/Network#connectionFailed)signal will be emitted with `NoSecrets `.

The networking backend may store the PSK for future use with [Network.connect() ](/docs/v0.3.0/types/Quickshell.Networking/Network#connect). As such, calling that function first is recommended to avoid having to show a prompt if not required.

NOTE

PSKs should only be provided when the [security ](#security)is one of `WpaPsk `, `Wpa2Psk `, or `Sae `.

* [security ](#security)

* [signalStrength ](#signalStrength)

* [connectWithPsk ](#connectWithPsk)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
