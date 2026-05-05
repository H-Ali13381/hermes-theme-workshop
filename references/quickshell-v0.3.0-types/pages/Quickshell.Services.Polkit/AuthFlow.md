## AuthFlow : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.Polkit `
## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* isCancelled : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates whether the current authentication request was cancelled.

* isResponseRequired : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates that a response from the user is required from the user, typically a password.

* cookie : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

A cookie that identifies this authentication request.

This is an internal identifier and not recommended to show to users.

* iconName : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The icon to present to the user in association with the message.

The icon name follows the [FreeDesktop icon naming specification ](https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html). Use [Quickshell.iconPath() ](/docs/v0.3.0/types/Quickshell/Quickshell#iconPath)to resolve the icon name to an actual file path for display.

* responseVisible : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates whether the user’s response should be visible. (e.g. for passwords this should be false)

* isCompleted : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Has the authentication request been completed.

* inputPrompt : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

This message is used to prompt the user for required input.

* isSuccessful : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates whether the authentication request was successful.

* actionId : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The action ID represents the action that is being authorized.

This is a machine-readable identifier.

* supplementaryMessage : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

An additional message to present to the user.

This may be used to show errors or supplementary information. See [supplementaryIsError ](#supplementaryIsError)to determine if this is an error message.

* message : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The main message to present to the user.

* failed : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates whether an authentication attempt has failed at least once during this authentication flow.

* identities : [list ](https://doc.qt.io/qt-6/qml-list.html)
readonly

The list of identities that may be used to authenticate.

Each identity may be a user or a group. You may select any of them to authenticate by setting [selectedIdentity ](#selectedIdentity). By default, the first identity in the list is selected.

* selectedIdentity : [unknown ](#unknown)

The identity that will be used to authenticate.

Changing this will abort any ongoing authentication conversations and start a new one.

* supplementaryIsError : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

Indicates whether the supplementary message is an error.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* cancelAuthenticationRequest ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Cancel the ongoing authentication request from the user side.

* submit ( value ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

value : [string ](https://doc.qt.io/qt-6/qml-string.html)

Submit a response to a request that was previously emitted. Typically the password.

* [isCancelled ](#isCancelled)

* [isResponseRequired ](#isResponseRequired)

* [cookie ](#cookie)

* [iconName ](#iconName)

* [responseVisible ](#responseVisible)

* [isCompleted ](#isCompleted)

* [inputPrompt ](#inputPrompt)

* [isSuccessful ](#isSuccessful)

* [actionId ](#actionId)

* [supplementaryMessage ](#supplementaryMessage)

* [message ](#message)

* [failed ](#failed)

* [identities ](#identities)

* [selectedIdentity ](#selectedIdentity)

* [supplementaryIsError ](#supplementaryIsError)

* [cancelAuthenticationRequest ](#cancelAuthenticationRequest)

* [submit ](#submit)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
