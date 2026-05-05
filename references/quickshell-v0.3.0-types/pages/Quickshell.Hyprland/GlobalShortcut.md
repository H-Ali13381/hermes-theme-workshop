## GlobalShortcut : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Hyprland `
Global shortcut implemented with [hyprland_global_shortcuts_v1 ](https://github.com/hyprwm/hyprland-protocols/blob/main/protocols/hyprland-global-shortcuts-v1.xml).

You can use this within hyprland as a global shortcut:

```
`bind = <modifiers>, <key>, global, <appid>:<name>
`
```

See [the wiki ](https://wiki.hyprland.org/Configuring/Binds/#dbus-global-shortcuts)for details.

WARNING

The shortcuts protocol does not allow duplicate appid + name pairs. Within a single instance of quickshell this is handled internally, and both users will be notified, but multiple instances of quickshell or XDPH may collide.

If that happens, whichever client that tries to register the shortcuts last will crash.

NOTE

This type does not use the xdg-desktop-portal global shortcuts protocol, as it is not fully functional without flatpak and would cause a considerably worse user experience from other limitations. It will only work with Hyprland. Note that, as this type bypasses xdg-desktop-portal, XDPH is not required.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* triggerDescription : [string ](https://doc.qt.io/qt-6/qml-string.html)

Have not seen this used ever, but included for completeness. Safe to ignore.

* name : [string ](https://doc.qt.io/qt-6/qml-string.html)

The name of the shortcut. You cannot change this at runtime.

* appid : [string ](https://doc.qt.io/qt-6/qml-string.html)

The appid of the shortcut. Defaults to `quickshell `. You cannot change this at runtime.

If you have more than one shortcut we recommend subclassing GlobalShortcut to set this.

* description : [string ](https://doc.qt.io/qt-6/qml-string.html)

The description of the shortcut that appears in `hyprctl globalshortcuts `. You cannot change this at runtime.

* pressed : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the keybind is currently pressed.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* released ( ) [](/docs/configuration/qml-overview#-signals)

Fired when the keybind is released.

* pressed ( ) [](/docs/configuration/qml-overview#-signals)

Fired when the keybind is pressed.

* [triggerDescription ](#triggerDescription)

* [name ](#name)

* [appid ](#appid)

* [description ](#description)

* [pressed ](#pressed)

* [released ](#released)

* [pressed ](#pressed)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
