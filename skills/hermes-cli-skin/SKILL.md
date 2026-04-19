---
name: hermes-cli-skin
description: >
  Create and install custom Hermes CLI skins (terminal visual themes).
  Use when the user wants to change Hermes's colors, prompt symbol,
  branding text, or visual identity in the terminal.
  NOT the same as theme-factory (artifact styling) or dashboard.theme (web UI).
version: 1.1.0
author: NousResearch / community
metadata:
  hermes:
    tags: [hermes, skin, theme, cli, terminal, branding, colors, ascii, braille]
    related_skills: [hermes-skills-management]
---

# Hermes CLI Skin

## Critical Distinction

There are THREE separate theming systems in Hermes. Do NOT confuse them:

1. **display.skin** — CLI terminal appearance (colors, prompt, branding). This skill.
2. **dashboard.theme** — Web dashboard UI colors (web browser only).
3. **theme-factory skill** — For styling output *artifacts* (slides, HTML pages, docs).

If the user says "change the theme" or "change how Hermes looks", they almost certainly mean `display.skin`.

---

## How It Works

Skins are YAML files placed at `~/.hermes/skins/<name>.yaml`.  
All fields are optional — missing values inherit from the default skin.  
Activate with `/skin <name>` (current session) or add `display.skin: <name>` to `config.yaml` for permanence.

### Key paths
```
~/.hermes/skins/           ← your skin files go here
~/.hermes/config.yaml      ← set display.skin: <name> for persistence
~/.hermes/skills/          ← skills directory
```

Built-in skins (already shipped with Hermes):
- `default` — Classic Hermes gold/kawaii
- `ares` — Crimson/bronze war-god theme
- `mono` — Clean grayscale monochrome
- `slate` — Cool blue developer-focused
- `daylight` — Light background theme
- `warm-lightmode` — Warm brown/gold for light terminals

---

## Skin YAML Schema

All fields are optional. Omitted color keys silently inherit from `default`.

```yaml
name: <skin-name>
description: "Short description"

colors:
  banner_border:   "#hex"   # Outer border of the startup banner
  banner_title:    "#hex"   # Main title text in the banner
  banner_accent:   "#hex"   # Accent highlights in the banner
  banner_dim:      "#hex"   # Dimmed/secondary banner elements
  banner_text:     "#hex"   # Body text in the banner
  ui_accent:       "#hex"   # Primary UI highlight color
  ui_label:        "#hex"   # Labels throughout the UI
  ui_ok:           "#hex"   # Success/ok indicators
  ui_error:        "#hex"   # Error indicators
  ui_warn:         "#hex"   # Warning indicators
  prompt:          "#hex"   # Input prompt text color
  input_rule:      "#hex"   # Underline/rule beneath input box
  response_border: "#hex"   # Border of the agent response box
  session_label:   "#hex"   # Session name label color
  session_border:  "#hex"   # Session divider color

branding:
  agent_name:     "Name"    # Banner title, status display
  welcome:        "Text"    # Shown at CLI startup
  goodbye:        "Text"    # Shown on exit
  response_label: " Name "  # Response box header label
  prompt_symbol:  "> "      # Input prompt symbol
  help_header:    "Text"    # /help header text

tool_prefix: ">"   # Character prefixing tool output lines (default: pipe)

tool_emojis:       # Per-tool emoji overrides (spinners & progress)
  terminal:    "sword"
  web_search:  "crystal"
  browser:     "crystal"
  read_file:   "scroll"
  write_file:  "scroll"
  memory:      "skull"

banner_hero: "..."   # 30×15 ASCII/braille art (see Banner Dimensions below)
banner_logo: "..."   # Wide header art, ≤100 cols (see Banner Dimensions below)
```

---

## Banner Dimensions (HARD constraints)

### `banner_hero` — 30 cols × 15 rows
The hero sits in the **LEFT column** of a Rich `Table.grid` beside the tool/skill info panel.
- Width: **exactly 30 characters** (see `ui-tui/src/banner.ts` → `CADUCEUS_WIDTH = 30`)
- Height: **exactly 15 rows**
- Exceeding either breaks the side-by-side column layout

### `banner_logo` — ≤100 cols, flexible height
Rendered above the hero+tools grid when terminal width ≥ 95 cols.
- Safe working sizes observed: 92×6, 92×7, 92×10, 92×12
- **NOT auto-centered** — rendered flush-left. If your content is narrower than
  your canvas string, it will appear offset. Strip leading gutters or center the
  block equally to compensate.

---

## Recommended Approach: Braille Unicode for ASCII Art

**Braille characters are the baseline recommendation for banner art.**

Why: The Braille Unicode block (U+2800–U+28FF) provides **2×4 sub-pixel resolution**
per character cell — 8 dots per cell, each individually addressable. This gives:

