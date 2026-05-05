## Notification : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.Notifications `
A notification emitted by a NotificationServer.

NOTE

This type is [Retainable ](/docs/v0.3.0/types/Quickshell/Retainable). It can be retained after destruction if necessary.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* id : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

Id of the notification as given to the client.

* desktopEntry : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The name of the sender’s desktop entry or "" if none was supplied.

* tracked : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the notification is tracked by the notification server.

Setting this property to false is equivalent to calling [dismiss() ](#dismiss).

* body : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

No details provided

* image : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

An image associated with the notification.

This image is often something like a profile picture in instant messaging applications.

* expireTimeout : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

Time in seconds the notification should be valid for

* transient : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, the notification should skip any kind of persistence function like a notification area.

* appName : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The sending application’s name.

* lastGeneration : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If this notification was carried over from the last generation when quickshell reloaded.

Notifications from the last generation will only be emitted if [NotificationServer.keepOnReload ](/docs/v0.3.0/types/Quickshell.Services.Notifications/NotificationServer#keepOnReload)is true.

* actions : [list ](https://doc.qt.io/qt-6/qml-list.html)< [NotificationAction ](/docs/v0.3.0/types/Quickshell.Services.Notifications/NotificationAction)>
readonly

Actions that can be taken for this notification.

* resident : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, the notification will not be destroyed after an action is invoked.

* appIcon : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The sending application’s icon. If none was provided, then the icon from an associated desktop entry will be retrieved. If none was found then "".

* hints : [unknown ](#unknown)
readonly

All hints sent by the client application as a javascript object. Many common hints are exposed via other properties.

* inlineReplyPlaceholder : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The placeholder text/button caption for the inline reply.

* hasInlineReply : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If true, the notification has an inline reply action.

A quick reply text field should be displayed and the reply can be sent using [sendInlineReply() ](#sendInlineReply).

* urgency : [NotificationUrgency ](/docs/v0.3.0/types/Quickshell.Services.Notifications/NotificationUrgency)
readonly

No details provided

* hasActionIcons : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If actions associated with this notification have icons available.

See [NotificationAction.identifier ](/docs/v0.3.0/types/Quickshell.Services.Notifications/NotificationAction#identifier)for details.

* summary : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The image associated with this notification, or "" if none.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* dismiss ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Destroy the notification and hint to the remote application that it was explicitly closed by the user.

* expire ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Destroy the notification and hint to the remote application that it has timed out an expired.

* sendInlineReply ( replyText ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

replyText : [string ](https://doc.qt.io/qt-6/qml-string.html)

Send an inline reply to the notification with an inline reply action.

WARNING

This method can only be called if [hasInlineReply ](#hasInlineReply)is true and the server has [NotificationServer.inlineReplySupported ](/docs/v0.3.0/types/Quickshell.Services.Notifications/NotificationServer#inlineReplySupported)set to true.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* closed ( reason ) [](/docs/configuration/qml-overview#-signals)

reason : [NotificationCloseReason ](/docs/v0.3.0/types/Quickshell.Services.Notifications/NotificationCloseReason)

Sent when a notification has been closed.

The notification object will be destroyed as soon as all signal handlers exit.

* [id ](#id)

* [desktopEntry ](#desktopEntry)

* [tracked ](#tracked)

* [body ](#body)

* [image ](#image)

* [expireTimeout ](#expireTimeout)

* [transient ](#transient)

* [appName ](#appName)

* [lastGeneration ](#lastGeneration)

* [actions ](#actions)

* [resident ](#resident)

* [appIcon ](#appIcon)

* [hints ](#hints)

* [inlineReplyPlaceholder ](#inlineReplyPlaceholder)

* [hasInlineReply ](#hasInlineReply)

* [urgency ](#urgency)

* [hasActionIcons ](#hasActionIcons)

* [summary ](#summary)

* [dismiss ](#dismiss)

* [expire ](#expire)

* [sendInlineReply ](#sendInlineReply)

* [closed ](#closed)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
