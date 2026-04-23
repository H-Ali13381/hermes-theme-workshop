# hermes-theme-workshop

**Hermes agent skills for desktop personalization** — terminal skins, full DE theming
engines, and everything in between. Extracted from iterative real-world usage on
Arch Linux / KDE Plasma / Hyprland.

---

## What's Here

```
hermes-theme-workshop/
├── README.md                            ← this file (the recipe)
├── skills/
│   ├── hermes-cli-skin/                 ← Terminal/CLI skinning (colors, banner art)
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── img_to_braille.py        ← Braille art generator (recommended)
│   │       └── image_to_hero.py         ← ASCII ramp generator (classic style)
│   ├── hermes-ricer/                    ← Deterministic KDE theming engine
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   │   ├── desktop_state_audit.py   ← Read-only baseline capture
│   │   │   ├── deterministic_ricing_session.py  ← Safe apply/rollback
│   │   │   ├── ricer.py                 ← Materialization engine
│   │   │   └── setup.sh                 ← Dependency install
│   │   └── templates/                   ← Design system templates
│   ├── hyprland-rice-from-scratch/      ← Full Hyprland tiling WM setup
│   ├── ricer-apps/                      ← App-level materializers (kitty, rofi, waybar...)
│   ├── ricer-catalog-capture/           ← Screenshot catalog for ricing options
│   ├── ricer-gtk/                       ← GTK theming layer
│   ├── ricer-kde/                       ← KDE Plasma deep-dive (Kvantum, panel SVG)
│   ├── ricer-rollback/                  ← Rollback architecture + deterministic sessions
│   └── ricer-wallpaper/                 ← Wallpaper generation and palette extraction
├── examples/
│   └── dragonfable.yaml                 ← Complete CLI skin example
└── assets/
    └── sample_images/                   ← drop your reference images here
```

---

## Two Systems, One Repo

This repo covers **both** Hermes output styling and desktop environment theming.
They are independent — pick one or both.

| System | What it changes | Skill |
|---|---|---|
| **CLI Skinning** | How Hermes *looks in the terminal* — colors, banners, prompt | `hermes-cli-skin` |
| **Desktop Ricing** | Your actual Linux desktop — KDE Plasma, Hyprland, GTK, wallpapers | `hermes-ricer` + sub-skills |

If you only want a cool terminal banner, read **Part 1**.
If you want to transform your entire desktop, read **Part 2**.

---

# Part 1 — CLI Skinning (Terminal Themes)

### Phase 1 — Install the Skill

```bash
# Clone this repo first
git clone https://github.com/H-Ali13381/hermes-theme-workshop
cd hermes-theme-workshop

mkdir -p ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts

# Copy the skill definition and scripts
cp skills/hermes-cli-skin/SKILL.md ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/
cp skills/hermes-cli-skin/scripts/img_to_braille.py \
   skills/hermes-cli-skin/scripts/image_to_hero.py \
   ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/
```

Verify Hermes sees it — in a Hermes session:
```
/skills
```
You should see `hermes-cli-skin` listed.

### Phase 2 — Understand Your Environment

Before generating art, tell your Hermes agent:

> *"Update the hermes-cli-skin skill to reflect my environment:*
> - *Hermes skins go in `~/.hermes/skins/`*
> - *Config is at `~/.hermes/config.yaml`*
> - *Python with Pillow+numpy is available at `/usr/bin/python3`*
> - *Skills are in `~/.hermes/skills/`"*

### Phase 3 — Choose a Theme Direction

Tell your agent what look you want. Be specific:
- **Color palette** — dark/moody, bright/neon, gold/fantasy, tech-blue, etc.
- **Tone** — playful, serious, dramatic, minimal
- **Reference** — a game, a character, a logo, a color hex code
- **Terminal font** — if you have Nerd Fonts installed, say so (unlocks braille safely)

Example prompt:
> *"Create a DragonFable-themed skin — dark background, gold and crimson accents,
> fantasy/RPG tone. I have Nerd Fonts installed."*

### Phase 4 — Generate Banner Art

**Why Braille Unicode is the baseline recommendation:**

