## PwNodeLinkTracker : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Services.Pipewire `
Tracks non-monitor link connections to a given node.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* node : [PwNode ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwNode)

The node to track connections to.

* linkGroups : [list ](https://doc.qt.io/qt-6/qml-list.html)< [PwLinkGroup ](/docs/v0.3.0/types/Quickshell.Services.Pipewire/PwLinkGroup)>
readonly

Link groups connected to the given node, excluding monitors.

If the node is a sink, links which target the node will be tracked. If the node is a source, links which source the node will be tracked.

* [node ](#node)

* [linkGroups ](#linkGroups)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
