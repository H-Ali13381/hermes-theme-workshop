## BackgroundEffect : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Wayland `
Applies background blur behind a [QsWindow ](/docs/v0.3.0/types/Quickshell/QsWindow)or subclass, as an attached object, using the [ext-background-effect-v1 ](https://wayland.app/protocols/ext-background-effect-v1)Wayland protocol.

NOTE

Using a background effect requires the compositor support the [ext-background-effect-v1 ](https://wayland.app/protocols/ext-background-effect-v1)protocol.

#### Example

```
`[PanelWindow](/docs/v0.3.0/types/Quickshell/PanelWindow) {
  id: root
  color: "#80000000"

  BackgroundEffect.blurRegion: Region { item: root.contentItem }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* blurRegion : [Region ](/docs/v0.3.0/types/Quickshell/Region)

Region to blur behind the surface. Set to null to remove blur.

* [blurRegion ](#blurRegion)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
