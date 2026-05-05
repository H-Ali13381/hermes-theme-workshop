## PersistentProperties : [Reloadable ](/docs/v0.3.0/types/Quickshell/Reloadable)

`import Quickshell `
PersistentProperties holds properties declated in it across a reload, which is often useful for things like keeping expandable popups open and styling them.

Below is an example of using `PersistentProperties `to keep track of the state of an expandable panel. When the configuration is reloaded, the `expanderOpen `property will be saved and the expandable panel will stay in the open/closed state.

```
`PersistentProperties {
  id: persist
  reloadableId: "persistedStates"

  property bool expanderOpen: false
}

Button {
  id: expanderButton
  anchors.centerIn: parent
  text: "toggle expander"
  onClicked: persist.expanderOpen = !persist.expanderOpen
}

Rectangle {
  anchors.top: expanderButton.bottom
  anchors.left: expanderButton.left
  anchors.right: expanderButton.right
  height: 100

  color: "lightblue"
  visible: persist.expanderOpen
}`
```

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* loaded ( ) [](/docs/configuration/qml-overview#-signals)

Called every time the reload stage completes. Will be called every time, including when nothing was loaded from an old instance.

* reloaded ( ) [](/docs/configuration/qml-overview#-signals)

Called every time the properties are reloaded. Will not be called if no old instance was loaded.

* [loaded ](#loaded)

* [reloaded ](#reloaded)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
