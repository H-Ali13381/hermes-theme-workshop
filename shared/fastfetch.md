# Fastfetch — System Info Theming & Custom Logos

Fastfetch is a system info display tool (successor to neofetch). Works on **any Linux environment** — not Hyprland-specific.

---

## 1. Overview

- Fast, actively maintained system info tool (neofetch is unmaintained — use fastfetch instead)
- Config: `~/.config/fastfetch/config.jsonc` (fastfetch ≥2.0) or `config.json` (older versions)
- Displays system info with a logo alongside — the logo can be replaced with custom braille art

**CRITICAL — config filename:**
- Fastfetch auto-detects `config.json` in `~/.config/fastfetch/`
- On some versions, `.jsonc` works; on others it silently falls back to default Arch logo
- If your custom theme doesn't appear: `mv config.jsonc config.json`

---

## 2. Installation

```bash
# Arch Linux
sudo pacman -S fastfetch

# Generate default config
fastfetch --gen-config
```

---

## 3. Theming with Palette

Color integration from the design system palette:

| JSON Path | Palette Key | Purpose |
|-----------|-------------|---------|
| `display.color.title` | primary | Username@host color |
| `display.color.keys` | accent | Label color (OS, CPU, etc.) |
| `display.color.separator` | accent or warning | Separator character color |
| `display.color.output` | foreground | Value text color |
| `logo.color.1` | primary | Logo primary color |
| `logo.color.2` | accent | Logo secondary color |

**Use hex values** (e.g., `"#d4a012"`) — named colors like `"gold"` are rejected.

### Thematic Separators

The separator character sets the mood of the greeting:

| Theme Mood | Separator |
|------------|-----------|
| Void / dragon | `" 𑁍 "` |
| Game / RPG | `" ♦ "` |
| Gothic / blood | `" ✦ "` |
| MapleStory | `" ♥ "` |
| Minimal / tech | `" → "` |
| Default | `" ∙ "` |

### Thematic Module Keys

Module keys can be customized for immersion:

```json
// Game/RPG style
{"type": "cpu", "key": "  HP"}, {"type": "memory", "key": "  MP"}

// Sci-fi style
{"type": "cpu", "key": "  CORE"}, {"type": "memory", "key": "  BANK"}

// Standard with Nerd Font icons
{"type": "cpu", "key": "  CPU"}, {"type": "memory", "key": "  MEM"}
```

---

## 4. Custom Braille Logo

Instead of the default distro ASCII art, use a **custom braille logo** matching the theme.

### Config for file-based logo

```jsonc
{
  "logo": {
    "type": "file",
    "source": "/home/USER/.config/fastfetch/logo.txt"
  }
}
```

Or inline with `"type": "raw"` and the braille text directly in `"source"`.

### Generation pipeline

1. Describe or generate an image matching the theme's mood (mascot, game character, abstract)
2. Convert to braille using `img_to_braille.py` — see `shared/braille-art.md` for full pipeline
3. Set as fastfetch logo in config

```bash
# Generate braille logo (40 wide, 18 tall)
python3 ~/.hermes/skills/creative/hermes-cli-skin/scripts/img_to_braille.py \
  --input ~/Pictures/logo.png \
  --width 40 --height 18 \
  --output ~/.config/fastfetch/logo.txt
```

- **Recommended size:** 30–40 chars wide, 15–20 rows tall
- See `shared/braille-art.md` for the full conversion pipeline, thresholding, and colorization

### Colored braille logos

For ANSI-colored braille in the logo file, use 24-bit true color escapes:

```
\e[38;2;201;162;39m⣿⣿⣿\e[0m   (gold-colored braille)
\e[38;2;122;212;240m⣿⣿⣿\e[0m   (cyan-colored braille)
```

---

## 5. Integration with ricer.py

When applying a rice, fastfetch should get:

1. **Color scheme** matching the palette (separator colors, key colors, output colors)
2. **Custom braille logo** generated from the theme's mood/aesthetic
3. **Thematic separator** character matching the design mood
4. **Styled module keys** (RPG, sci-fi, or standard depending on mood_tags)

Proposed materializer adds fastfetch to the standard ricing pipeline alongside terminal, bar, and launcher configs.

---

## 6. Shell Integration

Add to `~/.bashrc` or `~/.zshrc` to display on every new terminal:

```bash
fastfetch
```

Or conditionally (only in interactive shells):

```bash
[[ $- == *i* ]] && fastfetch
```

No reload needed — fastfetch reads its config fresh on every invocation.

---

## 7. Known Pitfalls

- **Config filename:** must be `config.json` on many versions, not `config.jsonc` — test both
- **Logo file paths:** use **absolute paths** — `~` expansion may not work in the JSON config
- **ANSI colors in logo files:** use `\e[38;2;R;G;Bm` (24-bit color) for full palette matching
- **neofetch is unmaintained** — fastfetch is the actively maintained successor, always prefer it
- **Named colors rejected:** use hex (`"#d4a012"`), not names (`"gold"`)
- **JSON validation:** `python3 -m json.tool ~/.config/fastfetch/config.json` to check syntax
- **Debugging:** `fastfetch --config ~/.config/fastfetch/config.json` to test explicitly
