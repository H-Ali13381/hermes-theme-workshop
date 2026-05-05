## NotificationServer : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Services.Notifications `
An implementation of the [Desktop Notifications Specification ](https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html)for receiving notifications from external applications.

The server does not advertise most capabilities by default. See the individual properties for details.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* imageSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the notification server should advertise that it supports images. Defaults to false.

* extraHints : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>

Extra hints to expose to notification clients.

* actionsSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If notification actions should be advertised as supported by the notification server. Defaults to false.

* actionIconsSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If notification actions should be advertised as supporting the display of icons. Defaults to false.

* bodySupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If notification body text should be advertised as supported by the notification server. Defaults to true.

Note that returned notifications are likely to return body text even if this property is false, as it is only a hint.

* inlineReplySupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the notification server should advertise that it supports inline replies. Defaults to false.

* persistenceSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the notification server should advertise that it can persist notifications in the background after going offscreen. Defaults to false.

* bodyImagesSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If notification body text should be advertised as supporting images as described in [the specification ](https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html#images)Defaults to false.

Note that returned notifications may still contain images if this property is false, as it is only a hint.

* trackedNotifications : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [Notification ](/docs/v0.3.0/types/Quickshell.Services.Notifications/Notification)>
readonly

All notifications currently tracked by the server.

* bodyHyperlinksSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If notification body text should be advertised as supporting hyperlinks as described in [the specification ](https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html#hyperlinks)Defaults to false.

Note that returned notifications may still contain hyperlinks if this property is false, as it is only a hint.

* bodyMarkupSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If notification body text should be advertised as supporting markup as described in [the specification] Defaults to false.

Note that returned notifications may still contain markup if this property is false, as it is only a hint. By default Text objects will try to render markup. To avoid this if any is sent, change [Text.textFormat ](https://doc.qt.io/qt-6/qml-qtquick-text.html#textFormat-prop)to `PlainText `.

* keepOnReload : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If notifications should be re-emitted when quickshell reloads. Defaults to true.

The [Notification.lastGeneration ](/docs/v0.3.0/types/Quickshell.Services.Notifications/Notification#lastGeneration)flag will be set on notifications from the prior generation for further filtering/handling.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* notification ( notification ) [](/docs/configuration/qml-overview#-signals)

notification : [Notification ](/docs/v0.3.0/types/Quickshell.Services.Notifications/Notification)

Sent when a notification is received by the server.

If this notification should not be discarded, set its `tracked `property to true.

* [imageSupported ](#imageSupported)

* [extraHints ](#extraHints)

* [actionsSupported ](#actionsSupported)

* [actionIconsSupported ](#actionIconsSupported)

* [bodySupported ](#bodySupported)

* [inlineReplySupported ](#inlineReplySupported)

* [persistenceSupported ](#persistenceSupported)

* [bodyImagesSupported ](#bodyImagesSupported)

* [trackedNotifications ](#trackedNotifications)

* [bodyHyperlinksSupported ](#bodyHyperlinksSupported)

* [bodyMarkupSupported ](#bodyMarkupSupported)

* [keepOnReload ](#keepOnReload)

* [notification ](#notification)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
