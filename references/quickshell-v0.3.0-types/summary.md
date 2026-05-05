# Quickshell v0.3.0 Type Docs Source of Truth

This directory is a pinned local snapshot of https://quickshell.org/docs/v0.3.0/types/.
Use it when generating, editing, statically validating, or reviewing Quickshell QML.

Machine-readable index: `index.json`.
Full scraped Markdown pages: `pages/<module>/<type>.md`.
Refresh command: `python3 scripts/ingest_quickshell_types.py --version v0.3.0`.

## Non-negotiable linux-ricing rules

- Use `PanelWindow` for bars, launchers, notification/quest cards, menus, HUDs, and visually floating shell widgets.
- Do not use `FloatingWindow` for KDE/Wayland shell chrome; it can appear as a decorated app window.
- Use `PopupWindow` for child popups/menus anchored to another item/window, not for the root panel surface.
- Use `Quickshell.Io.Process` with argv arrays for command actions when possible; reject hidden shell-string interpolation unless explicitly required.
- Keep preview-texture artifacts non-promotable; this docs source is for component-mode QML correctness.

## Critical types for widget/dashboard generation

### Quickshell.Io/Process

- Import: `Quickshell.Io`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Io/Process/
- Description: running: true
- Properties: stdout, running, clearEnvironment, command, processId, environment, stderr, stdinEnabled, workingDirectory
- Snapshot: `pages/Quickshell.Io/Process.md`

### Quickshell.Services.Mpris/Mpris

- Import: `Quickshell.Services.Mpris`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.Mpris/Mpris/
- Description: readonly
- Properties: players
- Snapshot: `pages/Quickshell.Services.Mpris/Mpris.md`

### Quickshell.Services.Mpris/MprisPlayer

- Import: `Quickshell.Services.Mpris`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.Mpris/MprisPlayer/
- Description: A media player exposed over MPRIS.
- Properties: isPlaying, trackAlbumArtist, shuffleSupported, lengthSupported, position, trackArtist, uniqueId, canPlay, loopSupported, desktopEntry, metadata, canSeek
- Snapshot: `pages/Quickshell.Services.Mpris/MprisPlayer.md`

### Quickshell.Services.Notifications/Notification

- Import: `Quickshell.Services.Notifications`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.Notifications/Notification/
- Description: A notification emitted by a NotificationServer.
- Properties: id, desktopEntry, tracked, body, image, expireTimeout, transient, appName, lastGeneration, actions, resident, appIcon
- Snapshot: `pages/Quickshell.Services.Notifications/Notification.md`

### Quickshell.Services.Notifications/NotificationServer

- Import: `Quickshell.Services.Notifications`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.Notifications/NotificationServer/
- Description: An implementation of the Desktop Notifications Specification for receiving notifications from external applications.
- Properties: imageSupported, extraHints, actionsSupported, actionIconsSupported, bodySupported, inlineReplySupported, persistenceSupported, bodyImagesSupported, trackedNotifications, bodyHyperlinksSupported, bodyMarkupSupported, keepOnReload
- Snapshot: `pages/Quickshell.Services.Notifications/NotificationServer.md`

### Quickshell.Services.Pipewire/Pipewire

- Import: `Quickshell.Services.Pipewire`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.Pipewire/Pipewire/
- Description: Contains links to all pipewire objects.
- Properties: links, defaultAudioSource, nodes, ready, preferredDefaultAudioSource, preferredDefaultAudioSink, linkGroups, defaultAudioSink
- Snapshot: `pages/Quickshell.Services.Pipewire/Pipewire.md`

### Quickshell.Services.SystemTray/SystemTray

- Import: `Quickshell.Services.SystemTray`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.SystemTray/SystemTray/
- Description: Referencing the SystemTray singleton will make quickshell start tracking system tray contents, which are updated as the tray changes, and can be accessed via the items property.
- Properties: items
- Snapshot: `pages/Quickshell.Services.SystemTray/SystemTray.md`

### Quickshell.Services.SystemTray/SystemTrayItem

- Import: `Quickshell.Services.SystemTray`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.SystemTray/SystemTrayItem/
- Description: A system tray item, roughly conforming to the kde/freedesktop spec (there is no real spec, we just implemented whatever seemed to actually be used).
- Properties: status, tooltipDescription, title, category, tooltipTitle, icon, hasMenu, onlyMenu, menu, id
- Snapshot: `pages/Quickshell.Services.SystemTray/SystemTrayItem.md`

