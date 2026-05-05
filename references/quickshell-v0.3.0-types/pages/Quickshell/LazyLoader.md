## LazyLoader : [Reloadable ](/docs/v0.3.0/types/Quickshell/Reloadable)

`import Quickshell `
The LazyLoader can be used to prepare components that don’t need to be created immediately, such as windows that aren’t visible until triggered by another action. It works on creating the component in the gaps between frame rendering to prevent blocking the interface thread. It can also be used to preserve memory by loading components only when you need them and unloading them afterward.

Note that when reloading the UI due to changes, lazy loaders will always load synchronously so windows can be reused.

#### Example

The following example creates a PopupWindow asynchronously as the bar loads. This means the bar can be shown onscreen before the popup is ready, however trying to show the popup before it has finished loading in the background will cause the UI thread to block.

```
`import QtQuick
import QtQuick.Controls
import Quickshell

ShellRoot {
  PanelWindow {
    id: window
    height: 50

    anchors {
      bottom: true
      left: true
      right: true
    }

    LazyLoader {
      id: popupLoader

      // start loading immediately
      loading: true

      // this window will be loaded in the background during spare
      // frame time unless active is set to true, where it will be
      // loaded in the foreground
      PopupWindow {
        // position the popup above the button
        parentWindow: window
        relativeX: window.width / 2 - width / 2
        relativeY: -height

        // some heavy component here

        width: 200
        height: 200
      }
    }

    Button {
      anchors.centerIn: parent
      text: "show popup"

      // accessing popupLoader.item will force the loader to
      // finish loading on the UI thread if it isn't finished yet.
      onClicked: popupLoader.item.visible = !popupLoader.item.visible
    }
  }
}`
```

WARNING

Components that internally load other components must explicitly support asynchronous loading to avoid blocking.

Notably, [Variants ](/docs/v0.3.0/types/Quickshell/Variants)does not corrently support asynchronous loading, meaning using it inside a LazyLoader will block similarly to not having a loader to start with.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the component is fully loaded.

Setting this property to `true `will force the component to load to completion, blocking the UI, and setting it to `false `will destroy the component, requiring it to be loaded again.

See also: [activeAsync ](#activeAsync).

* activeAsync : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the component is fully loaded.

Setting this property to true will asynchronously load the component similarly to [loading ](#loading). Reading it or setting it to false will behanve the same as [active ](#active).

* item : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
readonly

The fully loaded item if the loader is [loading ](#loading)or [active ](#active), or `null `if neither [loading ](#loading)nor [active ](#active).

Note that the item is owned by the LazyLoader, and destroying the LazyLoader will destroy the item.

WARNING

If you access the `item `of a loader that is currently loading, it will block as if you had set `active `to true immediately beforehand.

You can instead set [loading ](#loading)and listen to [activeChanged() ](#activeChanged)signal to ensure loading happens asynchronously.

* loading : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the loader is actively loading.

If the component is not loaded, setting this property to true will start loading it asynchronously. If the component is already loaded, setting this property has no effect.

See also: [activeAsync ](#activeAsync).

* source : [string ](https://doc.qt.io/qt-6/qml-string.html)

The URI to load the component from. Mutually exclusive to [component ](#component).

* component : [Component ](https://doc.qt.io/qt-6/qml-qtqml-component.html)
default

The component to load. Mutually exclusive to [source ](#source).

* [active ](#active)

* [activeAsync ](#activeAsync)

* [item ](#item)

* [loading ](#loading)

* [source ](#source)

* [component ](#component)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
