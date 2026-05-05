## PwNodeAudio : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.Pipewire `
Extra properties of a [PwNode ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwNode)if the node is an audio node.

See [PwNode.audio ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwNode#audio).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* channels : [list ](https://doc.qt.io/qt-6/qml-list.html)< [PwAudioChannel ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwAudioChannel)>
readonly

The audio channels present on the node.

WARNING

This property is invalid unless the node is bound using [PwObjectTracker ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwObjectTracker).

* muted : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the node is currently muted. Setting this property changes the mute state.

WARNING

This property is invalid unless the node is bound using [PwObjectTracker ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwObjectTracker).

* volumes : [list ](https://doc.qt.io/qt-6/qml-list.html)< [real ](https://doc.qt.io/qt-6/qml-real.html)>

The volumes of each audio channel individually. Each entry corresponds to the volume of the channel at the same index in [channels ](#channels). [volumes ](#volumes)and [channels ](#channels)will always be the same length.

WARNING

This property is invalid unless the node is bound using [PwObjectTracker ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwObjectTracker).

* volume : [real ](https://doc.qt.io/qt-6/qml-real.html)

The average volume over all channels of the node. Setting this property modifies the volume of all channels proportionately.

WARNING

This property is invalid unless the node is bound using [PwObjectTracker ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwObjectTracker).

* [channels ](#channels)

* [muted ](#muted)

* [volumes ](#volumes)

* [volume ](#volume)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
