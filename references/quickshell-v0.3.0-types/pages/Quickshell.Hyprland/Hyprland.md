## Hyprland : [QtObject ](https://doc.qt.io/qt-6/qml-qtqml-qtobject.html)
singleton

`import Quickshell.Hyprland `
## Properties [[?] ](/docs/v0.3.0/guide/qml-language#properties)

* focusedWorkspace : [HyprlandWorkspace ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandWorkspace)
readonly

The currently focused hyprland workspace. May be null.

* requestSocketPath : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Path to the request socket (.socket.sock)

* toplevels : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [HyprlandToplevel ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandToplevel)>
readonly

All hyprland toplevels

* usingLua : [bool ](https://doc.qt.io/qt-6/qml-bool.html)
readonly

True if Hyprland is running in lua mode. Dispatcher syntax changes when using lua.

This property will be false until the Hyprland module is initialized.

* activeToplevel : [HyprlandToplevel ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandToplevel)
readonly

Currently active toplevel (might be null)

* eventSocketPath : [string ](https://doc.qt.io/qt-6/qml-string.html)
readonly

Path to the event socket (.socket2.sock)

* workspaces : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [HyprlandWorkspace ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandWorkspace)>
readonly

All hyprland workspaces, sorted by id.

NOTE

Named workspaces have a negative id, and will appear before unnamed workspaces.

* focusedMonitor : [HyprlandMonitor ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandMonitor)
readonly

The currently focused hyprland monitor. May be null.

* monitors : [ObjectModel ](/docs/v0.3.0/types/Quickshell/ObjectModel)< [HyprlandMonitor ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandMonitor)>
readonly

All hyprland monitors.

## Functions [[?] ](/docs/v0.3.0/guide/qml-language#functions)

* dispatch ( request ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

request : [string ](https://doc.qt.io/qt-6/qml-string.html)

Execute a hyprland [dispatcher ](https://wiki.hyprland.org/Configuring/Dispatchers).

* monitorFor ( screen ) : [HyprlandMonitor ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandMonitor)

screen : [ShellScreen ](/docs/v0.3.0/types/Quickshell/ShellScreen)

Get the HyprlandMonitor object that corresponds to a quickshell screen.

* refreshMonitors ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Refresh monitor information.

Many actions that will invalidate monitor state don’t send events, so this function is available if required.

* refreshToplevels ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Refresh toplevel information.

Many actions that will invalidate workspace state don’t send events, so this function is available if required.

* refreshWorkspaces ( ) : [void ](https://doc.qt.io/qt-6/qml-void.html)

Refresh workspace information.

Many actions that will invalidate workspace state don’t send events, so this function is available if required.

## Signals [[?] ](/docs/v0.3.0/guide/qml-language#signals)

* rawEvent ( event ) [](/docs/configuration/qml-overview#-signals)

event : [HyprlandEvent ](/docs/v0.3.0/types/Quickshell.Hyprland/HyprlandEvent)

Emitted for every event that comes in through the hyprland event socket (socket2).

See [Hyprland Wiki: IPC ](https://wiki.hyprland.org/IPC/)for a list of events.

* [focusedWorkspace ](#focusedWorkspace)

* [requestSocketPath ](#requestSocketPath)

* [toplevels ](#toplevels)

* [usingLua ](#usingLua)

* [activeToplevel ](#activeToplevel)

* [eventSocketPath ](#eventSocketPath)

* [workspaces ](#workspaces)

* [focusedMonitor ](#focusedMonitor)

* [monitors ](#monitors)

* [dispatch ](#dispatch)

* [monitorFor ](#monitorFor)

* [refreshMonitors ](#refreshMonitors)

* [refreshToplevels ](#refreshToplevels)

* [refreshWorkspaces ](#refreshWorkspaces)

* [rawEvent ](#rawEvent)

Brought to you by:
[outfoxxed - Lead Developer ](https://outfoxxed.me)[xanazf - Website Developer / Designer ](https://xanazf.github.io)[and our contributors ](https://github.com/quickshell-mirror/quickshell/graphs/contributors)

[](https://matrix.to/#/#quickshell:outfoxxed.me)[](https://discord.gg/UtZeT3xNyT)[](https://git.outfoxxed.me/quickshell/quickshell)
[Changelog ](/changelog)
