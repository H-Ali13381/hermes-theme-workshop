## PamContext : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)

`import Quickshell.Services.Pam `
Connection to pam. See [the module documentation ](../)for pam configuration advice.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* config : [string ](https://doc.qt.io/qt-6/qml-string.html)

The pam configuration to use. Defaults to “login”.

The configuration should name a file inside [configDirectory ](#configDirectory).

This property may not be set while [active ](#active)is true.

* active : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the pam context is actively performing an authentication.

Setting this value behaves exactly the same as calling [start() ](#start)and [abort() ](#abort).

* configDirectory : [string ](https://doc.qt.io/qt-6/qml-string.html)

The pam configuration directory to use. Defaults to “/etc/pam.d”.

The configuration directory is resolved relative to the current file if not an absolute path.

On FreeBSD this property is ignored as the pam configuration directory cannot be changed.

This property may not be set while [active ](#active)is true.

* responseVisible : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the user’s response should be visible. Only valid when [responseRequired ](#responseRequired)is true.

* responseRequired : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If pam currently wants a response.

Responses can be returned with the [respond() ](#respond)function.

* user : [string ](https://doc.qt.io/qt-6/qml-string.html)

The user to authenticate as. If unset the current user will be used.

This property may not be set while [active ](#active)is true.

* messageIsError : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the last message should be shown as an error.

* message : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The last message sent by pam.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* abort ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Abort a running authentication session.

* respond ( response ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

response : [string ](https://doc.qt.io/qt-6/qml-string.html)

Respond to pam.

May not be called unless [responseRequired ](#responseRequired)is true.

* start ( ) : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Start an authentication session. Returns if the session was started successfully.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* pamMessage ( ) [](/docs/configuration/qml-overview#-signals)

Emitted whenever pam sends a new message, after the change signals for `message `, `messageIsError `, and `responseRequired `.

* completed ( result ) [](/docs/configuration/qml-overview#-signals)

result : [PamResult ](/docs/v0.3.0/types/Quickshell.Services.Pam/PamResult)

Emitted whenever authentication completes.

* error ( error ) [](/docs/configuration/qml-overview#-signals)

error : [PamError ](/docs/v0.3.0/types/Quickshell.Services.Pam/PamError)

Emitted if pam fails to perform authentication normally.

A `completed(PamResult.Error) `will be emitted after this event.

* [config ](#config)

* [active ](#active)

* [configDirectory ](#configDirectory)

* [responseVisible ](#responseVisible)

* [responseRequired ](#responseRequired)

* [user ](#user)

* [messageIsError ](#messageIsError)

* [message ](#message)

* [abort ](#abort)

* [respond ](#respond)

* [start ](#start)

* [pamMessage ](#pamMessage)

* [completed ](#completed)

* [error ](#error)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
