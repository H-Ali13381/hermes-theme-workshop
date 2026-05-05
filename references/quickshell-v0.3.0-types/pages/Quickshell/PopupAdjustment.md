## PopupAdjustment : PopupAdjustment

`import Quickshell `
Adjustment strategy for popups. See [PopupAnchor.adjustment ](/docs/v0.3.0/types/Quickshell/PopupAnchor#adjustment).

Adjustment flags can be combined with the `| `operator.

`Flip `will be applied first, then `Slide `, then `Resize `.

## Variants

* Slide

Alias for `SlideX | SlideY `.

* SlideX

If the X axis is constrained, the popup will slide along the X axis until it fits onscreen.

* SlideY

If the Y axis is constrained, the popup will slide along the Y axis until it fits onscreen.

* FlipY

If the Y axis is constrained, the popup will invert its vertical gravity if any.

* ResizeY

If the Y axis is constrained, the height of the popup will be reduced to fit on screen.

* Resize

Alias for `ResizeX | ResizeY `

* All

Alias for `Flip | Slide | Resize `.

* None

No details provided

* Flip

Alias for `FlipX | FlipY `.

* FlipX

If the X axis is constrained, the popup will invert its horizontal gravity if any.

* ResizeX

If the X axis is constrained, the width of the popup will be reduced to fit on screen.

* [Slide ](#Slide)

* [SlideX ](#SlideX)

* [SlideY ](#SlideY)

* [FlipY ](#FlipY)

* [ResizeY ](#ResizeY)

* [Resize ](#Resize)

* [All ](#All)

* [None ](#None)

* [Flip ](#Flip)

* [FlipX ](#FlipX)

* [ResizeX ](#ResizeX)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