The Braille Unicode block (U+2800–U+28FF) gives **2×4 sub-pixel resolution per character cell**
(8 individually addressable dots). At the same character count, it preserves 4× more detail
than standard ASCII ramps. Critically, Braille characters are **always 1 column wide**
(unlike `░▒▓█` block chars which render double-width on many terminals).

**Hard dimension limits** from `banner.ts`:

| Field | Width | Height | Notes |
|---|---|---|---|
| `banner_hero` | **30 cols** | **15 rows** | Left column beside tool list |
| `banner_logo` | **≤100 cols** | ≤12 rows | Above everything, terminal ≥95 cols only |

**4a. Get a source image**

```bash
mkdir -p ~/.hermes/assets/theme
wget -O ~/.hermes/assets/theme/mylogo.png "https://example.com/logo.png"
```

Good sources:
- Your project/game logo on a transparent background (PNG preferred)
- High-contrast portraits or mascots
- CC0 images from Unsplash, OpenGameArt, Pixabay

**4b. Generate Braille art (recommended)**

```bash
# banner_hero (30×15) — the small hero beside the tools list
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/img_to_braille.py \
  --input ~/.hermes/assets/theme/mylogo.png \
  --width 30 --height 15 \
  --palette gold \
  --out-preview

# Once happy with shape, generate YAML value:
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/img_to_braille.py \
  --input ~/.hermes/assets/theme/mylogo.png \
  --width 30 --height 15 \
  --palette gold \
  --out-yaml
```

**4c. Or generate ASCII ramp art (classic/retro style)**

```bash
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/image_to_hero.py \
  ~/.hermes/assets/theme/mylogo.png \
  --ramp classic \
  --palette gold \
  --plain
```

### Phase 5 — Write the Skin YAML

```bash
mkdir -p ~/.hermes/skins
```

Create `~/.hermes/skins/myskin.yaml`. Minimal example:

```yaml
name: myskin
description: "My custom theme"

colors:
  banner_border:   "#8c1a2e"
  banner_title:    "#c9a227"
  banner_accent:   "#c9a227"
  banner_dim:      "#5a3a0a"
  banner_text:     "#e8dcc8"
  ui_accent:       "#c9a227"
  response_border: "#c9a227"
  input_rule:      "#8c1a2e"
  prompt:          "#e8dcc8"

branding:
  agent_name:     "YourName"
  welcome:        "Your welcome message"
  goodbye:        "Your goodbye message"
  prompt_symbol:  "> "

banner_hero: "paste output from img_to_braille.py here"
```

See `examples/dragonfable.yaml` for a fully worked example.

**⚠️ Critical — don't use regex to update banner fields.** These fields are single-line
YAML scalars with embedded `\n` escapes and Rich markup. `re.sub` corrupts them.
Always rebuild the full YAML from a template string and overwrite the file.

### Phase 6 — Activate and Iterate

```bash
# Activate in current Hermes session (no restart needed)
/skin myskin

# Make permanent — edit ~/.hermes/config.yaml and add:
#   display:
#     skin: myskin
# Don't use >> append — running it twice creates duplicate keys.
```

**Common issues:**

| Symptom | Cause | Fix |
|---|---|---|
| Banner drifts / jagged lines | Spaces trimmed by `trimEnd()` | Ensure scripts use `⠀` (U+2800) not ASCII spaces |
| Colored feature invisible (e.g. red gem) | Grayscale-only mask silently drops saturated dark colors | Use `--lum-threshold 90 --red-ratio-g 1.2` |
| Block chars look double-wide | `░▒▓█` ambiguous-width on your terminal | Switch to `--ramp classic` or use Braille |
| Logo not centered | `banner_logo` is not auto-centered by renderer | Strip leading gutter or pad symmetrically |
| YAML parse error | Regex-patched a banner field | Rebuild entire YAML from template string |

---

# Part 2 — Desktop Ricing (KDE, Hyprland, GTK)

### Quick Start

