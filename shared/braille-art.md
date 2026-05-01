# Braille Art — Image → Braille Conversion Pipeline

Shared reference for converting images to braille Unicode art. Used by both Hermes CLI skins (`shared/hermes-skin.md`) and fastfetch/neofetch custom logos (`shared/fastfetch.md`).

---

## 1. What Is Braille Art

- Braille Unicode block (U+2800–U+28FF) provides **2×4 sub-pixel resolution** per character cell
- 8 dots per cell, each individually addressable → **4× the effective resolution** of standard ASCII art
- **Single-width guarantee** — unlike block chars `░▒▓█` which often render 2-wide in terminals
- Braille blank (`⠀` U+2800) is invisible and immune to `trimEnd()` — essential for padding lines to consistent width

---

## 2. Braille Cell Encoding

Each cell covers a 2-wide × 4-tall pixel block from the source image:

```
dot1 dot4       bit0 bit3
dot2 dot5  →    bit1 bit4
dot3 dot6       bit2 bit5
dot7 dot8       bit6 bit7
```

Codepoint: `0x2800 + bitmask` — each bit = 1 if the corresponding source pixel is "on" (above threshold).

---

## 3. Conversion Pipeline

1. **Source image** → crop to region of interest
2. **Resize** to target character dimensions (width × 2, height × 4 for pixel resolution)
3. **Threshold** — convert to grayscale OR use luminance + saturation thresholding (see §4)
4. **Map** each 2×4 pixel block to a braille character via bitmask
5. **Colorize** (optional) — classify per-cell average hue → Rich markup or ANSI escapes (see §5)
6. **Pad** trailing spaces with Braille blank (U+2800) to prevent trim drift

---

## 4. Thresholding Pitfall

Pure grayscale thresholding (`gray > 110`) drops **saturated dark colors** like crimson and deep blue. Fix: combine luminance AND saturation:

```python
bright = gray > 110
red_strong = (r > 90) & (r > g * 1.4) & (r > b * 1.6)
blue_strong = (b > 90) & (b > r * 1.3) & (b > g * 1.3)
on = bright | red_strong | blue_strong
```

This ensures vivid dark pixels are preserved in the output.

---

## 5. Per-Pixel Colorization

For multi-colored images, classify each braille cell's average color and emit markup:

- **ANSI escape codes** — for terminal tools like fastfetch: `\e[38;2;R;G;Bm` (24-bit true color)
- **Rich markup** — for Hermes skins: `[#RRGGBB]text[/]`

Example hue classifier (simplified):

```python
def classify_color(r, g, b):
    if r > g * 1.4 and r > b * 1.6: return 'red'
    if r > b + 20 and g > b - 10: return 'gold'
    if b > r * 1.3 and b > g * 1.3: return 'blue'
    return 'neutral'
```

Map classified colors to the design system palette for theme-coherent output.

---

## 6. Target Dimensions by Use Case

| Use Case | Width (chars) | Height (rows) | Notes |
|----------|--------------|---------------|-------|
| Hermes `banner_hero` | 30 | 15 | **Exact** — exceeding breaks layout |
| Hermes `banner_logo` | ≤100 | flexible | Flush-left rendering |
| fastfetch logo | 30–40 | 15–20 | Alongside system info, keep reasonable |
| neofetch logo | 30–40 | 15–20 | Same as fastfetch |
| EWW widget art | varies | varies | Depends on widget size |

---

## 7. Available Scripts

Located in the `hermes-cli-skin` skill (`~/.hermes/skills/creative/hermes-cli-skin/scripts/`):

- **`img_to_braille.py`** — production braille converter with luminance+saturation thresholding, per-cell hue colorization, auto-tight bounding box, braille-blank padding
- **`image_to_hero.py`** — traditional ASCII ramp converter (classic/doom/blocky ramps)

**Requirements:** PIL/numpy — run via `terminal`, not `execute_code`.

---

## 8. Quick Usage

```bash
# Braille art for fastfetch (40 wide, 18 tall)
python3 ~/.hermes/skills/creative/hermes-cli-skin/scripts/img_to_braille.py \
  --input ~/Pictures/logo.png \
  --width 40 --height 18 \
  --output ~/.config/fastfetch/logo.txt

# Braille art for Hermes banner_hero (exact 30×15)
python3 ~/.hermes/skills/creative/hermes-cli-skin/scripts/img_to_braille.py \
  --input ~/Pictures/mascot.png \
  --width 30 --height 15 \
  --out-yaml
```

---

## 9. ASCII Ramp Alternative

For retro/classic aesthetics, use ASCII character ramps instead of braille:

- **Classic ramp:** `' .:-=+*#%@'`
- **Block ramp:** `' ░▒▓█'` — beware 2-wide rendering in many terminals
- Lower resolution than braille but distinctive chunky look
- Some users and themes (retro, pixel-art) specifically call for this style
