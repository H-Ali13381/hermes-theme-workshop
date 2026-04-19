# Pitfalls — Full Detail

## 1. trimEnd() Drift (Misaligned Banner)

The Hermes banner parser calls `trimEnd()` on every line of `banner_hero`/`banner_logo`
before rendering. ASCII spaces (U+0020) at line ends are stripped, causing jagged layout.

**Fix:** Replace ALL spaces (including inline) with Braille blank `⠀` (U+2800):
- Always 1 column wide, invisible, NOT matched by `trimEnd()`
- Both scripts handle this automatically
- Default `HERMES_CADUCEUS` uses this — it's the canonical solution

**Symptom:** "It's still misaligned" even after confirming 30×15 dimensions. Every row
has correct visual width in YAML but rendered output drifts line by line.

---

## 2. Invisible Saturated Dark Colors

Pure grayscale luminance mask (`gray > 110`) silently drops saturated dark colors:
- Crimson red `#d42818` → grayscale ~89 → never lights a dot
- Deep blue, forest green — same problem

**Symptom:** "The red gem is invisible" / colored feature missing from output.

**Fix — dual mask:**
```python
bright     = gray_stretched > 110
red_strong = (r > 90) & (r > g * 1.4) & (r > b * 1.6)
on = bright | red_strong   # add blue_strong, green_strong as needed
```

**Verify with --validate-colors:** accent tier should be 50–100+ cells for a prominent feature.
If <20 cells, loosen: `--lum-threshold 90 --red-ratio-g 1.2`

Do NOT replace grayscale with pure background-distance (`dist > 50`) — collapses
internal shading into solid ⣿ blobs, losing all relief detail.

---

## 3. Never Regex-Patch Banner Fields

`banner_hero` and `banner_logo` are single-line double-quoted YAML scalars containing
literal `\n` escapes AND Rich markup. `re.sub` interprets `\n` in replacement strings
as actual newlines, corrupting the scalar.

**Symptom:** `yaml.safe_load` fails with scanner error on a line starting `[#colorname]...`
(stranded fragment of old markup). Or banner_logo parses as 1 line of ~900 chars.

**Fix:** Always rebuild the entire YAML from a template string and overwrite:
```python
# Keep /tmp/<name>_hero.txt as source-of-truth — never re-extract from YAML
hero = open('/tmp/myskin_hero.txt').read()
yaml_content = TEMPLATE + f'banner_hero: "{hero}"\n'
open(path, 'w').write(yaml_content)
```

If you must surgically replace one field, use `re.search` + slice OR `re.sub` with lambda:
```python
# Lambda bypasses escape interpretation
re.sub(pattern, lambda _: new_value, content)
```

---

## 4. banner_logo Not Auto-Centered

See `hermes_cli/banner.py` — logo is printed flush-left, no `Align.center`, no justify.

If your content is narrower than the canvas string, it renders offset.

**Options:**
- A. Flush-left — strip leading gutter. Matches figlet banners visually.
- B. Equal gutters — only "centered" if terminal matches canvas width exactly.

Per-row centering (shifting each row independently) WILL break multi-row art — letters
that span rows slide out of alignment. Always center the block as a unit.

---

## 5. re.sub Mangles \n In Replacement Strings

Applies to ANY field with backslash escapes: `re.sub(pat, new_value, content)` where
`new_value` contains literal `\n` → those get converted to actual newlines.

**Fix:** Use lambda: `re.sub(pat, lambda _: new_value, content)`

---

## 6. Auto-Tight Bbox for Padded PNGs

PNGs with transparent backgrounds waste resolution. Pipeline:
```python
img = Image.open(path).convert('RGBA')
bg = Image.new('RGBA', img.size, (0,0,0,255))
composited = Image.alpha_composite(bg, img)
gray = np.array(composited.convert('L'))
mask = gray > 20
ys, xs = np.where(mask)
y0, y1 = max(0, ys.min()-3), min(H, ys.max()+3)
x0, x1 = max(0, xs.min()-3), min(W, xs.max()+3)
tight = composited.crop((x0, y0, x1, y1))
```

For logos in a corner of a larger banner: coarse-crop to the logo region FIRST,
then run auto-tight bbox.

---

## 7. Prefer Clean Logo-Only Sources

Coarse-crop + bbox works but if a clean logo PNG exists, use it directly.
Dense promo banners (logo + characters + buttons + text) give muddy results even
after careful cropping — anti-aliased halos bleed into the bbox.
