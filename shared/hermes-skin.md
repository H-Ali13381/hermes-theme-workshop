# Hermes CLI Skin — Match Your Agent to Your Desktop

## 1. What This Is

Hermes (the AI agent running this skill) has its own terminal theme system called **skins**.
When ricing a desktop, the agent's CLI appearance should match the palette too — creating
a fully cohesive experience where the desktop, terminal apps, and the AI agent itself all
share the same design system.

- Skins control the Hermes CLI banner, prompt colors, UI accents, and status indicators
- A skin can be auto-generated from the same 10-key palette used for the desktop rice
- This is the final layer of cohesion: your AI assistant looks like it belongs on your desktop

## 2. Skin File Location & Activation

- Skins are YAML files at `~/.hermes/skins/<name>.yaml`
- **Activate (current session):** `/skin <name>`
- **Activate (permanent):** set `display.skin: <name>` in `~/.hermes/config.yaml`
- **Built-in skins:** `default`, `ares`, `mono`, `slate`, `daylight`, `warm-lightmode`

## 3. Palette → Skin Color Mapping

How the 10-key design system maps to Hermes skin color keys:

| Design System Key | Skin Color Key | Usage |
|---|---|---|
| `background` | — | Not directly used (terminal bg is separate) |
| `foreground` | `banner_text`, `prompt` | Main text colors |
| `primary` | `banner_title`, `banner_accent`, `ui_accent`, `response_border`, `session_label` | Primary highlight throughout UI |
| `secondary` | `banner_dim`, `session_border` | Dimmed/secondary elements |
| `accent` | `ui_label` | Labels and accents |
| `surface` | `input_rule` | Subtle UI elements |
| `muted` | `banner_border` | Border/frame elements |
| `danger` | `ui_error` | Error indicators |
| `success` | `ui_ok` | Success indicators |
| `warning` | `ui_warn` | Warning indicators |

## 4. Auto-Generation from Design System

Generate a skin YAML from a `design_system.json`:

```python
def generate_hermes_skin(design_system, agent_name='Hermes'):
    palette = design_system['palette']
    return f"""name: {design_system['name']}
description: "Auto-generated skin matching {design_system['name']} desktop theme"

colors:
  banner_border:     "{palette['muted']}"
  banner_title:      "{palette['primary']}"
  banner_accent:     "{palette['primary']}"
  banner_dim:        "{palette['secondary']}"
  banner_text:       "{palette['foreground']}"
  ui_accent:         "{palette['primary']}"
  ui_label:          "{palette['accent']}"
  ui_ok:             "{palette['success']}"
  ui_error:          "{palette['danger']}"
  ui_warn:           "{palette['warning']}"
  prompt:            "{palette['foreground']}"
  input_rule:        "{palette['surface']}"
  response_border:   "{palette['primary']}"
  session_label:     "{palette['primary']}"
  session_border:    "{palette['secondary']}"

branding:
  agent_name:      "{agent_name}"
  response_label:  " {agent_name} "
"""
```

### Usage in ricer.py

```python
import json, os

with open('design_system.json') as f:
    ds = json.load(f)

skin_yaml = generate_hermes_skin(ds)
skin_path = os.path.expanduser(f"~/.hermes/skins/{ds['name']}.yaml")
os.makedirs(os.path.dirname(skin_path), exist_ok=True)
with open(skin_path, 'w') as f:
    f.write(skin_yaml)

print(f"Hermes skin written to {skin_path}")
print(f"Activate: /skin {ds['name']}")
```

## 5. Banner Art

The skin also supports custom ASCII/braille banner art:

- **`banner_hero`**: 30 cols × 15 rows — left column of the startup banner
- **`banner_logo`**: ≤100 cols — wide header above the hero

### Creating banner art

1. Use `image_gen` to create a mascot/logo matching the theme mood
2. Convert to braille with scripts from the `hermes-cli-skin` skill:
   - `scripts/img_to_braille.py` — general image-to-braille converter
   - `scripts/image_to_hero.py` — resizes and formats for banner_hero dimensions
3. **Braille (U+2800–U+28FF)** is recommended over ASCII — 2×4 subpixel resolution per character
4. Pad spaces with Braille blank (`⠀` U+2800) to prevent `trimEnd()` drift

See `shared/braille-art.md` for the full braille conversion pipeline and colorization techniques.

### Art style guidelines

- Dark themes: light braille on transparent background
- Keep detail level appropriate for 30×15 character grid
- Thematic consistency: dragon for doom-knight, snowflake for nord, cat for catppuccin, etc.

## 6. Integration with ricer.py

When applying a full rice, the materializer should also generate and install a matching Hermes skin:

1. After applying desktop theme, generate skin YAML from the same `design_system`
2. Write to `~/.hermes/skins/<theme-name>.yaml`
3. Print instruction: `Run /skin <theme-name> to match your Hermes agent to this theme`
4. Or auto-activate if running inside Hermes (check for `~/.hermes/config.yaml`)

### Proposed materializer addition

```python
def materialize_hermes_skin(design_system):
    """Generate and install a matching Hermes CLI skin."""
    skin_yaml = generate_hermes_skin(design_system)
    skin_dir = os.path.expanduser("~/.hermes/skins")
    os.makedirs(skin_dir, exist_ok=True)
    
    skin_path = os.path.join(skin_dir, f"{design_system['name']}.yaml")
    with open(skin_path, 'w') as f:
        f.write(skin_yaml)
    
    # Check if we're running inside Hermes
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    if os.path.exists(config_path):
        print(f"✓ Hermes skin installed: {skin_path}")
        print(f"  Activate now:      /skin {design_system['name']}")
        print(f"  Activate forever:  display.skin: {design_system['name']} in config.yaml")
    
    return skin_path
```

## 7. Known Pitfalls

- **`/skin <name>` activates immediately** — no restart needed
- **`config.yaml` changes need a new session** to take effect
- **Never regex-patch `banner_hero`/`banner_logo` YAML fields** — multiline braille art breaks with find-and-replace; always rebuild the full skin file
- **Banner art scripts need PIL/numpy** — run via `terminal`, not `execute_code`
- **Block chars (░▒▓█) often render 2-wide** — use ASCII or braille for guaranteed 1-wide glyphs
- **Skin only affects CLI terminal interface** — Telegram, Discord, and web gateways are not themed
- **Color format**: skin YAML expects hex strings (e.g., `"#7ad4f0"`), same as design_system palette — no conversion needed
