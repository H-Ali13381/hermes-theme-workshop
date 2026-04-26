# KDE Splash Screen

## Configuration

Splash screen is set via `ksplashrc`:

```bash
kwriteconfig6 --file ksplashrc --group KSplash --key Theme <theme-id>
kwriteconfig6 --file ksplashrc --group KSplash --key Engine KSplashQML
```

## Config File Location

```
~/.config/ksplashrc
```

Example contents:
```ini
[KSplash]
Engine=KSplashQML
Theme=org.kde.breeze.desktop
```

## Custom Splash Themes

Splash themes live at:
```
~/.local/share/plasma/look-and-feel/<theme-id>/contents/splash/
```

Required files:
- `Splash.qml` — the QML scene rendered during boot
- `images/` — any images referenced by the QML

The `Theme` key in ksplashrc references the look-and-feel package ID, not a file path.

## Available Themes

List installed splash themes:
```bash
find /usr/share/plasma/look-and-feel ~/.local/share/plasma/look-and-feel -maxdepth 1 -type d 2>/dev/null
```

## Pitfalls

- Splash screen changes only take effect on next login/reboot — no live preview.
- The `Engine` key must be set to `KSplashQML` for QML-based splash themes.
- Splash theme is often tied to the Look-and-Feel package — changing it independently requires explicit ksplashrc writes.
