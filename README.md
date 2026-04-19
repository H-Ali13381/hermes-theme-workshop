# hermes-theme-workshop

**A complete recipe for setting up custom Hermes agent themes**, extracted from iterative
real-world usage. Includes updated skills, Braille-first ASCII art tools, and worked examples.

---

## What's Here

```
hermes-theme-workshop/
├── README.md                            ← this file (the recipe)
├── skills/
│   ├── hermes-cli-skin/
│   │   ├── SKILL.md                     ← full skill definition (install this)
│   │   └── scripts/
│   │       ├── img_to_braille.py        ← Braille art generator (recommended)
│   │       └── image_to_hero.py         ← ASCII ramp generator (classic style)
│   └── theme-factory/
│       └── SKILL.md                     ← artifact theming skill (slides/docs/HTML)
├── examples/
│   └── dragonfable.yaml                 ← complete working skin example
└── assets/
    └── sample_images/                   ← CC0 reference images to get started
```

> **Two separate theming systems exist in Hermes.** This repo covers both:
> - `hermes-cli-skin` — changes how the **terminal/CLI looks** (colors, prompt, banner art)
> - `theme-factory` — styles output **artifacts** (HTML pages, slides, docs)
>
> If you want to change how Hermes *looks when running*, you want `hermes-cli-skin`.

---

## The Recipe (Step-by-Step)

### Phase 1 — Install the Skills

**1a. Find the source repos**

