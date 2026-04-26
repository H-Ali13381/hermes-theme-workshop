# Konsole Theming

## File Locations

- Colorscheme: `~/.local/share/konsole/linux-ricing-colors.colorscheme`
- Profile: `~/.local/share/konsole/linux-ricing.profile`
- Default profile config: `~/.config/konsolerc`

## Colorscheme Format

Uses decimal RGB (`r,g,b`) — same as KDE `.colors` files. Always use `hex_to_rgb()` to convert.

```ini
[General]
Description=hermes-void-dragon
Opacity=1
Wallpaper=

[Background]
Color=12,18,32

[Foreground]
Color=228,240,255

[Color0]
Color=28,30,42

[Color1]
Color=204,48,144

[Color2]
Color=42,128,96

[Color3]
Color=200,120,32

[Color4]
Color=122,212,240

[Color5]
Color=13,46,50

[Color6]
Color=212,160,18

[Color7]
Color=228,240,255

[Color0Intense]
Color=61,34,20

[Color1Intense]
Color=219,62,158

[Color2Intense]
Color=55,166,125

[Color3Intense]
Color=215,140,42

[Color4Intense]
Color=105,220,245

[Color5Intense]
Color=20,60,65

[Color6Intense]
Color=225,175,30

[Color7Intense]
Color=240,248,255
```

## 10-Key → 16 ANSI Color Mapping

Konsole uses the same 10-key → 16 ANSI mapping defined in `shared/design-system.md`.

## DefaultProfile Activation

**CRITICAL:** The profile file alone is not enough. You MUST set the DefaultProfile key:

```bash
kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile linux-ricing.profile
```

Without this, Konsole ignores the new profile entirely on next launch.

## Profile File

```ini
[Appearance]
ColorScheme=linux-ricing-colors

[General]
Name=linux-ricing
Parent=FALLBACK/

[Scrolling]
HistoryMode=2
```

## Pitfalls

- **New session required.** Terminal colors activate only in new Konsole sessions after theming. Running instances are not affected.
- **ANSI color4/color3 collision** on gold-heavy palettes: if `primary==warning`, kitty and konsole color4 (blue) becomes indistinguishable from color3 (yellow). Fix: swap color4 to `secondary`.
- **Decimal RGB only** — same as all KDE `.colors` files.
