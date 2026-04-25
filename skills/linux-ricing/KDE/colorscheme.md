# KDE Colorscheme

## File Location

KDE colorscheme files live at:
```
~/.local/share/color-schemes/<name>.colors
```

The ricer generates and writes `~/.local/share/color-schemes/hermes-<name>.colors` automatically.

## File Format

KDE `.colors` files use INI-style sections with **decimal RGB** values (`r,g,b`), NOT hex:

```ini
[General]
ColorScheme=hermes-void-dragon
Name=hermes-void-dragon

[Colors:Window]
BackgroundNormal=12,18,32
ForegroundNormal=228,240,255

[Colors:View]
BackgroundNormal=28,30,42
ForegroundNormal=228,240,255

[Colors:Button]
BackgroundNormal=28,30,42
ForegroundNormal=228,240,255
DecorationFocus=122,212,240
DecorationHover=212,160,18

[Colors:Selection]
BackgroundNormal=122,212,240
ForegroundNormal=12,18,32

[Colors:Tooltip]
BackgroundNormal=28,30,42
ForegroundNormal=228,240,255

[Colors:Complementary]
BackgroundNormal=12,18,32
ForegroundNormal=228,240,255

[WM]
activeBackground=12,18,32
activeForeground=228,240,255
inactiveBackground=28,30,42
inactiveForeground=98,102,114
```

## Generation from 10-Key Palette

```python
def hex_to_rgb(h):
    """Convert '#rrggbb' to 'r,g,b' decimal string for KDE .colors format."""
    h = h.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"

# Mapping from palette keys to KDE color roles:
# background → Window/BackgroundNormal, View/BackgroundNormal
# foreground → Window/ForegroundNormal, View/ForegroundNormal
# primary    → Selection/BackgroundNormal, Button/DecorationFocus
# accent     → Button/DecorationHover
# surface    → Button/BackgroundNormal, Tooltip/BackgroundNormal
# muted      → WM/inactiveForeground
```

## Activation

```bash
plasma-apply-colorscheme hermes-void-dragon
```

The name passed must match the `[General] ColorScheme=` value inside the `.colors` file — it's a **name**, not a file path.

## Force Re-Application

`plasma-apply-colorscheme` does nothing if the scheme name matches the current one. To force:

```bash
plasma-apply-colorscheme BreezeClassic && sleep 1 && plasma-apply-colorscheme hermes-void-dragon
```

## Pitfalls

- **DECIMAL RGB only.** Writing `#7ad4f0` instead of `122,212,240` produces a silently invalid scheme.
- **Colorscheme may be inherited** from `[KDE] LookAndFeelPackage=` if `[General] ColorScheme=` is missing from kdeglobals. Always read both keys during snapshot.
- **Colorscheme-only apply looks subtle** if already on a dark theme. The dramatic change comes from Kvantum — always configure Kvantum alongside.
- **PRESETS missing `kvantum_theme`** silently fall back to `"kvantum-dark"` which is almost certainly not installed.
