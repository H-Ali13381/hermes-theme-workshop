## PwLinkGroup : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.Pipewire `
A group of connections between pipewire nodes, one per source->target pair.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* target : [PwNode ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwNode)
readonly

The node that is receiving information. (the sink)

* state : [PwLinkState ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwLinkState)
readonly

The current state of the link group.

WARNING

This property is invalid unless the node is bound using [PwObjectTracker ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwObjectTracker).

* source : [PwNode ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwNode)
readonly

The node that is sending information. (the source)

* [target ](#target)

* [state ](#state)

* [source ](#source)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
