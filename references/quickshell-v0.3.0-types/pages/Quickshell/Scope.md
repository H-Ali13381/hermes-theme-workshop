## Scope : [Reloadable ](/docs/v0.3.0/types/Quickshell/Reloadable)

`import Quickshell `
Convenience type equivalent to setting [Reloadable.reloadableId ](/docs/v0.3.0/types/Quickshell/Reloadable#reloadableId)for all children.

Note that this does not work for visible [Item ](https://doc.qt.io/qt-6/qml-qtquick-item.html)s (all widgets).

```
`ShellRoot {
  Variants {
    variants: ...

    Scope {
      // everything in here behaves the same as if it was defined
      // directly in `Variants` reload-wise.
    }
  }
}`
```

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* children : [list ](https://doc.qt.io/qt-6/qml-list.html)< [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)>
default readonly

No details provided

* [children ](#children)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