- **4× the effective resolution** of standard ASCII ramps at the same character count
- **Pixel-accurate letterforms** that survive the 30×15 hero constraint
- **Single-width guarantee** — Braille chars are always 1 column wide (unlike `░▒▓` block chars)
- **Braille blank (`⠀` U+2800)** is invisible AND immune to `trimEnd()` — essential for padding

Standard ASCII ramps are a fallback for simpler/retro aesthetics or when the user
prefers them. Offer both and let the user pick — but lead with Braille.

### Braille cell encoding
Each cell covers a 2-wide × 4-tall pixel block from the source image.
Dot layout (bit positions):
```
dot1 dot2       bit0 bit3
dot3 dot4  →    bit1 bit4
dot5 dot6       bit2 bit5
dot7 dot8       bit6 bit7
```
Braille codepoint: `0x2800 + bitmask` where each bit is 1 if the source pixel
is "on" (above luminance threshold or strongly saturated).

Use `scripts/img_to_braille.py` for production-quality conversion with:
- Luminance threshold + saturation override (catches crimson reds, deep blues)
- Per-cell hue classification → Rich color markup (`[#hex]...[/]`)
- Auto-tight bounding box for padded PNGs
- Braille-blank padding to prevent `trimEnd()` drift

Use `scripts/image_to_hero.py` for traditional ASCII ramp conversion (classic/doom/blocky ramps).

---

## CRITICAL: Trailing Whitespace Gets Trimmed

The Hermes banner parser calls `trimEnd()` on every line before rendering.
ASCII spaces (U+0020) at line ends are stripped, causing jagged/drifting layout.

**Fix**: Pad ALL spaces (including inline) with **Braille blank `⠀` (U+2800)**.
- Always 1 column wide
- Invisible (no visible glyph)
- NOT matched by `trimEnd()`
- The default `HERMES_CADUCEUS` uses this — it's the canonical solution

Both scripts in `scripts/` handle this automatically.

---

## CRITICAL: Saturated Dark Colors Are Invisible Under Grayscale Thresholding

If you derive the "dot on" mask only from grayscale luminance (`gray > 110`), strongly
saturated dark colors (crimson red `#d42818` → gray ~89, deep blue, forest green)
are SILENTLY dropped. Their pixels never light a dot.

**Symptom**: "The red gem is invisible" / colored features missing from output.

**Fix** — combine luminance AND saturation masks:
```python
bright     = gray_stretched > 110
red_strong = (r > 90) & (r > g * 1.4) & (r > b * 1.6)
on = bright | red_strong   # add blue_strong, green_strong as needed
```

See `scripts/img_to_braille.py` — this mask is implemented and commented there.

---

## CRITICAL: Never Regex-Patch banner_logo / banner_hero

The banner fields are single-line double-quoted YAML scalars containing literal `\n`
escapes AND Rich markup. `re.sub` interprets `\n` in replacement strings as actual
newlines, corrupting the scalar into a multi-line mess.

**Fix**: Always rebuild the entire skin YAML from a template string and overwrite with
`write_file`. Keep `/tmp/<name>_hero.txt` as source-of-truth for hero art so you
never need to re-extract it from YAML.

If you must surgically replace one field, use `re.search` + slice:
```python
m = re.search(r'^banner_logo:\s*"(?:[^"\\]|\\.)*"', content, flags=re.M)
new_line = f'banner_logo: "{logo_escaped}"'
content = content[:m.start()] + new_line + content[m.end():]
```
Or use `re.sub` with a lambda: `re.sub(pat, lambda _: new, content)` — the lambda
bypasses escape interpretation.

---

## Per-Pixel Hue Classification (Colorized Braille)

For multi-hue images (gold dragon + red gem + dark shadow), map each braille
cell's average color into a small palette:

```python
def classify(r, g, b, a=255):
    if a < 30: return None
    if r > 100 and r > g * 1.4 and r > b * 1.6:
        return CRIMSON if r > 160 else CRIMSON_DK
    if r > b + 20 and g > b - 10:
        lum = 0.299*r + 0.587*g + 0.114*b
        if lum > 170: return GOLD_BRIGHT
        if lum > 90:  return GOLD
        return GOLD_DIM
    return GOLD_DIM
```

Collect RGBA from all lit dots in each cell, average, classify, emit `[#hex]...[/]`
Rich tags per color run. This preserves actual colors without manual region masks.

---

## Title Card via Pyfiglet (Text Logos)

For pure-text `banner_logo` (agent name, project title):

```python
import pyfiglet
art = pyfiglet.figlet_format("AGENTNAME", font="ansi_shadow", width=200)
```

