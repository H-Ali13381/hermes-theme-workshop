---
name: hermes-cli-skin
description: >
  Create and install custom Hermes CLI skins (terminal visual themes).
  Use when the user wants to change Hermes's colors, prompt symbol,
  branding text, or visual identity in the terminal.
  NOT the same as theme-factory (artifact styling) or dashboard.theme (web UI).
version: 2.0.0
author: NousResearch / community
metadata:
  hermes:
    tags: [hermes, skin, theme, cli, terminal, branding, colors, ascii, braille]
    related_skills: [hermes-skills-management]
---

# Hermes CLI Skin

## Distinction
Three theming systems exist — do NOT confuse them:
1. **display.skin** — CLI terminal appearance. This skill.
2. **dashboard.theme** — Web UI only.
3. **theme-factory** — Output artifacts (slides, HTML, docs).

## Key Paths
```
~/.hermes/skins/<name>.yaml   ← skin files
~/.hermes/config.yaml         ← display.skin: <name> for persistence
~/.hermes/skills/             ← skills directory
~/.hermes/assets/theme/       ← reference images
```

## Activation
```bash
/skin <name>          # current session (no restart needed)
# permanent: edit ~/.hermes/config.yaml, add:
# display:
#   skin: <name>
# WARNING: never use >> append — duplicate keys break config parsing
```

## Built-in Skins
`default`, `ares`, `mono`, `slate`, `daylight`, `warm-lightmode`

---

## Skin YAML Schema (all fields optional)
```yaml
name: <skin-name>
description: "..."

colors:
  banner_border / banner_title / banner_accent / banner_dim / banner_text
  ui_accent / ui_label / ui_ok / ui_error / ui_warn
  prompt / input_rule / response_border / session_label / session_border

branding:
  agent_name / welcome / goodbye / response_label / prompt_symbol / help_header

tool_prefix: ">"
tool_emojis:
  terminal / web_search / browser / read_file / write_file / memory

banner_hero: "..."   # 30×15 — see Banner Dimensions
banner_logo: "..."   # ≤100 cols — see Banner Dimensions
```

---

## Banner Dimensions (HARD constraints from banner.ts)
| Field | Width | Height | Notes |
|---|---|---|---|
| `banner_hero` | **30 cols** | **15 rows** | Left column beside tool list |
| `banner_logo` | **≤100 cols** | ≤12 rows | Shown when terminal ≥95 cols |

`banner_logo` is **NOT auto-centered** — rendered flush-left.

---

## Banner Art — Braille Unicode (Recommended)

Braille (U+2800–U+28FF) = **2×4 subpixel resolution per cell**, always 1-wide.
Use `⠀` (U+2800, Braille blank) for ALL padding — immune to `trimEnd()` trimming.
Block chars `░▒▓█` often render 2-wide — avoid unless tested.

**Generate art:**
```bash
# Braille (recommended)
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/img_to_braille.py \
  --input ~/.hermes/assets/theme/image.png \
  --width 30 --height 15 --palette gold --out-preview

# ASCII ramp (classic/retro)
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/image_to_hero.py \
  image.png --ramp classic --palette gold --plain
```

Always preview first, get shape approval, THEN write YAML.
`execute_code` sandbox has no PIL/numpy — use `terminal` + `python3`.

---

## Critical Pitfalls (summary — see references/pitfalls.md for full detail)

1. **trimEnd() drift** — Replace ALL spaces with `⠀` (U+2800). Both scripts do this automatically.
2. **Invisible saturated colors** — Pure grayscale mask silently drops crimson/deep blue. Use dual luminance+saturation mask. Pass `--validate-colors` to img_to_braille.py.
3. **Never regex-patch banner fields** — Rebuild entire YAML from template string + `write_file`. `re.sub` corrupts `\n` escapes in YAML scalars.
4. **banner_logo not centered** — Strip leading gutter or pad symmetrically. No auto-center in renderer.
5. **Iterate on plain art first** — Get shape approval, then colorize. Keep old builder scripts (v1, v2…) for easy revert.

---

## DragonFable / Doom Knight Example
```yaml
name: dragonfable
colors:
  banner_border: "#8c1a2e"  banner_title: "#c9a227"  banner_accent: "#c9a227"
  banner_dim: "#5a3a0a"     banner_text: "#e8dcc8"   ui_accent: "#c9a227"
  ui_label: "#c9a227"       ui_ok: "#7ab87a"          ui_error: "#e05c5c"
  ui_warn: "#d4882a"        prompt: "#e8dcc8"          input_rule: "#8c1a2e"
  response_border: "#c9a227" session_label: "#c9a227" session_border: "#4a1a24"
branding:
  agent_name: "Doomherald"
  welcome: "The darkness stirs. Doomherald answers your call."
  goodbye: "Until the next battle."
  response_label: " Doomherald "
  prompt_symbol: "> "
tool_prefix: ">"
tool_emojis: {terminal: sword, web_search: crystal, read_file: scroll, memory: skull}
```

---

## Linked Files (load on demand)
- `references/pitfalls.md` — Full technical detail on all pitfalls
- `references/braille-art.md` — Braille encoding, hue classification, pyfiglet, color validation
- `scripts/img_to_braille.py` — Production Braille converter
- `scripts/image_to_hero.py` — Classic ASCII ramp converter
