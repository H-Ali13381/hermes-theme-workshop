## WlrKeyboardFocus : WlrKeyboardFocus

`import Quickshell.Wayland `
See [WlrLayershell.keyboardFocus ](/docs/v0.3.0/types/Quickshell.Wayland/WlrLayershell#keyboardFocus).

## Variants

* Exclusive

Exclusive access to the keyboard, locking out all other windows.

WARNING

You CANNOT use this to make a secure lock screen.

If you want to make a lock screen, use [WlSessionLock ](/docs/v0.3.0/types/Quickshell.Wayland/WlSessionLock).

* OnDemand

Access to the keyboard as determined by the operating system.

WARNING

On some systems, `OnDemand `may cause the shell window to retain focus over another window unexpectedly. You should try `None `if you experience issues.

* None

No keyboard input will be accepted.

* [Exclusive ](#Exclusive)

* [OnDemand ](#OnDemand)

* [None ](#None)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