`ansi_shadow` produces 6 rows of `█`-style block letters with built-in shadow chars.
Apply 3-tone shading:
```python
BRIGHT = '#f0d688'   # row 0 top highlight
MID    = '#cc9e24'   # middle rows
DIM    = '#885d14'   # last row + shadow chars ╗╝╔╚║═
```

---

## Workflow: Preview Before Install

**Always show multiple options before writing any YAML.**

Standard preview lineup for a logo/mascot:
- ASCII ramp (classic/doom) at target dimensions
- Braille at same dimensions

Braille wins for logos/mascots because 2×4 subpixels preserve letterforms.
Frame each preview with `+---+` box borders so the user can judge footprint.

Re-emit framed if the user says "where's the preview?" — messaging platforms
can lose formatting context.

---

## Installation Steps

```bash
# 1. Create skins directory
mkdir -p ~/.hermes/skins

# 2. Write your skin YAML
# (use write_file tool or copy from this repo's examples/)

# 3. Activate for current session (no restart needed)
/skin <name>

# 4. Make permanent — add to ~/.hermes/config.yaml
display:
  skin: <name>
```

---

## Generating Art from an Image

### Step 1 — Prepare your source image
- Use clean, high-contrast sources (logos on transparent/solid bg preferred)
- For PNGs with padding: the scripts auto-crop tight bounding boxes
- For dense promo images: coarse-crop to the region of interest first
- Save to `~/.hermes/assets/` or your skin's `assets/` subfolder

### Step 2 — Generate Braille art (recommended)
```bash
python3 scripts/img_to_braille.py \
  --input /path/to/image.png \
  --width 30 --height 15 \          # banner_hero dimensions
  --palette gold \                   # or: crimson, cyan, mono
  --out-yaml                         # print ready-to-paste YAML value
```

### Step 3 — Or generate ASCII ramp art (classic style)
```bash
python3 scripts/image_to_hero.py /path/to/image.png \
  --ramp classic \                   # or: doom, blocky
  --palette gold
```

### Step 4 — Write the skin YAML
Use `write_file` to create `~/.hermes/skins/<name>.yaml`.
NEVER patch banner fields with regex — always rebuild the full YAML.

### Step 5 — Activate and verify
```
/skin <name>
```
Check: does the hero/logo render correctly? Is there drift/misalignment?
If drift: ensure all ASCII spaces are replaced with `⠀` (U+2800).

---

## Example Skin: DragonFable / Doom Knight

```yaml
# ~/.hermes/skins/dragonfable.yaml
name: dragonfable
description: "Doom Knight's Mantle — shadow void, dragon gold, crimson fell"

colors:
  banner_border:     "#8c1a2e"   # Crimson Fell
  banner_title:      "#c9a227"   # Dragon Gold
  banner_accent:     "#c9a227"
  banner_dim:        "#5a3a0a"   # Tarnished gold
  banner_text:       "#e8dcc8"   # Pale Rune (ivory)
  ui_accent:         "#c9a227"
  ui_label:          "#c9a227"
  ui_ok:             "#7ab87a"
  ui_error:          "#e05c5c"
  ui_warn:           "#d4882a"
  prompt:            "#e8dcc8"
  input_rule:        "#8c1a2e"
  response_border:   "#c9a227"
  session_label:     "#c9a227"
  session_border:    "#4a1a24"

branding:
  agent_name:      "Doomherald"
  welcome:         "The darkness stirs. Doomherald answers your call."
  goodbye:         "Until the next battle."
  response_label:  " Doomherald "
  prompt_symbol:   "> "
  help_header:     "Commands of the Doom Knight"

tool_prefix: ">"

tool_emojis:
  terminal:    "sword"
  web_search:  "crystal"
  browser:     "crystal"
  read_file:   "scroll"
  write_file:  "scroll"
  memory:      "skull"
```

---

## Pitfalls

- `theme-factory` is for artifacts (HTML, slides, docs) — NOT the CLI appearance.
- `dashboard.theme` changes the web UI only — NOT the terminal.
- `/skin <name>` activates immediately in the running session without restart.
- `config.yaml` changes require a new session to take effect.
- User skins take precedence over built-ins of the same name.
- Missing color keys silently inherit from `default` — no need to specify every field.
- `execute_code` sandbox does NOT have PIL/numpy. Always run image scripts via
  `terminal` using `python3 /path/to/script.py`.
- Block chars `░▒▓█` (U+2591–U+2588) often render 2-wide on many terminals.
  Stick to ASCII or Braille for guaranteed 1-wide output.
- Iterate on plain art FIRST (shape approval), THEN colorize. Colorization is
  mechanical — don't bikeshed before the shape is right.
- Keep old builder scripts (v1, v2, v3) intact — users often want to revert.
- When building for banner_logo: banner_logo is NOT auto-centered. Render flush-left
  or pad symmetrically, but tell the user the tradeoff.
