## ColorQuantizer : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell `
A color quantization utility used for getting prevalent colors in an image, by averaging out the image’s color data recursively.

#### Example

```
`ColorQuantizer {
  id: colorQuantizer
  source: Qt.resolvedUrl("./yourImage.png")
  depth: 3 // Will produce 8 colors (2³)
  rescaleSize: 64 // Rescale to 64x64 for faster processing
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* depth : [real ](https://doc.qt.io/qt-6/qml-real.html)

Max depth for the color quantization. Each level of depth represents another binary split of the color space

* imageRect : [rect ](https://doc.qt.io/qt-6/qml-rect.html)

Rectangle that the source image is cropped to.

Can be set to `undefined `to reset.

* source : [unknown ](#unknown)

Path to the image you’d like to run the color quantization on.

* colors : [list ](https://doc.qt.io/qt-6/qml-list.html)< [color ](https://doc.qt.io/qt-6/qml-color.html)>
readonly

Access the colors resulting from the color quantization performed.

NOTE

The amount of colors returned from the quantization is determined by the property depth, specifically 2ⁿ where n is the depth.

* rescaleSize : [real ](https://doc.qt.io/qt-6/qml-real.html)

The size to rescale the image to, when rescaleSize is 0 then no scaling will be done.

NOTE

Results from color quantization doesn’t suffer much when rescaling, it’s recommended to rescale, otherwise the quantization process will take much longer.

* [depth ](#depth)

* [imageRect ](#imageRect)

* [source ](#source)

* [colors ](#colors)

* [rescaleSize ](#rescaleSize)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
