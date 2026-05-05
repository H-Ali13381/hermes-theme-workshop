## PwNodePeakMonitor : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Services.Pipewire `
Tracks volume peaks for a node across all its channels.

The peak monitor binds nodes similarly to [PwObjectTracker ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwObjectTracker)when enabled.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* peak : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Maximum value of [peaks ](#peaks).

* node : [PwNode ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwNode)

The node to monitor. Must be an audio node.

* enabled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If true, the monitor is actively capturing and computing peaks. Defaults to true.

* channels : [list ](https://doc.qt.io/qt-6/qml-list.html)< [PwAudioChannel ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwAudioChannel)>
readonly

Channel positions for the captured format. Length matches [peaks ](#peaks).

* peaks : [list ](https://doc.qt.io/qt-6/qml-list.html)< [real ](https://doc.qt.io/qt-6/qml-real.html)>
readonly

Per-channel peak noise levels (0.0-1.0). Length matches [channels ](#channels).

The channel’s volume does not affect this property.

* [peak ](#peak)

* [node ](#node)

* [enabled ](#enabled)

* [channels ](#channels)

* [peaks ](#peaks)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
