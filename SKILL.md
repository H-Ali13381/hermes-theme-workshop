---
title: Linux Ricing
description: AI-native Linux desktop design system. The agent acts as designer — auditing the user's machine, exploring creative directions, generating mockups, and implementing a fully personalized desktop end-to-end. The user is the art/UX director.
trigger: User wants to theme/rice their Linux desktop, mentions changing colors/wallpaper/bar/launcher appearance, asks what their desktop could look like, or invokes /rice.
version: 3.0.0
tags: [linux, ricing, theming, desktop, hyprland, kde, waybar, rofi, kitty, animated-wallpaper, generative]
---

# Linux Ricing — AI-Native Desktop Design System

## 1. Philosophy

> *The agent is the designer. The user is the art/UX director.*

An OS is the membrane between a human mind and raw computation. The desktop is the only part most people ever touch — it is the face of the machine. Most software assumes you will adapt to it. **Ricing inverts that.**

This skill does not apply color schemes. It helps a person make their machine feel like *theirs* — possibly in ways they haven't consciously imagined yet.

**The agent behaves like a skilled designer:**
- Audits the machine silently before asking any questions
- Gathers a brief through a structured creative conversation
- Makes bold aesthetic choices and explains the rationale
- Explores widely before converging on a single direction
- Implements element-by-element with confirmation at each step
- Delivers a handoff document: every changed hotkey, every design decision, every quirk

The user should never have to know what a `kvantum.kvconfig` file is.

**Full design philosophy → `dev/DESIGN_PHILOSOPHY.md`**

---

## 2. Session Workflow (8 Steps)

When this skill is triggered, follow these steps in order. Do not skip steps.

### Pre-flight — Resume Detection
**Before anything else**, check for incomplete sessions:

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py resume-check
```

Returns a JSON list. If any results:
> *"I found an incomplete rice session from [started] — '[theme]', [status]. Want to pick up where we left off, or start fresh?"*

- **Resume** → load the session and read it fully:
  ```bash
  python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py load <session-dir>
  python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py read
  ```
  Load `design.json` from the session dir if present, then skip to the next incomplete step.
- **Start fresh** → init a new session:
  ```bash
  python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py init
  ```

Full session state spec → `dev/DESIGN_PHILOSOPHY.md §Session State & Persistence`

---

### Step 1 — Audit (Silent, Parallel)
Before asking any questions, read the machine. Detect:

**Device profile:**
- Laptop or desktop? (`cat /sys/class/dmi/id/chassis_type` — 8/9/10/14 = laptop; check for battery: `ls /sys/class/power_supply/`)
- Screen count and resolution (`xrandr` or `hyprctl monitors`)
- Touchpad present? (`libinput list-devices | grep -i touchpad`)
- GPU and VRAM (`glxinfo` or `nvidia-smi` or `vainfo`)

**Environment:**
- Window manager and compositor
- Installed apps: terminal, browser, editor, games (check Steam playtime)
- Current wallpaper (analyze visually)
- Existing theme: colors, fonts, GTK/icon theme
- Current hotkeys and panel/toolbar layout
- `USER.md` / `SOUL.md` / `MEMORY.md` if present
- Animated wallpaper engine: `swww`, `mpvpaper`, `xwinwrap`, `komorebi`, `waypaper`, KDE built-in, Wallpaper Engine via Steam/Wine
- `FAL_KEY` set in Hermes? (needed for wallpaper generation)

**Device signals feed design decisions:**

| Signal | Implication |
|--------|-------------|
| Laptop, single screen | Screen real estate is scarce. Favor minimal chrome, auto-hiding panels, Hyprland tiling. Keyboard-centric workflow assumed. |
| Laptop + touchpad | Ask in Step 2: *"Do you use the touchpad heavily, or mostly keyboard?"* Touchpad-heavy → gestures worth configuring (swipe workspaces, pinch zoom). |
| Desktop, single screen | More chrome acceptable. KDE or Hyprland both viable. |
| Desktop, multi-monitor | Rich panel/bar setup makes sense. Per-monitor workspace layouts. KDE's multi-monitor support is strong. Waybar with per-output config on Hyprland. |
| Low VRAM / integrated GPU | Avoid heavy blur/compositor effects. Suggest `picom` with minimal config or Hyprland with effects disabled. |
| High-end GPU | Animations, blur, custom shaders, animated wallpaper all viable. |

Audit runs in the background. The user experiences a creative conversation, not a system scan.

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 1 \
  "device=<laptop|desktop>" "screens=<count>" "GPU=<model>" "WM=<wm>" \
  "animated_wallpaper_engine=<name|none>" "FAL_KEY=<set|not set>" \
  "stance_hypothesis=<stance guess>"
```

### Step 2 — Explore (Chaos Phase)
**Fan out hard.** This is the most important step.

**Layer 1 — Mandatory questions (ask every user, in order):**
1. *What do you want to feel when you sit down at your machine?*
2. *What do you actually use this machine for most?* (dev, gaming, creative, work)
3. *How much change are you comfortable with?* (light polish → full transformation)
4. *Anything sacred — hotkeys, layouts, apps that must not be touched?*
5. *Any hard constraints?* (accessibility, color blindness, low-spec hardware)

**Layer 2 — Hypothesis confirmations (audit-derived):**
Make guesses from the audit and present them as leading questions:
- *"I see 300+ hours in Hollow Knight — want to go somewhere dark and atmospheric?"*
- *"You're running Neovim + tmux — want the theme to center around your terminal?"*
- *"You have Vesktop installed — sync the Discord theme with the rest of the desktop?"*

**Stance framing:** Use the Design Stance Model (see §1 + `dev/DESIGN_PHILOSOPHY.md`) to reflect the user's preferences back at them — not as a menu, as a hypothesis:
> *"From what you've described, it sounds like somewhere between Ghost and Blade — legible and a little adversarial. Does that track?"*

**Creative tools — use all of them:**
- Spin up subagents at high temperature for wild, unexpected ideas
- `mcp_image_generate` to show reference images, not just describe them
- Web search for visual references (games, films, art movements)
- Mine recurring obsessions from audit (games, animals, aesthetics)

