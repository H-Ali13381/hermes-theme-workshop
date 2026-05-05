## MprisPlayer : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
uncreatable

`import Quickshell.Services.Mpris `
A media player exposed over MPRIS.

WARNING

Support for various functionality and general compliance to the MPRIS specification varies wildly by player. Always check the associated `canXyz `and `xyzSupported `properties if available.

NOTE

The TrackList and Playlist interfaces were not implemented as we could not find any media players using them to test against.

## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* isPlaying : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

True if [playbackState ](#playbackState)== `MprisPlaybackState.Playing `.

Setting this property is equivalent to calling [play() ](#play)or [pause() ](#pause). You cannot set this property if [canTogglePlaying ](#canTogglePlaying)is false.

* trackAlbumArtist : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The current track’s album artist, or `"" `if none was provided.

TIP

Use `player.trackAlbumArtist || "Unknown Album" `to provide a message when no album artist is available.

* shuffleSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* lengthSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* position : [real ](https://doc.qt.io/qt-6/qml-real.html)

The current position in the playing track, as seconds, with millisecond precision, or `0 `if [positionSupported ](#positionSupported)is false.

May only be written to if [canSeek ](#canSeek)and [positionSupported ](#positionSupported)are true.

WARNING

To avoid excessive property updates wasting CPU while `position `is not actively monitored, `position `usually will not update reactively, unless a nonlinear change in position occurs, however reading it will always return the current position.

If you want to actively monitor the position, the simplest way it to emit the [positionChanged() ](#positionChanged)signal manually for the duration you are monitoring it, Using a [FrameAnimation ](https://doc.qt.io/qt-6/qml-qtquick-frameanimation.html)if you need the value to update smoothly, such as on a slider, or a [Timer ](https://doc.qt.io/qt-6/qml-qtquick-timer.html)if not, as shown below.

```
`FrameAnimation {
  // only emit the signal when the position is actually changing.
  running: player.playbackState == MprisPlaybackState.Playing
  // emit the positionChanged signal every frame.
  onTriggered: player.positionChanged()
}`
```

```
`Timer {
  // only emit the signal when the position is actually changing.
  running: player.playbackState == MprisPlaybackState.Playing
  // Make sure the position updates at least once per second.
  interval: 1000
  repeat: true
  // emit the positionChanged signal every second.
  onTriggered: player.positionChanged()
}`
```

* trackArtist : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The current track’s artist, or an `"" `if none was provided.

TIP

Use `player.trackArtist || "Unknown Artist" `to provide a message when no artist is available.

* uniqueId : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

An opaque identifier for the current track unique within the current player.

WARNING

This is NOT `mpris:trackid `as that is sometimes missing or nonunique in some players.

* canPlay : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* loopSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* desktopEntry : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The name of the desktop entry for the media player, or an empty string if not provided.

* metadata : [unknown ](#unknown)
readonly

Metadata of the current track.

A map of common properties is available [here ](https://www.freedesktop.org/wiki/Specifications/mpris-spec/metadata). Do not count on any of them actually being present.

Note that the [trackTitle ](#trackTitle), [trackAlbum ](#trackAlbum), [trackAlbumArtist ](#trackAlbumArtist), [trackArtist ](#trackArtist)and [trackArtUrl ](#trackArtUrl)properties have extra logic to guard against bad players sending weird metadata, and should be used over grabbing the properties directly from the metadata.

* canSeek : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* positionSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* canPause : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* dbusName : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The DBus service name of the player.

* trackAlbum : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The current track’s album, or `"" `if none was provided.

TIP

Use `player.trackAlbum || "Unknown Album" `to provide a message when no album is available.

* length : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

The length of the playing track, as seconds, with millisecond precision, or the value of [position ](#position)if [lengthSupported ](#lengthSupported)is false.

* minRate : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

No details provided

* maxRate : [real ](https://doc.qt.io/qt-6/qml-real.html)
readonly

No details provided

* rate : [real ](https://doc.qt.io/qt-6/qml-real.html)

The speed the song is playing at, as a multiplier.

Only values between [minRate ](#minRate)and [maxRate ](#maxRate)(inclusive) may be written to the property. Additionally, It is recommended that you only write common values such as `0.25 `, `0.5 `, `1.0 `, `2.0 `to the property, as media players are free to ignore the value, and are more likely to accept common ones.

* trackArtists : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

[!ERROR] deprecated in favor of [trackArtist ](#trackArtist).

* volume : [real ](https://doc.qt.io/qt-6/qml-real.html)

The volume of the playing track from 0.0 to 1.0, or 1.0 if [volumeSupported ](#volumeSupported)is false.

May only be written to if [canControl ](#canControl)and [volumeSupported ](#volumeSupported)are true.

* trackTitle : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The title of the current track, or `"" `if none was provided.

TIP

Use `player.trackTitle || "Unknown Title" `to provide a message when no title is available.

* volumeSupported : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* canGoPrevious : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* loopState : [MprisLoopState ](/docs/v0.3.0/types/Quickshell.Services.Mpris/MprisLoopState)

The loop state of the media player, or `None `if [loopSupported ](#loopSupported)is false.

May only be written to if [canControl ](#canControl)and [loopSupported ](#loopSupported)are true.

* canControl : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* canRaise : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* supportedUriSchemes : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>
readonly

Uri schemes supported by [openUri() ](#openUri).

* canSetFullscreen : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* shuffle : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the play queue is currently being shuffled, or false if [shuffleSupported ](#shuffleSupported)is false.

May only be written if [canControl ](#canControl)and [shuffleSupported ](#shuffleSupported)are true.

* trackArtUrl : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The current track’s art url, or `"" `if none was provided.

* canGoNext : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* fullscreen : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If the player is currently shown in fullscreen.

May only be written to if [canSetFullscreen ](#canSetFullscreen)is true.

* canTogglePlaying : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

* playbackState : [MprisPlaybackState ](/docs/v0.3.0/types/Quickshell.Services.Mpris/MprisPlaybackState)

The playback state of the media player.

* If [canPlay ](#canPlay)is false, you cannot assign the `Playing `state.

* If [canPause ](#canPause)is false, you cannot assign the `Paused `state.

* If [canControl ](#canControl)is false, you cannot assign the `Stopped `state. (or any of the others, though their repsective properties will also be false)

* supportedMimeTypes : [list ](https://doc.qt.io/qt-6/qml-list.html)< [string ](https://doc.qt.io/qt-6/qml-string.html)>
readonly

Mime types supported by [openUri() ](#openUri).

* identity : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The human readable name of the media player.

* canQuit : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

No details provided

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* next ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Play the next song.

May only be called if [canGoNext ](#canGoNext)is true.

* openUri ( uri ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

uri : [string ](https://doc.qt.io/qt-6/qml-string.html)

Open the given URI in the media player.

Many players will silently ignore this, especially if the uri does not match [supportedUriSchemes ](#supportedUriSchemes)and [supportedMimeTypes ](#supportedMimeTypes).

* pause ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Equivalent to setting [playbackState ](#playbackState)to `Paused `.

* play ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Equivalent to setting [playbackState ](#playbackState)to `Playing `.

* previous ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Play the previous song, or go back to the beginning of the current one.

May only be called if [canGoPrevious ](#canGoPrevious)is true.

* quit ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Quit the media player.

May only be called if [canQuit ](#canQuit)is true.

* raise ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Bring the media player to the front of the window stack.

May only be called if [canRaise ](#canRaise)is true.

* seek ( offset ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

offset : [real ](https://doc.qt.io/qt-6/qml-real.html)

Change `position `by an offset.

Even if [positionSupported ](#positionSupported)is false and you cannot set `position `, this function may work.

May only be called if [canSeek ](#canSeek)is true.

* stop ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Equivalent to setting [playbackState ](#playbackState)to `Stopped `.

* togglePlaying ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Equivalent to calling [play() ](#play)if not playing or [pause() ](#pause)if playing.

May only be called if [canTogglePlaying ](#canTogglePlaying)is true, which is equivalent to [canPlay ](#canPlay)or [canPause ](#canPause)depending on the current playback state.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* postTrackChanged ( ) [](/docs/configuration/qml-overview#-signals)

Sent after track info related properties have been updated, following [trackChanged ](#trackChanged).

WARNING

It is not safe to assume all track information is up to date after this signal is emitted. A large number of players will update track information, particularly [trackArtUrl ](#trackArtUrl), slightly after this signal.

* trackChanged ( ) [](/docs/configuration/qml-overview#-signals)

The track has changed.

All track information properties that were sent by the player will be updated immediately following this signal. [postTrackChanged ](#postTrackChanged)will be sent after they update.

Track information properties: [uniqueId ](#uniqueId), [metadata ](#metadata), [trackTitle ](#trackTitle), [trackArtist ](#trackArtist), [trackAlbum ](#trackAlbum), [trackAlbumArtist ](#trackAlbumArtist), [trackArtUrl ](#trackArtUrl)

WARNING

Some particularly poorly behaved players will update metadata before indicating the track has changed.

* [isPlaying ](#isPlaying)

* [trackAlbumArtist ](#trackAlbumArtist)

* [shuffleSupported ](#shuffleSupported)

* [lengthSupported ](#lengthSupported)

* [position ](#position)

* [trackArtist ](#trackArtist)

* [uniqueId ](#uniqueId)

* [canPlay ](#canPlay)

* [loopSupported ](#loopSupported)

* [desktopEntry ](#desktopEntry)

* [metadata ](#metadata)

* [canSeek ](#canSeek)

* [positionSupported ](#positionSupported)

* [canPause ](#canPause)

* [dbusName ](#dbusName)

* [trackAlbum ](#trackAlbum)

* [length ](#length)

* [minRate ](#minRate)

* [maxRate ](#maxRate)

* [rate ](#rate)

* [trackArtists ](#trackArtists)

* [volume ](#volume)

* [trackTitle ](#trackTitle)

* [volumeSupported ](#volumeSupported)

* [canGoPrevious ](#canGoPrevious)

* [loopState ](#loopState)

* [canControl ](#canControl)

* [canRaise ](#canRaise)

* [supportedUriSchemes ](#supportedUriSchemes)

* [canSetFullscreen ](#canSetFullscreen)

* [shuffle ](#shuffle)

* [trackArtUrl ](#trackArtUrl)

* [canGoNext ](#canGoNext)

* [fullscreen ](#fullscreen)

* [canTogglePlaying ](#canTogglePlaying)

* [playbackState ](#playbackState)

* [supportedMimeTypes ](#supportedMimeTypes)

* [identity ](#identity)

* [canQuit ](#canQuit)

* [next ](#next)

* [openUri ](#openUri)

* [pause ](#pause)

* [play ](#play)

* [previous ](#previous)

* [quit ](#quit)

* [raise ](#raise)

* [seek ](#seek)

* [stop ](#stop)

* [togglePlaying ](#togglePlaying)

* [postTrackChanged ](#postTrackChanged)

* [trackChanged ](#trackChanged)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
