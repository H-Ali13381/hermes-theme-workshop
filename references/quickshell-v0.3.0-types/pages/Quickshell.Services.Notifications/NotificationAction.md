## NotificationAction : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.Notifications `
See [Notification.actions ](/docs/v0.3.0/types/Quickshell.Services.Notifications/Notification#actions).

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* identifier : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The identifier of the action.

When [Notification.hasActionIcons ](/docs/v0.3.0/types/Quickshell.Services.Notifications/Notification#hasActionIcons)is true, this property will be an icon name. When it is false, this property is irrelevant.

* text : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The localized text that should be displayed on a button.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* invoke ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Invoke the action. If [Notification.resident ](/docs/v0.3.0/types/Quickshell.Services.Notifications/Notification#resident)is false it will be dismissed.

* [identifier ](#identifier)

* [text ](#text)

* [invoke ](#invoke)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