Chaos is good here. More ideas is better. Nothing is eliminated yet.

**Animated wallpaper question:** If an animated engine is detected OR installable, ask: *"Do you want an animated wallpaper that changes with the time of day?"* See §14 for the full pipeline.

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 2 \
  "stance_settled=<stance>" "reference_anchor=<game/film/scene>" \
  "diegesis_mode=<non-diegetic|diegetic|meta>" "animated_wallpaper=<yes/no, engine>" \
  "sacred_items=<hotkeys/apps>" "key_ideas=<bullet summary>"
```

### Step 3 — Refine
Through discussion, eliminate less interesting ideas. Converge on one theme with:
- A **name** (evocative — "Midnight Garden", not "dark-blue-v2")
- A **mood** (2–3 adjectives)
- A **reference anchor** (image, game, film, scene)
- A **stance** (one of the Seven Stances or a named blend)
- Rough **scope** (which elements will change)

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 3 \
  "theme_name=<name>" "mood=<2-3 adjectives>" "reference_anchor=<final>" \
  "stance=<final stance or blend>" "scope=<elements that will change>"
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py rename <theme-slug>
```
Then write `design.json` to the session dir.

### Step 4 — Present Plan
Generate a **static HTML visual preview page** with:
- Theme name, mood, reference anchor, and stance
- **Actual visual mockups**: wallpaper, desktop layout, widgets, color palette, bar/panel, launcher, lock screen
- Animated wallpaper preview if applicable
- Full list of planned changes (every app, every element)
- Links to packages that need installing
- New hotkeys/shortcuts that will result

**Hard requirement: a text plan is NOT a preview.** The user must be able to open and visually judge the concept before implementation. At minimum, create:
- `preview.html` or `plan.html` in the session dir
- at least one real image mockup (`preview-mockup.png`, generated image, screenshot composite, SVG render, or CSS/HTML mockup)
- a palette board rendered visually, not only hex values

If image generation is unavailable or produces unusable output, build a CSS/SVG mockup manually. Do not proceed to rollback/apply with only prose.

**Verification before approval:**
1. Save all preview assets in the session dir.
2. Start a local preview server or provide direct file paths.
3. Open/render the page with browser/vision or an equivalent check.
4. Confirm images are not broken and the mockup shows the planned UI elements.
5. Tell the user the exact URL/path to open.