There are two official sources for Hermes skills:
- [`anthropics/skills`](https://github.com/anthropics/skills) — community skills including `theme-factory`
- [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent) — core Hermes repo; built-in skins live there

The `hermes-cli-skin` skill (in this repo) was developed through iterative real-world usage
and is not yet in either official repo. **Install it from here.**

**1b. Install skills from this repo**

```bash
mkdir -p ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts

# Copy the skill definition
cp skills/hermes-cli-skin/SKILL.md ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/

# Copy the scripts
cp skills/hermes-cli-skin/scripts/img_to_braille.py \
   skills/hermes-cli-skin/scripts/image_to_hero.py \
   ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/
```

Verify Hermes sees it — in a Hermes session:
```
/skills
```
You should see `hermes-cli-skin` listed.

**1c. Install theme-factory (for artifact styling)**

```bash
git clone https://github.com/anthropics/skills /tmp/anthropics-skills
mkdir -p ~/.hermes/skills/
cp -r /tmp/anthropics-skills/skills/theme-factory ~/.hermes/skills/
```

---

### Phase 2 — Understand Your Environment

Before generating art, tell your Hermes agent:

> *"Update the hermes-cli-skin skill to reflect my environment:*
> - *Hermes skins go in `~/.hermes/skins/`*
> - *Config is at `~/.hermes/config.yaml`*
> - *Python with Pillow+numpy is available at `/usr/bin/python3`*
> - *Skills are in `~/.hermes/skills/`"*

The skill already contains correct paths, but environment quirks vary (Arch vs. Debian,
Nerd Font vs. stock terminal, etc.). Telling the agent upfront avoids a round of
path-not-found errors.

---

### Phase 3 — Choose a Theme Direction

Tell your agent what look you want. Be specific:
- **Color palette** — dark/moody, bright/neon, gold/fantasy, tech-blue, etc.
- **Tone** — playful, serious, dramatic, minimal
- **Reference** — a game, a character, a logo, a color hex code
- **Terminal font** — if you have Nerd Fonts installed, say so (unlocks braille safely)

Example prompt:
> *"Create a DragonFable-themed skin — dark background, gold and crimson accents,
> fantasy/RPG tone. I have Nerd Fonts installed."*

---

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
# Download a clean logo or reference image
wget -O ~/.hermes/assets/theme/mylogo.png "https://example.com/logo.png"
```

Good sources:
- Your project/game logo on a transparent background (PNG preferred)
- High-contrast portraits or mascots
- CC0 images from [Unsplash](https://unsplash.com), [OpenGameArt](https://opengameart.org), [Pixabay](https://pixabay.com)
- Sample images in `assets/sample_images/` of this repo

**4b. Generate Braille art (recommended)**

```bash
# banner_hero (30×15) — the small hero beside the tools list
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/img_to_braille.py \
  --input ~/.hermes/assets/theme/mylogo.png \
  --width 30 --height 15 \
  --palette gold \
  --out-preview   # preview first — approve shape before colorizing

# Once happy with shape, generate YAML value:
python3 ... --out-yaml
```

**4c. Or generate ASCII ramp art (classic/retro style)**

```bash
python3 ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/scripts/image_to_hero.py \
  ~/.hermes/assets/theme/mylogo.png \
  --ramp classic \    # or: doom, blocky
  --palette gold \
  --plain             # preview first
```

**4d. Always preview before installing**

The scripts print framed previews. Review the shape before writing YAML.
Iterate ramp/palette/threshold until you're happy — it's cheaper than editing
installed YAML files.

---

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

---

### Phase 6 — Activate and Iterate

```bash
# Activate in current Hermes session (no restart needed)
/skin myskin

# Make permanent
echo "display:" >> ~/.hermes/config.yaml
echo "  skin: myskin" >> ~/.hermes/config.yaml
```

**Check for common issues:**

| Symptom | Cause | Fix |
|---|---|---|
| Banner drifts / jagged lines | Spaces trimmed by `trimEnd()` | Ensure scripts use `⠀` (U+2800) not ASCII spaces |
| Colored feature invisible (e.g. red gem) | Grayscale-only mask silently drops saturated dark colors | Use `--lum-threshold 90 --red-ratio-g 1.2` to loosen mask |
| Block chars look double-wide | `░▒▓█` ambiguous-width on your terminal | Switch to `--ramp classic` or use Braille |
| Logo not centered | `banner_logo` is not auto-centered by renderer | Strip leading gutter or pad symmetrically |
| YAML parse error | Regex-patched a banner field | Rebuild entire YAML from template string |

---

### Phase 7 — Play and Refine

Taste is iterative. Common refinement loop:

1. `/skin myskin` — see current state
2. Adjust color hex values for vibe
3. Regenerate art with different palette/threshold if needed
4. Rewrite YAML with `write_file` (not regex patch)
5. `/skin myskin` again

Keep old builder script versions (v1, v2, ...) in `/tmp/` while iterating — easy revert.

---

## Asking Your Agent

Here's the full prompt chain that reliably produces good results:

**Step 1 — Install skills**
> *"Install the hermes-cli-skin skill from ~/Documents/SideProjects/hermes-theme-workshop/skills/hermes-cli-skin/ into ~/.hermes/skills/autonomous-ai-agents/hermes-cli-skin/"*

**Step 2 — Load and orient**
> *"Load the hermes-cli-skin skill and tell me what it recommends for generating banner art."*

**Step 3 — Pick a theme direction**
> *"I want a [theme description] theme. My terminal has Nerd Fonts. Create a skin YAML called 'mytheme'."*

**Step 4 — Generate art from an image**
> *"Download a [description] image and generate a 30×15 Braille banner_hero from it using img_to_braille.py. Show me a preview first."*

**Step 5 — Install and verify**
> *"Write the complete skin YAML to ~/.hermes/skins/mytheme.yaml and activate it with /skin mytheme"*

**Step 6 — Iterate**
> *"The red part is invisible. Try --lum-threshold 90 --red-ratio-g 1.2 and regenerate."*

---

## Contributing

If you build a great skin or discover new pitfalls, PRs are welcome:
- Add your skin YAML to `examples/`
- Update `SKILL.md` with any new pitfalls you hit
- Add sample images to `assets/sample_images/` (CC0 only)

---

## Sources

- `hermes-cli-skin` skill: developed through real-world Hermes sessions (this repo)
- `theme-factory` skill: [`anthropics/skills`](https://github.com/anthropics/skills)
- Hermes core + built-in skins: [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent)
- Braille Unicode encoding reference: [Braille Patterns (Wikipedia)](https://en.wikipedia.org/wiki/Braille_Patterns)
- ASCII art ramps: [Paul Bourke's character ramp](http://paulbourke.net/dataformats/asciiart/)