### Quickshell.Services.UPower/UPower

- Import: `Quickshell.Services.UPower`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Services.UPower/UPower/
- Description: An interface to the UPower daemon , which can be used to view battery and power statistics for your computer and connected devices.
- Properties: devices, displayDevice, onBattery
- Snapshot: `pages/Quickshell.Services.UPower/UPower.md`

### Quickshell.Wayland/WlrLayer

- Import: `Quickshell.Wayland`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/WlrLayer/
- Description: See WlrLayershell.layer .
- Variants: Background, Bottom, Top, Overlay
- Snapshot: `pages/Quickshell.Wayland/WlrLayer.md`

### Quickshell.Wayland/WlrLayershell

- Import: `Quickshell.Wayland`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Wayland/WlrLayershell/
- Description: Decorationless window that can be attached to the screen edges using the zwlr_layer_shell_v1 protocol.
- Properties: keyboardFocus, layer, namespace
- Snapshot: `pages/Quickshell.Wayland/WlrLayershell.md`

### Quickshell.Widgets/IconImage

- Import: `Quickshell.Widgets`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Widgets/IconImage/
- Description: This is a specialization of Image configured for icon-style images, designed to make it easier to use correctly. If you need more control, use Image directly.
- Properties: backer, source, actualSize, mipmap, status, implicitSize, asynchronous
- Snapshot: `pages/Quickshell.Widgets/IconImage.md`

### Quickshell.Widgets/WrapperMouseArea

- Import: `Quickshell.Widgets`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell.Widgets/WrapperMouseArea/
- Description: This component is useful for wrapping a single component in a mouse area. It works the same as WrapperItem , but with a MouseArea .
- Properties: topMargin, child, leftMargin, implicitHeight, implicitWidth, rightMargin, margin, extraMargin, resizeChild, bottomMargin
- Snapshot: `pages/Quickshell.Widgets/WrapperMouseArea.md`

### Quickshell/Edges

- Import: `Quickshell`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell/Edges/
- Description: Edge flags can be combined with the | operator.
- Variants: Left, Top, None, Bottom, Right
- Snapshot: `pages/Quickshell/Edges.md`

### Quickshell/ExclusionMode

- Import: `Quickshell`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell/ExclusionMode/
- Description: See PanelWindow.exclusionMode .
- Variants: Normal, Ignore, Auto
- Snapshot: `pages/Quickshell/ExclusionMode.md`

### Quickshell/FloatingWindow

- Import: `Quickshell`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell/FloatingWindow/
- Description: Standard toplevel operating system window that looks like any other application.
- Properties: maximized, maximumSize, fullscreen, parentWindow, minimized, minimumSize, title
- Snapshot: `pages/Quickshell/FloatingWindow.md`

### Quickshell/PanelWindow

- Import: `Quickshell`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell/PanelWindow/
- Description: Decorationless window attached to screen edges by anchors.
- Properties: focusable, margins, anchors, exclusiveZone, aboveWindows, exclusionMode
- Snapshot: `pages/Quickshell/PanelWindow.md`

### Quickshell/PopupWindow

- Import: `Quickshell`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell/PopupWindow/
- Description: Popup window that can display in a position relative to a floating or panel window.
- Properties: parentWindow, relativeY, screen, visible, grabFocus, relativeX, anchor
- Snapshot: `pages/Quickshell/PopupWindow.md`

### Quickshell/QsWindow

- Import: `Quickshell`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell/QsWindow/
- Description: Base class of Quickshell windows
- Properties: backingWindowVisible, height, visible, implicitWidth, implicitHeight, contentItem, mask, devicePixelRatio, data, surfaceFormat, screen, updatesEnabled
- Snapshot: `pages/Quickshell/QsWindow.md`

### Quickshell/ShellRoot

- Import: `Quickshell`
- URL: https://quickshell.org/docs/v0.3.0/types/Quickshell/ShellRoot/
- Description: Optional root config element, allowing some settings to be specified inline.
- Properties: settings
- Snapshot: `pages/Quickshell/ShellRoot.md`
