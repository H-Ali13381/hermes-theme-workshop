## NMSettings : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Networking `
A NetworkManager connection settings profile.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* uuid : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

A universally unique identifier for the connection.

* id : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The human-readable unique identifier for the connection.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* clearSecrets ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Clear all of the secrets belonging to the settings.

* forget ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Delete the settings.

* read ( ) : [unknown ](#unknown)

Get the settings map describing this network configuration.

NOTE

This will never include any secrets required for connection to the network, as those are often protected.

* write ( settings ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

settings : [](#unknown)

Update the connection with new settings and save the connection to disk. Only changed fields need to be included. Writing a setting to `null `will remove the setting or reset it to its default.

NOTE

Secrets may be part of the update request, and will be either stored in persistent storage or sent to a Secret Agent for storage, depending on the flags associated with each secret.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* loaded ( ) [](/docs/configuration/qml-overview#-signals)

No details provided

* settingsChanged ( settings ) [](/docs/configuration/qml-overview#-signals)

settings : [](#unknown)
No details provided

* [uuid ](#uuid)

* [id ](#id)

* [clearSecrets ](#clearSecrets)

* [forget ](#forget)

* [read ](#read)

* [write ](#write)

* [loaded ](#loaded)

* [settingsChanged ](#settingsChanged)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
