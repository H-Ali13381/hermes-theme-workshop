## Greetd : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
singleton

`import Quickshell.Services.Greetd `
This object provides access to a running greetd instance if present. With it you can authenticate a user and launch a session.

See [the greetd wiki ](https://man.sr.ht/~kennylevinsen/greetd/#setting-up-greetd-with-gtkgreet)for instructions on how to set up a graphical greeter.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* user : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The currently authenticating user.

* state : [GreetdState ](/docs/v0.3.0/types/Quickshell.Services.Greetd/GreetdState)
readonly

The current state of the greetd connection.

* available : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

If the greetd socket is available.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* cancelSession ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Cancel the active greetd session.

* createSession ( user ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

user : [string ](https://doc.qt.io/qt-6/qml-string.html)

Create a greetd session for the given user.

* launch ( command ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

command : [list ](https://doc.qt.io/qt-6/qml-list.html)

Launch the session, exiting quickshell. [state ](#state)must be `GreetdState.ReadyToLaunch `to call this function.

* launch ( command, environment ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

command : [list ](https://doc.qt.io/qt-6/qml-list.html)environment : [list ](https://doc.qt.io/qt-6/qml-list.html)

Launch the session, exiting quickshell. [state ](#state)must be `GreetdState.ReadyToLaunch `to call this function.

* launch ( command, environment, quit ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

command : [list ](https://doc.qt.io/qt-6/qml-list.html)environment : [list ](https://doc.qt.io/qt-6/qml-list.html)quit : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Launch the session, exiting quickshell if [quit ](#quit)is true. [state ](#state)must be `GreetdState.ReadyToLaunch `to call this function.

The [launched ](#launched)signal can be used to perform an action after greetd has acknowledged the desired session.

WARNING

Note that greetd expects the greeter to terminate as soon as possible after setting a target session, and waiting too long may lead to unexpected behavior such as the greeter restarting.

Performing animations and such should be done before calling [launch ](#launch).

* respond ( response ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

response : [string ](https://doc.qt.io/qt-6/qml-string.html)

Respond to an authentication message.

May only be called in response to an [authMessage() ](#authMessage)with `responseRequired `set to true.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* error ( error ) [](/docs/configuration/qml-overview#-signals)

error : [string ](https://doc.qt.io/qt-6/qml-string.html)

Greetd has encountered an error.

* authFailure ( message ) [](/docs/configuration/qml-overview#-signals)

message : [string ](https://doc.qt.io/qt-6/qml-string.html)

Authentication has failed an the session has terminated.

Usually this is something like a timeout or a failed password entry.

* authMessage ( message, error, responseRequired, echoResponse ) [](/docs/configuration/qml-overview#-signals)

message : [string ](https://doc.qt.io/qt-6/qml-string.html)error : [bool ](https://doc.qt.io/qt-6/qml-bool.html)responseRequired : [bool ](https://doc.qt.io/qt-6/qml-bool.html)echoResponse : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

An authentication message has been sent by greetd.

* `message `- the text of the message

* `error `- if the message should be displayed as an error

* `responseRequired `- if a response via `respond() `is required for this message

* `echoResponse `- if the response should be displayed in clear text to the user

Note that `error `and `responseRequired `are mutually exclusive.

Errors are sent through `authMessage `when they are recoverable, such as a fingerprint scanner not being able to read a finger correctly, while definite failures such as a bad password are sent through `authFailure `.

* readyToLaunch ( ) [](/docs/configuration/qml-overview#-signals)

Authentication has finished successfully and greetd can now launch a session.

* launched ( ) [](/docs/configuration/qml-overview#-signals)

Greetd has acknowledged the launch request and the greeter should quit as soon as possible.

This signal is sent right before quickshell exits automatically if the launch was not specifically requested not to exit. You usually don’t need to use this signal.

* [user ](#user)

* [state ](#state)

* [available ](#available)

* [cancelSession ](#cancelSession)

* [createSession ](#createSession)

* [launch ](#launch)

* [launch ](#launch)

* [launch ](#launch)

* [respond ](#respond)

* [error ](#error)

* [authFailure ](#authFailure)

* [authMessage ](#authMessage)

* [readyToLaunch ](#readyToLaunch)

* [launched ](#launched)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
