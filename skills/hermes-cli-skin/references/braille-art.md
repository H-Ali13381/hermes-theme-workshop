# Braille Art — Technical Reference

## Braille Cell Encoding

Each cell covers a 2-wide × 4-tall pixel block. Dot layout (bit positions):
```
col0  col1
dot1  dot4   → bit0  bit3
dot2  dot5   → bit1  bit4
dot3  dot6   → bit2  bit5
dot7  dot8   → bit6  bit7
```
Codepoint: `0x2800 + bitmask`. Braille blank = `0x2800` (⠀).

---

## Per-Pixel Hue Classification (Colorized Braille)

For multi-hue images (gold dragon + red gem + dark shadow):
```python
def classify(r, g, b, a=255):
    if a < 30: return None
    # Red-dominant → crimson family
    if r > 100 and r > g * 1.4 and r > b * 1.6:
        return CRIMSON if r > 160 else CRIMSON_DK
    # Warm → gold family
    if r > b + 20 and g > b - 10:
        lum = 0.299*r + 0.587*g + 0.114*b
        if lum > 170: return GOLD_BRIGHT
        if lum > 90:  return GOLD
        return GOLD_DIM
    return GOLD_DIM
```

Collect RGBA from all lit dots per cell → average → classify → emit `[#hex]...[/]` Rich tags.

---

## Pyfiglet Title Card (Text Logos)

```python
import pyfiglet
art = pyfiglet.figlet_format("AGENTNAME", font="ansi_shadow", width=200)
```

`ansi_shadow` produces 6 rows of `█`-style block letters with shadow chars `╗╝╔╚║═`.
Apply 3-tone gold shading:
```python
BRIGHT = '#f0d688'   # row 0 only
MID    = '#cc9e24'   # middle rows
DIM    = '#885d14'   # last row + ╗╝╔╚║═ shadow chars
```
Run-length encode color changes with `[#hex]...[/]` tags.

---

## Safe Character Sets

| Set | Width | Notes |
|-----|-------|-------|
| Plain ASCII ` .:-=+*#%@` | Always 1-wide | Safest, universal |
| Braille U+2800–U+28FF | Always 1-wide | Best detail, needs Nerd Fonts |
| `■` U+25A0, `◆` U+25C6 | Usually 1-wide | East Asian Ambiguous — test first |
| `░▒▓█` U+2591–U+2588 | Often 2-wide | AVOID in banner_hero unless verified |

---

## banner_logo Observed Working Sizes

| Size | Source |
|------|--------|
| 98×6 | pyfiglet ansi_shadow default |
| 92×7 | DRAGONFABLE ansi_shadow |
| 92×10 | Colorized braille logo crop |
| 92×12 | Braille from 5.5:1 aspect source |

Stay ≤100 cols for narrow terminal compatibility.

---

## Workflow: Preview Before Install

Standard preview lineup for a logo/mascot:
1. ASCII ramp at target dimensions (plain, no markup)
2. Braille at same dimensions (plain, no markup)
3. User picks → THEN generate colored YAML value

Re-emit framed with `+---+` borders if messaging platform loses formatting context.
