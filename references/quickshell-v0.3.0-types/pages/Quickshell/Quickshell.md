## Quickshell : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
singleton

`import Quickshell `
## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* cacheDir : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The per-shell cache directory.

Usually `~/.cache/quickshell/by-shell/<shell-id> `

Can be overridden using `//@ pragma CacheDir $BASE/path `in the root qml file, where `$BASE `corresponds to `$XDG_CACHE_HOME `(usually `~/.cache `).

* processId : [int ](https://doc.qt.io/qt-6/qml-int.html)
readonly

Quickshell’s process id.

* stateDir : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The per-shell state directory.

Usually `~/.local/state/quickshell/by-shell/<shell-id> `

Can be overridden using `//@ pragma StateDir $BASE/path `in the root qml file, where `$BASE `corresponds to `$XDG_STATE_HOME `(usually `~/.local/state `).

* clipboardText : [string ](https://doc.qt.io/qt-6/qml-string.html)

The system clipboard.

WARNING

Under wayland the clipboard will be empty unless a quickshell window is focused.

* screens : [list ](https://doc.qt.io/qt-6/qml-list.html)< [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)>
readonly

All currently connected screens.

This property updates as connected screens change.

#### Reusing a window on every screen

```
`ShellRoot {
  Variants {
    // see Variants for details
    variants: Quickshell.screens
    PanelWindow {
      property var modelData
      screen: modelData
    }
  }
}`
```

This creates an instance of your window once on every screen. As screens are added or removed your window will be created or destroyed on those screens.

* dataDir : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The per-shell data directory.

Usually `~/.local/share/quickshell/by-shell/<shell-id> `

Can be overridden using `//@ pragma DataDir $BASE/path `in the root qml file, where `$BASE `corresponds to `$XDG_DATA_HOME `(usually `~/.local/share `).

* shellDir : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

The full path to the root directory of your shell.

The root directory is the folder containing the entrypoint to your shell, often referred to as `shell.qml `.

* shellRoot : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

WARNING

Deprecated: Renamed to [shellDir ](#shellDir)for consistency.

* workingDirectory : [string ](https://doc.qt.io/qt-6/qml-string.html)

Quickshell’s working directory. Defaults to whereever quickshell was launched from.

* configDir : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

WARNING

Deprecated: Renamed to [shellDir ](#shellDir)for clarity.

* watchFiles : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

If true then the configuration will be reloaded whenever any files change. Defaults to true.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* cachePath ( path ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

path : [string ](https://doc.qt.io/qt-6/qml-string.html)

Equivalent to `${Quickshell.cacheDir}/${path} `

* configPath ( path ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

path : [string ](https://doc.qt.io/qt-6/qml-string.html)

WARNING

Deprecated: Renamed to [shellPath() ](#shellPath)for clarity.

* dataPath ( path ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

path : [string ](https://doc.qt.io/qt-6/qml-string.html)

Equivalent to `${Quickshell.dataDir}/${path} `

* env ( variable ) : [variant ](https://doc.qt.io/qt-6/qml-variant.html)

variable : [string ](https://doc.qt.io/qt-6/qml-string.html)

Returns the string value of an environment variable or null if it is not set.

* execDetached ( context ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

context : [](#unknown)

Launch a process detached from Quickshell.

The context parameter can either be a list of command arguments or a JS object with the following fields:

* `command `: A list containing the command and all its arguments. See [Process.command ](/docs/v0.3.0/types/Quickshell.Io/Process#command).

* `environment `: Changes to make to the process environment. See [Process.environment ](/docs/v0.3.0/types/Quickshell.Io/Process#environment).

* `clearEnvironment `: Removes all variables from the environment if true.

* `workingDirectory `: The working directory the command should run in.

WARNING

This does not run command in a shell. All arguments to the command must be in separate values in the list, e.g. `["echo", "hello"] `and not `["echo hello"] `.

Additionally, shell scripts must be run by your shell, e.g. `["sh", "script.sh"] `instead of `["script.sh"] `unless the script has a shebang.

NOTE

You can use `["sh", "-c", <your command>] `to execute your command with the system shell.

This function is equivalent to [Process.startDetached() ](/docs/v0.3.0/types/Quickshell.Io/Process#startDetached).

* hasQtVersion ( major, minor ) : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

major : [int ](https://doc.qt.io/qt-6/qml-int.html)minor : [int ](https://doc.qt.io/qt-6/qml-int.html)

Check if Qt’s version is at least `major.minor `.

NOTE

You can version gate code blocks using Quickshell’s preprocessor which has the same function available.

```
`//@ if hasVersion(6, 10)
...
//@ endif`
```

* hasThemeIcon ( icon ) : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

icon : [string ](https://doc.qt.io/qt-6/qml-string.html)

Check if specified icon has an available icon in your icon theme

* hasVersion ( major, minor, features ) : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

major : [int ](https://doc.qt.io/qt-6/qml-int.html)minor : [int ](https://doc.qt.io/qt-6/qml-int.html)features : [](#unknown)

Check if Quickshell’s version is at least `major.minor `and the listed unreleased features are available. If Quickshell is newer than the given version it is assumed that all unreleased features are present. The unreleased feature list may be omitted.

NOTE

You can version gate code blocks using Quickshell’s preprocessor which has the same function available.

```
`//@ if hasVersion(0, 3, ["feature"])
...
//@ endif`
```

* hasVersion ( major, minor ) : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

major : [int ](https://doc.qt.io/qt-6/qml-int.html)minor : [int ](https://doc.qt.io/qt-6/qml-int.html)
No details provided

* iconPath ( icon ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

icon : [string ](https://doc.qt.io/qt-6/qml-string.html)

Returns a string usable for a [Image.source ](https://doc.qt.io/qt-6/qml-qtquick-image.html#source-prop)for a given system icon.

NOTE

By default, icons are loaded from the theme selected by the qt platform theme, which means they should match with all other qt applications on your system.

If you want to use a different icon theme, you can put `//@ pragma IconTheme <name> `at the top of your root config file or set the `QS_ICON_THEME `variable to the name of your icon theme.

* iconPath ( icon, check ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

icon : [string ](https://doc.qt.io/qt-6/qml-string.html)check : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Setting the `check `parameter of `iconPath `to true will return an empty string if the icon does not exist, instead of an image showing a missing texture.

* iconPath ( icon, fallback ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

icon : [string ](https://doc.qt.io/qt-6/qml-string.html)fallback : [string ](https://doc.qt.io/qt-6/qml-string.html)

Setting the `fallback `parameter of `iconPath `will attempt to load the fallback icon if the requested one could not be loaded.

* inhibitReloadPopup ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

When called from [reloadCompleted() ](#reloadCompleted)or [reloadFailed() ](#reloadFailed), prevents the default reload popup from displaying.

The popup can also be blocked by setting `QS_NO_RELOAD_POPUP=1 `.

* reload ( hard ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

hard : [bool ](https://doc.qt.io/qt-6/qml-bool.html)

Reload the shell.

`hard `- perform a hard reload. If this is false, Quickshell will attempt to reuse windows that already exist. If true windows will be recreated.

See [Reloadable ](/docs/v0.3.0/types/Quickshell/Reloadable)for more information on what can be reloaded and how.

* shellPath ( path ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

path : [string ](https://doc.qt.io/qt-6/qml-string.html)

Equivalent to `${Quickshell.configDir}/${path} `

* statePath ( path ) : [string ](https://doc.qt.io/qt-6/qml-string.html)

path : [string ](https://doc.qt.io/qt-6/qml-string.html)

Equivalent to `${Quickshell.stateDir}/${path} `

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* reloadCompleted ( ) [](/docs/configuration/qml-overview#-signals)

The reload sequence has completed successfully.

* reloadFailed ( errorString ) [](/docs/configuration/qml-overview#-signals)

errorString : [string ](https://doc.qt.io/qt-6/qml-string.html)

The reload sequence has failed.

* lastWindowClosed ( ) [](/docs/configuration/qml-overview#-signals)

Sent when the last window is closed.

To make the application exit when the last window is closed run `Qt.quit() `.

* [cacheDir ](#cacheDir)

* [processId ](#processId)

* [stateDir ](#stateDir)

* [clipboardText ](#clipboardText)

* [screens ](#screens)

* [dataDir ](#dataDir)

* [shellDir ](#shellDir)

* [shellRoot ](#shellRoot)

* [workingDirectory ](#workingDirectory)

* [configDir ](#configDir)

* [watchFiles ](#watchFiles)

* [cachePath ](#cachePath)

* [configPath ](#configPath)

* [dataPath ](#dataPath)

* [env ](#env)

* [execDetached ](#execDetached)

* [hasQtVersion ](#hasQtVersion)

* [hasThemeIcon ](#hasThemeIcon)

* [hasVersion ](#hasVersion)

* [hasVersion ](#hasVersion)

* [iconPath ](#iconPath)

* [iconPath ](#iconPath)

* [iconPath ](#iconPath)

* [inhibitReloadPopup ](#inhibitReloadPopup)

* [reload ](#reload)

* [shellPath ](#shellPath)

* [statePath ](#statePath)

* [reloadCompleted ](#reloadCompleted)

* [reloadFailed ](#reloadFailed)

* [lastWindowClosed ](#lastWindowClosed)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