→ *Not right?* Go back to **Step 2** (not Step 3 — re-explore, don't just prune)

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 4 \
  "preview_html=<path-or-url>" "preview_mockup=<path>" \
  "packages_to_install=<list>" "new_hotkeys=<list or none>" \
  "user_approval=<pending|confirmed>"
```
Save the preview page and assets to the session dir.

**Approval gate:** Step 4 must remain `user_approval=pending` until the user has been shown the exact URL/path and has approved the visual direction. Do not run Step 4.5 rollback or any dry-run/apply step before the visual preview is verified and presented.

### Step 4.5 — Rollback Checkpoint
**No implementation begins without this.**
```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/desktop_state_audit.py
```
Inform the user: *"Rollback point set at `~/.cache/linux-ricing/baselines/<timestamp>/`. You can return to this state at any time with `ricer undo`."*

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 4.5 \
  "baseline=~/.cache/linux-ricing/baselines/<timestamp>"
```

### Step 5 — Install
List every package that will be installed and why. Explain sudo requirements upfront. Wait for user review before running anything.

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 5 \
  "packages_installed=<list>" "errors=<none or description>"
```

### Step 6 — Implement
Run `ricer preset <name> --dry-run` (or `ricer apply --design <file> --dry-run`) first — preview all changes without writing anything. Show the user the dry-run output.

#### Preview-as-Canvas Implementation Contract (mandatory gate)

Before touching any config, treat the Step 4 visual artifacts as the **source of truth** for what the desktop must look like. The agent's job in Step 6 is to make the live system converge on the preview — not to ship a freehand interpretation that "captures the vibe."

1. **Load the contract.** If `<session-dir>/implementation-contract.md` exists, read it in full. It overrides anything inferred from `design.json` or prose. If it does not exist, derive the contract from the approved artifacts in priority order:
   1. `<session-dir>/preview.html` (or `plan.html`)
   2. `<session-dir>/preview-mockup*.png` (and any other approved mockup images)
   3. `<session-dir>/design.json`
   4. The session.md notes from Steps 2–4

2. **Enumerate the elements.** From the preview, list every element that must be reproduced (panel, launcher, terminal, lock screen, widgets, wallpaper, cursor, fastfetch, GTK chrome, Hermes skin, …). Cross-check against the §11 Quality Bar checklist — anything in the preview that has no checklist entry is an extra item; anything in the checklist not in the preview is either out of scope or a gap to flag to the user before proceeding.

3. **One element at a time.** For each element, in this order:
   1. **Element spec** — write a short spec (4–10 lines) before editing any file: target file(s), exact colors / fonts / radii / spacing pulled from the preview, behavior (auto-hide, blur, opacity), and what "matches the preview" looks like in concrete terms. Save inline in session.md via `append-item` so the spec is auditable. Element specs are the smallest unit of work — never edit before one exists.
   2. **Apply** — materialize via `ricer` or the relevant materializer (see §4, §9).
   3. **Verify visually** — capture or render the live element and compare to the preview asset. Use a screenshot + vision check, a side-by-side diff, or `kscreen-doctor`/`hyprctl` introspection where the element is non-visual (logical geometry, scale).
   4. **Score** — rate the live element against the preview using the 5-category scorecard below. Each category is 0–2 (0 = miss, 1 = partial, 2 = match); report all five plus the total /10:
      - **Palette** — color match, contrast, accent placement
      - **Shape** — geometry, layout, alignment, radii, chrome silhouette
      - **Diegesis** — fit with the chosen stance / world / fictional frame
      - **Usability** — legibility, hover/focus states, hit targets, no regressions
      - **Preview integration** — overall fidelity to the approved mockup as a single artifact
   5. **Gate** — minimum **8/10 total** to mark the element ✓ verified. If the total is below 8/10, either iterate until it clears or surface the deviation to the user with the specific gap and ask them to accept it explicitly. Record the user's acceptance in session.md (`append-item`) — silent skips are not allowed.

4. **No silent skips.** Every checklist item from §11 ends Step 6 in one of three states: ✓ verified (≥8/10 total), ✓ accepted-deviation (user explicitly accepted lower score, with the gap recorded), or SKIP with a written reason logged via `append-item`. "I forgot" / "ran out of time" / "looked close enough" are not reasons.

5. **Re-explore on structural mismatch.** If the live element cannot reach the preview (e.g., the preview shows a textured panel that Plasma's SVG renderer cannot produce — see `KDE/plasma-panel.md`), do not silently downgrade. Stop, present the limitation to the user with the alternatives (e.g., Plasma theme SVG vs EWW overlay vs accepted limitation), and re-enter the contract with the user's choice recorded.

Never batch multiple elements into one unverified step.

#### AI Wallpaper Prompt Hygiene
- NEVER use trigger words like "NFT", "collection", "brand", "logo" in image generation prompts — the model will literally render them as text in the image.
- Always include "No text, no words, no watermarks, no logos" in wallpaper prompts.
- If the user describes an aesthetic as "like NFTs" or "like crypto art", translate to the actual visual properties: "iridescent", "chromatic aberration", "generative algorithmic patterns", "holographic gradients".
- Vision-check generated wallpapers before applying if the vision tool is available.

#### Logging element progress

`session_manager.py` `append-item` only takes free-form text (no key=value parsing). Encode the spec, score, and verdict inside the text itself. After each verified element:

```bash
# Element spec (write before editing files)
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-item \
  "<element> spec: targets=<files> palette=<keys> font=<family/size> radii=<px> behavior=<notes>"

# Verdict (write after the score gate clears)
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-item \
  "<element>: <what changed> — score palette=2 shape=2 diegesis=1 usability=2 preview=2 (9/10) — ✓ verified"

# Accepted-deviation (only when the user explicitly accepts a sub-8 total)
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-item \
  "<element>: <what changed> — score <…> (<n>/10) — ✓ accepted-deviation: <gap> (user OK)"

# Skip (must include a real reason — never silent)
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-item \
  "<element>: SKIP — <reason: not in preview / hardware unsupported / user descoped>"
```

When all elements are done, close the step:
```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 6
```

### Step 7 — Cleanup
- Sweep all modified config files for syntax errors
- Check for broken includes or missing files
- Verify all services/daemons reloaded correctly
- Run final desktop state audit, compare to pre-session baseline

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 7 \
  "config_syntax_errors=<none or list>" "services_reloaded=<list>" \
  "post_session_audit=<passed or delta>"
```

### Step 8 — Handoff Document
Generate in **both Markdown and HTML**. Save to session dir:
- `~/.config/rice-sessions/<theme-name>-<date>/handoff.md`
- `~/.config/rice-sessions/<theme-name>-<date>/handoff.html`

**Contents:**
- Theme name, date, stance, session summary
- Every changed hotkey and shortcut (old → new)
- Every changed config file (path + what changed + why)
- Design decisions with rationale
- Known quirks and workarounds
- How to roll back
- What was intentionally left unchanged and why

The HTML version should render the color palette visually and include before/after screenshots where possible.

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py append-step 8 \
  "handoff_md=written" "handoff_html=written"
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py complete
```

---

## 3. Architecture Overview

```
Input (prompt / image / preset)
    │
    ▼
[Design System Generator] ─→ design_system.json (10-key palette + metadata)
    │
    ▼
[Discovery Layer] ─→ detect distro, WM, session type, installed apps
    │
    ▼
[Template Engine] ─→ render app config fragments from palette
    │
    ▼
[Materialization Layer] ─→ backup old state, write fragments, inject includes
    │
    ▼
[Activation Layer] ─→ signal/reload apps (KWin reconfigure, SIGUSR1, pkill, etc.)
    │
    ▼
[Rollback Layer] ─→ manifest saved to ~/.cache/linux-ricing/current/manifest.json
```

**Safety guarantees:**
- Theme fragments are written alongside main configs; includes are injected with `# linux-ricing` markers
- Backups are created before every change in `~/.cache/linux-ricing/backups/<timestamp>/`
- `--dry-run` previews all changes without writing anything
- `simulate-undo` shows exactly what rollback would do
- 4-layer rollback architecture (GitHub dotfiles → ~/.hermes git → ricer.py backups → immutable baselines)

---

## 4. Technical Workflow — ricer.py

When building a rice from scratch or applying a theme:

1. **Environment discovery** — detect distro, WM/DE, session type, installed apps (see §5)
2. **Route to environment** — KDE → `KDE/` docs, Hyprland → `Hyprland/` docs
3. **Select or generate design system** — preset name, text prompt, or image extraction
4. **Install missing packages** — adapt package names for detected package manager (see §10)
5. **Dry-run** — `ricer preset <name> --dry-run` to preview all changes
6. **Apply** — materialize configs for all detected targets (terminal, bar, launcher, notifications, WM borders, GTK, wallpaper, lock screen, fastfetch)
7. **Verify** — visual check of each layer; `ricer status` for summary
8. **Iterate** — one component at a time with user confirmation between steps
9. **Confirm rollback** — `ricer simulate-undo` to verify restore plan

Always iterate one component at a time with user confirmation between each step.

---

## 5. Environment Discovery

Run before any ricing work to detect the user's stack:

```bash
cat /etc/os-release                          # distro + package manager
echo $XDG_SESSION_TYPE                       # x11 or wayland
echo $XDG_CURRENT_DESKTOP                    # GNOME, KDE, Hyprland, etc.
ps -e | grep -E 'i3|sway|bspwm|dwm|qtile|hyprland|gnome-shell|plasmashell|xfwm4|openbox'

# Package manager
command -v pacman && echo arch
command -v apt    && echo debian/ubuntu
command -v dnf    && echo fedora
command -v zypper && echo opensuse
command -v xbps-install && echo void
```

### Routing by session

| Session | Route to | Key tools |
|---------|----------|-----------|
| **KDE Plasma** (plasmashell running) | `KDE/` | plasma-apply-colorscheme, Kvantum, kwriteconfig6, qdbus6 |
| **Hyprland** (hyprctl on PATH) | `Hyprland/` | hyprctl, waybar, rofi, dunst, awww, hyprlock |
| **Sway / i3 / bspwm** | `shared/` + X11 stack | polybar/waybar, rofi, picom, feh |

### Cross-environment rules
- **Dunst conflicts with KDE's notification server** — write dunst config but don't start the daemon when plasmashell is active
- **Waybar is redundant on KDE** — KDE has its own panel; don't start waybar when plasmashell is running
- **KDE sub-systems** (Kvantum, plasma_theme, cursor) have no standalone binary — register them explicitly in `discover_apps()` when KDE is detected

---

## 6. Directory Layout

```
~/.hermes/skills/creative/linux-ricing/
├── SKILL.md                  ← you are here (entry point)
├── QUICKSTART.md             ← zero-to-themed-desktop in 5 minutes
├── shared/                   ← cross-environment docs & app theming
│   ├── design-system.md      ← 10-key palette schema, ANSI mapping, color derivation
│   ├── palette-extraction.md ← image → palette (4 vision passes + Pillow algorithm)
│   ├── wallpaper-generation.md ← AI wallpaper gen, fal.ai style transfer, UI chrome
│   ├── widgets.md             ← EWW setup, AI→widget pipeline, image slicing, hover patterns
│   ├── rollback.md           ← 4-layer backup architecture, session protocol, presets
│   ├── gtk.md                ← GTK 3/4 theming (works under KDE & Hyprland)
│   ├── terminal.md           ← kitty, alacritty color mapping & config
│   ├── shell-prompt.md       ← starship, powerlevel10k, fzf theming
│   ├── waybar.md             ← waybar config, CSS, @import injection
│   ├── rofi.md               ← rofi rasi themes, power menu script
│   ├── dunst.md              ← dunst INI config, DBus conflict handling
│   ├── templates.md          ← all Jinja2 template dirs documented
│   ├── catalog-capture.md    ← screenshot catalog for theme comparison
│   ├── hermes-skin.md        ← sync Hermes agent CLI theme with desktop palette
│   ├── braille-art.md        ← image → braille conversion pipeline
│   └── fastfetch.md          ← system info tool theming + custom logos
├── KDE/                      ← KDE Plasma-specific docs
│   ├── setup.md              ← 5-layer stack, discover_apps(), live reload
│   ├── colorscheme.md        ← .colors format, generation, activation
│   ├── kvantum.md            ← widget style, catppuccin themes, Qt SVG limits
│   ├── plasma-panel.md       ← Plasma theme SVGs, element IDs, textures
│   ├── cursor.md             ← cursor theme install & activation
│   ├── splash-screen.md      ← KDE splash customization
│   ├── konsole.md            ← Konsole colorscheme format
│   └── wallpaper.md          ← plasma-apply-wallpaperimage
│   ├── widgets.md            ← EWW on KDE, Plasmoid alternative
├── Hyprland/                 ← Hyprland-specific docs
│   ├── setup.md              ← full rice from scratch on Arch
│   ├── borders-animations.md ← border gradients, gaps, animation curves
│   ├── hyprlock.md           ← lock screen config, hypridle
│   ├── wallpaper.md          ← awww daemon, multi-monitor, DPMS fix
│   ├── fastfetch.md          ← Hyprland-specific modules (→ shared/fastfetch.md)
│   ├── waybar.md             ← Hyprland-specific: workspace modules, autostart
│   ├── rofi.md               ← Hyprland-specific: keybindings
│   ├── dunst.md              ← Hyprland-specific: autostart, plasmashell conflict
│   ├── widgets.md            ← EWW on Hyprland: layer rules, workspace integration
├── scripts/
│   ├── ricer.py              ← main Python driver (CLI)
│   ├── palette_extractor.py  ← Pillow-based image → palette
│   ├── deterministic_ricing_session.py ← enforced safety protocol
│   ├── desktop_state_audit.py          ← immutable baseline capture
│   ├── capture_theme_references.py     ← catalog screenshot automation
│   ├── reference_capture_window.py     ← PyQt6 widget showcase for captures
│   ├── generate_panel_svg.py           ← SVG panel generation
│   └── setup.sh              ← first-time setup
├── templates/                ← Jinja2 config templates (see shared/templates.md)
│   └── kitty/ waybar/ rofi/ dunst/ gtk/ alacritty/ hyprland/
│       kde/ polybar/ wofi/ mako/ swaync/ picom/
├── assets/
│   └── catalog/              ← captured theme comparison screenshots
├── tests/                    ← test suite
└── dev/                      ← internal development notes
    └── TODO.md
```

### Runtime directories

| Purpose | Path |
|---------|------|
| Active theme | `~/.cache/linux-ricing/current/` |
| Active manifest | `~/.cache/linux-ricing/current/manifest.json` |
| Manifest history | `~/.cache/linux-ricing/current/history/` |
| Backups | `~/.cache/linux-ricing/backups/<timestamp>/` |
| Baselines | `~/.cache/linux-ricing/baselines/<timestamp>_baseline.json` |
| Session logs | `~/.cache/linux-ricing/session_logs/` |
| CLI symlink | `~/.local/bin/ricer` → `scripts/ricer.py` |

---

## 7. Design System JSON Schema

Every theme — preset, extracted, or generated — is a **10-key palette** with metadata:

```json
{
  "name": "my-theme",
  "description": "One-sentence description.",
  "palette": {
    "background": "#0c1220",
    "foreground": "#e4f0ff",
    "primary":    "#7ad4f0",
    "secondary":  "#0d2e32",
    "accent":     "#d4a012",
    "surface":    "#1c1e2a",
    "muted":      "#3d2214",
    "danger":     "#cc3090",
    "success":    "#2a8060",
    "warning":    "#c87820"
  },
  "kvantum_theme": "catppuccin-mocha-teal",
  "cursor_theme": "catppuccin-macchiato-teal-cursors",
  "icon_theme": "Papirus-Dark",
  "gtk_theme": "Adwaita-dark",
  "mood_tags": ["dark", "dragon", "cyan"]
}
```

### Palette role semantics

| Key | Purpose |
|-----|---------|
| `background` | Window/terminal background |
| `foreground` | Primary text color |
| `primary` | Focused borders, active elements, links |
| `secondary` | Subtle accents, inactive borders |
| `accent` | Highlights, cursors, special elements |
| `surface` | Elevated surfaces (panels, inputs) |
| `muted` | Disabled text, subtle backgrounds |
| `danger` | Errors, destructive actions |
| `success` | Confirmations, healthy status |
| `warning` | Caution, non-critical alerts |

See `shared/design-system.md` for the full 10-key → 16 ANSI derivation algorithm.

### Required metadata keys

Every preset **must** include: `name`, `description`, `palette` (all 10 keys), `kvantum_theme`, `cursor_theme`, `icon_theme`, `gtk_theme`, `mood_tags`. Missing `kvantum_theme` silently falls back to `"kvantum-dark"` which is almost certainly not installed.

---

## 8. Available Presets

| Name | Description |
|------|-------------|
| `catppuccin-mocha` | Soothing pastel dark theme |
| `nord` | Arctic, north-bluish color palette |
| `gruvbox-dark` | Retro groove dark colors |
| `dracula` | Dark theme with vibrant colors |
| `tokyo-night` | Dark Tokyo-inspired blue/purple |
| `rose-pine` | Rose Piné — warm dawn theme |
| `doom-knight` | DragonFable DoomKnight — deep purples, battered gold, dark crimson |
| `void-dragon` | Void dragon knight — cyan soul blade, gold filigree, void sky |
| `bareblood` | Gothic maximalist — blood reds, wine blacks, muted rose-grey |

Apply: `ricer preset <name>` — Preview: `ricer preset <name> --dry-run`

---

## 9. ricer.py CLI Quick Reference

```
ricer discover                              # detect desktop stack and installed apps
ricer status                                # show active theme + detected stack
ricer presets                               # list built-in presets
ricer preset <name>                         # apply a named preset
ricer preset <name> --dry-run               # preview without writing anything
ricer apply --design <path>                 # apply a design_system.json file
ricer extract --image <path> [--out FILE] [--name NAME]
                                            # derive design_system from an image (Pillow)
ricer apply --wallpaper <path> --extract    # extract palette from image then apply full rice
ricer simulate-undo                         # show exactly what undo would restore
ricer undo                                  # restore previous state from manifest
```

### First-time setup

```bash
bash ~/.hermes/skills/creative/linux-ricing/scripts/setup.sh
```

Installs jinja2 + pillow (non-fatal on pip failure), chmod +x ricer.py, creates cache dirs, symlinks `ricer` into `~/.local/bin`. Verify: `ricer status`.

---

## 10. Package Installation by Distro

### Arch Linux (primary target)

**Core Hyprland stack:**
```bash
sudo pacman -S --noconfirm hyprland xdg-desktop-portal-hyprland uwsm \
  waybar rofi dunst kitty awww hyprlock hypridle \
  papirus-icon-theme ttf-jetbrains-mono-nerd otf-firamono-nerd \
  fastfetch wl-clipboard grim slurp brightnessctl playerctl \
  polkit-kde-agent qt5-wayland qt6-wayland nwg-look
```

**KDE theming tools:**
```bash
sudo pacman -S kvantum qt6ct
yay -S kvantum-theme-catppuccin-git    # AUR — Kvantum accent packs
```

### Package name gotchas
- `rofi-wayland` does NOT exist in Arch repos — use `rofi` (v2.0+ has native Wayland)
- `swww` does NOT exist in Arch repos — use `awww` (swww v0.12+ rename)
- `hyprpaper` v0.8.3 silently fails — use `awww` instead
- `org.kde.video` wallpaper plugin does NOT work on KDE Plasma 6 — the package is absent even if the plugin ID appears in qdbus output. Plasmashell logs "Error loading the wallpaper, no valid package loaded". Use AUR package `plasma6-wallpapers-smart-video-wallpaper-reborn` (`yay -S plasma6-wallpapers-smart-video-wallpaper-reborn`). Plugin ID: `luisbocanegra.smart.video.wallpaper.reborn`. Config key for video file is `VideoUrls` (NOT `VideoPath`). Requires `mpv` as backend. CRITICAL: plasmashell restart (e.g. after applying a colorscheme) resets the wallpaper — re-apply via qdbus after restart.

### Other distros

| Distro | Command |
|--------|---------|
| Debian/Ubuntu | `sudo apt update && sudo apt install -y <packages>` |
| Fedora | `sudo dnf install -y <packages>` |
| openSUSE | `sudo zypper install -y <packages>` |
| Void | `sudo xbps-install -S <packages>` |

If a package name differs across distros, check with `command -v <name>` first. For AUR: `yay -S` or `paru -S`.

### Dependencies

- Python 3.10+ (`list[str]`, `str | None` syntax)
- `jinja2` — templating (optional, fallback renderer built-in)
- `pillow` — image color extraction (optional, required for `ricer extract`)
- KDE tools (if KDE): `plasma-apply-colorscheme`, `plasma-apply-wallpaperimage`, `plasma-apply-cursortheme`, `kreadconfig6`/`kwriteconfig6`, `qdbus6`

---

## 11. Quality Bar — Theming Depth Checklist

**MANDATORY: Walk this list at Step 6. Every applicable item must end in one of three states — `✓ verified`, `✓ accepted-deviation`, or `SKIP <reason>` — logged to session.md via `append-item`. Silent skips are not allowed.**

Each `✓ verified` entry is gated by the **5-category /10 scorecard** from Step 6 (Palette, Shape, Diegesis, Usability, Preview integration; each 0–2). Minimum 8/10 total, or the user must explicitly accept the deviation. "Looks close enough" is not acceptance — the specific gap and the user's OK must be in the log.

**Every checked item requires scorecard evidence in the log** — a per-category breakdown plus total, written via `append-item`. A check mark without a recorded score is treated as a silent skip and must be redone. **`SKIP` is only valid with a written reason AND, where the item is in the approved preview, the user's explicit acceptance recorded in the same `append-item` entry.** "Not in preview" is a sufficient reason on its own; "ran out of time" / "looked close enough" / "user probably won't notice" are not.

Skipping items silently is the #1 failure mode of this skill. The agent tends to implement 6-7 items and declare victory. The user expects all of them. When in doubt, implement it — the rollback exists for a reason.

- [ ] **Terminal** (kitty/alacritty/konsole) — 16-color palette + font + opacity
- [ ] **Bar** (waybar/polybar) — CSS palette + border + font
- [ ] **Launcher** (rofi/wofi) — palette + border + radius
- [ ] **Notifications** (dunst/mako, or KDE native if Plasma) — urgency colors + frame
- [ ] **Window decorations** — Hyprland border gradient / KDE Aurorae / KDE colorscheme
- [ ] **GTK theme** — settings.ini + gtk.css for GTK3/GTK4 apps
- [ ] **Wallpaper** — AI-generated or palette-matched
- [ ] **Lock screen** (hyprlock / KDE lock) — full config rewrite with palette
- [ ] **Login/greeter** (SDDM) — matching background + colors
- [ ] **Fastfetch** — separator char + palette-colored keys + custom logo
- [ ] **Cursor + icon set** — matching installed theme
- [ ] **Shell prompt** (starship/p10k) — palette-aware symbols
- [ ] **Custom widgets** (EWW) — AI-designed UI elements with image textures
- [ ] **Hermes CLI skin** — agent's terminal appearance matches the palette

Minimum viable rice: 6 verified (each ≥8/10 total on the five-category scorecard). Total environment: 10+.

**Common items skipped and why they shouldn't be:**
- Fastfetch: takes <5 minutes, high visual impact when opening terminal
- Lock screen: user sees it every time they unlock, massive missed opportunity
- Shell prompt: starship config is 20 lines, transforms the terminal feel
- Hermes skin: the agent's own interface should match what it built

**Auditing your own work:** before declaring Step 6 done, re-read the Step 6 entries in session.md and confirm every checklist item above appears with one of the three terminal states. If an item is missing entirely from the log, that *is* a silent skip — go back and either implement it or log the SKIP with a reason.

---

## 12. Known Cross-Environment Pitfalls

### ANSI 16-Color Palette Collision
When `primary == warning` (e.g., doom-knight's gold), ANSI color4 (blue) becomes indistinguishable from color3 (yellow). Fix: swap color4 to `secondary` when this collision is detected. Implemented in both kitty and konsole materializers.

### Include Injection vs Full Rewrite
The default approach (write theme fragment + inject include) only works when the target config is vanilla/modular. If the config has hardcoded inline colors (e.g., a full kitty theme with all color0–15 defined), the include gets overridden. **Always check first** — `grep -c` for inline color definitions and do a full config rewrite when needed. See `shared/terminal.md` and the relevant app docs for per-app detection heuristics.

### KDE "Already Set" No-Op
`plasma-apply-colorscheme` does nothing if the scheme name matches the current one. Force re-application by bouncing to BreezeClassic first, then re-applying.

### KDE .colors Format
KDE .colors files require **decimal RGB** (`r,g,b`), NOT hex (`#rrggbb`). Writing hex produces a silently invalid colorscheme.

### Kvantum Widget Style
`widgetStyle=kvantum-dark` is WRONG and silently falls back to Breeze. Correct value: `widgetStyle=kvantum` (lowercase, no suffix).

### GTK Apps Require Restart
No live-reload for GTK — apps must be closed and reopened to pick up settings.ini changes.

### Hyprland + KDE Coexistence
When Hyprland launches on a KDE system, plasmashell may start in the background, squatting on the `org.freedesktop.Notifications` D-Bus name (blocking dunst) and causing monitor DPMS issues. Fix: `exec-once = pkill plasmashell; dunst`.

### awww Daemon Must Run First
`awww img` panics if awww-daemon isn't running. Always `pgrep awww-daemon || awww-daemon &; sleep 2` before setting wallpaper.

### KDE Video Wallpaper — org.kde.video is Fake
`org.kde.video` appears in `/usr/share/plasma/wallpapers/` enum and can be set via qdbus6 without error, but no actual wallpaper package exists for it. Plasmashell logs "Error loading the wallpaper, no valid package loaded." **Use `plasma6-wallpapers-smart-video-wallpaper-reborn` (AUR)** instead — plugin ID `luisbocanegra.smart.video.wallpaper.reborn`. Requires `mpv` as backend.

### KDE Plasmashell Restart Resets Wallpaper
After `kquitapp6 plasmashell && plasmashell --replace`, the wallpaper plugin and config reset to defaults. Re-apply the wallpaper via qdbus6 after every plasmashell restart.

### Waybar on KDE — No hyprland/* Modules
`hyprland/workspaces` and `hyprland/window` are Hyprland-only. When running KDE Plasma, these modules silently don't load. Remove them from config.jsonc and use KDE-native alternatives or custom modules. Dunst also can't run on KDE — KDE's plasmashell owns the `org.freedesktop.Notifications` DBus name.

### Config Generation Checklist Enforcement
When delegating config generation to subagents, the subagent MUST receive the actual waybar config.jsonc module list to cross-reference against CSS selectors. Without this, the CSS will contain selectors for modules that don't exist (e.g., `#custom-gpu`) and miss modules that do exist (e.g., `#custom-logo`, `#custom-power`, `#custom-separator`). Always read the live config first, pass it as context.

### Waybar CSS Strictness
- `@define-color` variables inside `@keyframes` cause parse errors — use raw `rgba()` values
- 8-digit hex (`#RRGGBBAA`) doesn't work in `@define-color` — use `rgba(r,g,b,a)`
- No live CSS reload — `pkill waybar; waybar &` every time

### Config Validation

```bash
rofi:     rofi -theme <file>.rasi -dump-theme 2>&1 | head -5
waybar:   pkill waybar; waybar &    # check stderr for parse errors
i3:       i3 -C -c ~/.config/i3/config
sway:     sway -C -c ~/.config/sway/config
hyprland: journalctl -f             # no dry-run; check journal after restart
dunst:    dunst -config <file> 2>&1 | head -10   # check for WARNING/CRITICAL
```

### Dunst v2 Deprecated Keys
`geometry` and `shrink` are dunst v1 keys — dunst v2+ logs WARNING and ignores them. Replace with:
```ini
# OLD (v1):  geometry = "380x5-20+44"
# NEW (v2):
width = 380
offset = 20x44
origin = top-right
# Also remove: shrink = no/yes
```

### Rofi Invalid Properties
`x-offset` and `y-offset` on the `window` block are not valid rofi properties in current versions. Remove them. Use `location` and `anchor` for positioning instead.

---

## 13. Subdirectory Documentation Index

Load the appropriate doc alongside this one based on the task:

### shared/ — Cross-Environment (load for any rice)

| File | Covers |
|------|--------|
| `shared/design-system.md` | 10-key palette schema, ANSI color derivation, materializer contract |
| `shared/palette-extraction.md` | Image → palette: 4 vision passes, Pillow algorithm |
| `shared/wallpaper-generation.md` | Animated pipeline (FAL+Seedance), static gen, fal.ai style transfer, UI chrome |
| `shared/rollback.md` | 4-layer backup architecture, session protocol, all 9 presets |
| `shared/gtk.md` | GTK 3/4 settings.ini + gtk.css overrides |
| `shared/terminal.md` | kitty, alacritty, wezterm (Lua), foot (INI no-# pitfall), display fonts |
| `shared/shell-prompt.md` | starship, powerlevel10k, fzf |
| `shared/waybar.md` | waybar config, CSS, @import injection |
| `shared/rofi.md` | rofi rasi themes, power menu script |
| `shared/dunst.md` | dunst INI config, DBus conflict handling |
| `shared/polybar.md` | polybar color fragment injection, module color refs |
| `shared/wofi.md` | wofi CSS selectors, GTK theme interaction |
| `shared/mako.md` | mako INI config, urgency sections, reload |
| `shared/swaync.md` | SwayNC CSS, JSON config, mako conflict |
| `shared/picom.md` | picom shadow/opacity/blur, @include injection, KDE conflict |
| `shared/templates.md` | All 13 Jinja2 template directories documented |
| `shared/catalog-capture.md` | Screenshot catalog builder for theme comparison |
| `shared/widgets.md` | EWW setup, AI→widget pipeline, image slicing, hover patterns |
| `shared/hermes-skin.md` | Hermes CLI skin generation, palette→skin mapping |
| `shared/braille-art.md` | Image → braille art pipeline, colorization, dimensions |
| `shared/fastfetch.md` | System info theming, custom braille logos, palette colors |

### KDE/ — KDE Plasma

| File | Covers |
|------|--------|
| `KDE/setup.md` | 5-layer stack overview, discover_apps(), snapshot, live reload |
| `KDE/colorscheme.md` | .colors format, decimal RGB, generation, activation |
| `KDE/kvantum.md` | Widget style, catppuccin themes, Qt SVG limits |
| `KDE/plasma-panel.md` | Plasma theme SVGs, required element IDs, textures |
| `KDE/cursor.md` | Cursor theme installation & activation |
| `KDE/splash-screen.md` | Splash screen customization |
| `KDE/konsole.md` | Konsole colorscheme format, profile activation |
| `KDE/wallpaper.md` | plasma-apply-wallpaperimage, palette integration |
| `KDE/widgets.md` | EWW on KDE, Plasmoid alternative |

### Hyprland/ — Hyprland (stubs reference shared/ for cross-env apps)

| File | Covers |
|------|--------|
| `Hyprland/setup.md` | Full from-scratch guide: packages, config, multi-monitor, debugging |
| `Hyprland/borders-animations.md` | Border gradients, gaps, rounding, animation curves, window rules |
| `Hyprland/hyprlock.md` | Lock screen config, mood-aware placeholders, hypridle |
| `Hyprland/wallpaper.md` | awww daemon, multi-monitor, HDMI DPMS fix |
| `Hyprland/fastfetch.md` | Hyprland-specific modules (→ `shared/fastfetch.md`) |
| `Hyprland/waybar.md` | Hyprland workspace modules, autostart (→ `shared/waybar.md`) |
| `Hyprland/rofi.md` | Hyprland keybindings (→ `shared/rofi.md`) |
| `Hyprland/dunst.md` | Autostart, plasmashell conflict (→ `shared/dunst.md`) |
| `Hyprland/widgets.md` | Layer rules, workspace integration, replacing waybar |

### Recommended loading combos

| Ricing task | Load these docs |
|-------------|----------------|
| Full KDE rice | `SKILL.md` + `KDE/setup.md` + `shared/rollback.md` + `shared/design-system.md` (+ `shared/hermes-skin.md` recommended) |
| Full Hyprland rice | `SKILL.md` + `Hyprland/setup.md` + `shared/rollback.md` + `shared/design-system.md` (+ `shared/hermes-skin.md` recommended) |
| Just change wallpaper | `shared/wallpaper-generation.md` + `shared/palette-extraction.md` |
| Theme one app | `shared/design-system.md` + the specific app doc |
| Add a new preset | `shared/rollback.md` + `shared/design-system.md` |
| Build screenshot catalog | `shared/catalog-capture.md` |
| Custom system info logo | `shared/braille-art.md` + `shared/fastfetch.md` |
| Design custom AI widgets | `shared/widgets.md` + environment-specific widgets doc |

For a full desktop ricing session, load this file + the environment-specific setup doc + `shared/rollback.md`.

---

## 14. Animated Wallpaper Pipeline

Full doc → `dev/DESIGN_PHILOSOPHY.md §Wallpaper System`. Summary:

### Detection (Step 1)
Check for installed animated wallpaper engines:

| Engine | Notes |
|--------|-------|
| `swww` / `awww` | Static + transitions (fade, wipe, grow). No video loop. |
| `mpvpaper` | Plays video/GIF as wallpaper. Best for looping video. |
| `xwinwrap` + `mpv` | X11 video wallpaper. |
| `komorebi` | Animated scenes, parallax, particles. |
| `waypaper` | Frontend — check backend. |
| KDE built-in | Native animated wallpaper support. |
| Wallpaper Engine | Via Steam + Wine — check Steam library. |

Also check: `FAL_KEY` set in Hermes? Required for generation.

### Fallback Chain
```
FAL set up + KDE Plasma   → install plasma6-wallpapers-smart-video-wallpaper-reborn (AUR)
                             Plugin ID: luisbocanegra.smart.video.wallpaper.reborn
                             Requires: mpv. org.kde.video does NOT work — no backing package.
FAL set up + Hyprland     → install mpvpaper (AUR) for video loops, awww for static+transitions
FAL not set up            → suggest setup, proceed with static
No FAL, no interest       → static only
```

### Generation Pipeline (FAL available)
1. Generate **4 static variants** of the same scene via `mcp_image_generate`:
   - Dawn (cool light, soft edges, mist)
   - Day (full clarity, saturated)
   - Dusk (warm golden tones, long shadows)
   - Night (deep darks, accent highlights)

2. Animate each via FAL image-to-video. **Recommended: Seedance 2.0** (`bytedance/seedance-2.0/image-to-video`).
   See `shared/wallpaper-generation.md` for model details, the fal_client.subscribe() workaround,
   and the multi-model racing pattern.

3. Store: `~/.config/wallpapers/<theme-name>/{dawn,day,dusk,night}.mp4`

4. **KDE Plasma:** Set via qdbus6 with `luisbocanegra.smart.video.wallpaper.reborn` plugin.
   **Hyprland:** `mpvpaper` plays the looping video, cron swaps with `awww img`.

Times are user-configurable — night owls may want "night" until noon.

---

## 15. Supported Targets

Coverage key: **✅ full doc** · **⚠ partial** (templates/brief mention) · **🔲 out of scope** (explicitly descoped)

### Desktop Environments / WMs

| WM/DE | Coverage | Notes |
|-------|----------|-------|
| **KDE Plasma** | ✅ full | `KDE/setup.md` + all KDE subdocs |
| **Hyprland** | ✅ full | `Hyprland/setup.md` + all Hyprland subdocs |
| **Sway / i3 / bspwm** | 🔲 out of scope | X11/Sway-specific config not documented. GTK theming (`shared/gtk.md`) works across all WMs; app theming docs are WM-agnostic. |
| **GNOME** | 🔲 out of scope | gsettings-based theming not documented. GTK theming (`shared/gtk.md`) applies. |

### Applications

| App | Coverage | Doc |
|-----|----------|-----|
| **kitty** | ✅ full | `shared/terminal.md` |
| **alacritty** | ✅ full | `shared/terminal.md` |
| **konsole** | ✅ full | `KDE/konsole.md` |
| **wezterm** | ✅ full | `shared/terminal.md` — Lua config, color_scheme override pitfall |
| **foot** | ✅ full | `shared/terminal.md` — no-# prefix pitfall, SIGUSR1 reload |
| **waybar** | ✅ full | `shared/waybar.md`, `Hyprland/waybar.md` |
| **polybar** | ✅ full | `shared/polybar.md` |
| **EWW** | ✅ full | `shared/widgets.md`, `KDE/widgets.md`, `Hyprland/widgets.md` |
| **rofi** | ✅ full | `shared/rofi.md`, `Hyprland/rofi.md` |
| **wofi** | ✅ full | `shared/wofi.md` |
| **dunst** | ✅ full | `shared/dunst.md`, `Hyprland/dunst.md` |
| **mako** | ✅ full | `shared/mako.md` |
| **swaync** | ✅ full | `shared/swaync.md` |
| **awww / swww** | ✅ full | `Hyprland/wallpaper.md`, `shared/wallpaper-generation.md` |
| **plasma-apply-wallpaperimage** | ✅ full | `KDE/wallpaper.md` |
| **picom** | ✅ full | `shared/picom.md` — note: X11 only, not used on Hyprland |
| **Hyprland compositor FX** | ✅ full | `Hyprland/borders-animations.md` |
| **hyprlock** | ✅ full | `Hyprland/hyprlock.md` |
| **GTK 3/4** | ✅ full | `shared/gtk.md` |
| **Qt / Kvantum** | ✅ full | `KDE/kvantum.md` |
| **starship** | ✅ full | `shared/shell-prompt.md` |
| **powerlevel10k / fzf** | ✅ full | `shared/shell-prompt.md` |
| **fastfetch / nitch** | ✅ full | `shared/fastfetch.md`, `Hyprland/fastfetch.md` |
| **Hermes CLI skin** | ✅ full | `shared/hermes-skin.md` |
| **feh / nitrogen** | ⚠ partial | Brief mention in wallpaper docs — X11-only wallpaper setters |
| **ironbar** | 🔲 out of scope | Rust bar, niche Wayland adoption — use waybar |
| **fuzzel** | 🔲 out of scope | Wayland launcher — use rofi-wayland |
| **i3lock-color** | 🔲 out of scope | X11 lock screen — use hyprlock on Wayland |
| **conky** | 🔲 out of scope | X11 desktop overlay — broken on Wayland |
| **cava** | 🔲 out of scope | Terminal audio visualizer — cosmetic extra, minimal theming surface |
| **tmux** | 🔲 out of scope | Dev tool, not a rice target for this skill |
| **Firefox userChrome.css** | 🔲 out of scope | Separate rabbit hole — needs its own skill |
| **AGS / Fabric** | 🔲 out of scope | EWW is primary widget system for this skill |

---

## 16. Skill Maintenance Notes

- Keep this skill generic. All paths, commands, and examples must be reproducible by any user on any machine. Do NOT embed usernames, machine names, or session-specific content.
- Incremental patching causes drift. After several small patches, do a full rewrite.
- Separate "what the user did" from "what anyone should do." Live-testing findings belong in the relevant subdirectory doc's Known Pitfalls section.