```bash
# 1. Install dependencies
bash ~/.hermes/skills/hermes-ricer/scripts/setup.sh

# 2. Capture your current desktop state (READ-ONLY, always safe)
python3 ~/.hermes/skills/hermes-ricer/scripts/desktop_state_audit.py

# 3. Dry-run a preset (no changes made)
ricer preset void-dragon --dry-run

# 4. Apply
python3 ~/.hermes/skills/hermes-ricer/scripts/deterministic_ricing_session.py --preset void-dragon

# 5. Undo if needed
python3 ~/.hermes/skills/hermes-ricer/scripts/deterministic_ricing_session.py --rollback
```

### What Gets Themed

| Layer | Controls | Tool |
|---|---|---|
| **Colorscheme** | Qt window borders, titlebars, system menus | `plasma-apply-colorscheme` |
| **Kvantum** | Buttons, scrollbars, dropdowns, checkboxes | `kvantum.kvconfig` |
| **Plasma theme** | Panel background, tooltips, dialogs | `plasma-apply-desktoptheme` |
| **Cursor** | Mouse cursor theme | `plasma-apply-cursortheme` |
| **Konsole** | Terminal colors and profiles | `.profile` + `.colorscheme` |
| **Wallpaper** | Per-monitor wallpaper and fill mode | `plasma-apply-wallpaperimage` |

### Built-in Presets

| Name | Description |
|---|---|
| `catppuccin-mocha` | Soothing pastel dark |
| `nord` | Arctic blue |
| `gruvbox-dark` | Retro groove warm |
| `dracula` | Vibrant neon purple |
| `tokyo-night` | Dark cyberpunk |
| `rose-pine` | Soft nature pastels |
| `solarized-dark` | Low-contrast warm |
| `doom-knight` | Gothic gold and crimson |
| `void-dragon` | Void sky, cyan blade, gold filigree |

### Sub-Skills (Deep Reference)

Load these alongside `hermes-ricer` when you need platform-specific detail:

- `ricer-kde` — Kvantum widget styles, panel SVG rules, Qt renderer limitations, live reload safety
- `ricer-gtk` — GTK theme integration with KDE
- `ricer-apps` — Kitty, Rofi, Waybar, and other app-level configs
- `ricer-wallpaper` — Wallpaper generation and palette extraction
- `ricer-rollback` — Rollback architecture and the 3-layer backup system
- `ricer-catalog-capture` — Screenshot catalog workflow for ricing options
- `hyprland-rice-from-scratch` — Full Hyprland tiling WM setup guide

### Safety Model

The ricer suite is built on one rule: **every change must be reversible, audited, and reproducible.**

```
Capture baseline → Dry-run → Review diff → Apply → Verify → Rollback if needed
```

Three backup layers protect you:
1. **Git** — tracks the scripts themselves (`~/.hermes/skills/hermes-ricer/`)
2. **Pre-flight backups** — timestamped copies of all affected configs before every apply
3. **Immutable baselines** — complete desktop state snapshots from `desktop_state_audit.py`

---

## Prompt Chains

### CLI Skinning

> *"Install the hermes-cli-skin skill and create a [description] skin called 'mytheme'. I have Nerd Fonts."*

> *"Generate a 30×15 Braille banner_hero from this image, preview first, then write the full skin YAML."*

### Desktop Ricing

> *"Load hermes-ricer and run a dry-run of the void-dragon preset. Show me what would change."*

> *"Capture my current KDE desktop state, then apply the doom-knight preset with a custom wallpaper."*

---

## Contributing

PRs welcome:
- Add your skin YAML to `examples/`
- Add new presets to `hermes-ricer/templates/`
- Update any `SKILL.md` with new pitfalls you discover
- Add sample images to `assets/sample_images/` (CC0 only)

---

## Sources

- `hermes-cli-skin` skill: developed through real-world Hermes sessions (this repo)
- `hermes-ricer` suite: developed through real-world KDE/Hyprland ricing sessions (this repo)
- Hermes core + built-in skins: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
- Braille Unicode encoding reference: [Braille Patterns (Wikipedia)](https://en.wikipedia.org/wiki/Braille_Patterns)
- ASCII art ramps: [Paul Bourke's character ramp](http://paulbourke.net/dataformats/asciiart/)
