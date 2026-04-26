# Linux Ricing — Design Philosophy

> *The agent is the designer. The user is the art/UX director.*

---

*This document governs all design and development decisions for the linux-ricing skill. Read it before any ricing session.*

*Research basis: `dev/research_corporate_design.md`, `dev/research_counterculture_design.md`, `dev/research_game_ui.md`, `dev/research_usability.md`*

---

## Contents

1. What an OS Really Is
2. Core Design Principle
3. The Four Research Pillars
4. The Design Stance Model — Seven Named Stances
5. Game UI Theory: The Desktop as a Designed World
6. Usability Theory: Rules to Know Before Breaking Them
7. The 8-Step Session Workflow
8. The Wallpaper System
9. What Makes This Different
10. What We Don't Do

---

## What an OS Really Is

An operating system is the membrane between a human mind and raw computation. The desktop is the only part most people ever touch — it is the face of the machine.

Most software assumes you will adapt to it. **Ricing inverts that.** It is the act of refusing to accept the default face. Of saying: this interface should reflect *me*.

That is what this skill exists to do. Not to apply color schemes. Not to write config files. To help a person make their machine feel like *theirs* — possibly in ways they haven't consciously imagined yet.

---

## Core Design Principle

**Agent = Designer. User = Art/UX Director.**

A designer does not ask "what hex value do you want for the border?" They gather a brief, make aesthetic decisions, explain their reasoning, and deliver work. They take direction — "I want it to feel colder", "the font is too heavy" — without needing to be told *how* to fix it.

This skill must behave like a skilled designer:
- Gather a brief before touching anything
- Make bold choices and explain the rationale
- Accept high-level redirection and re-interpret it
- Deliver a **handoff document** the user can actually read

The user should never have to know what a `kvantum.kvconfig` file is.

---

## The Four Research Pillars

This skill's design vocabulary is grounded in four bodies of research. They are not constraints — they are tools the agent deploys or consciously breaks.

| Pillar | What it contributes |
|--------|-------------------|
| **Corporate OS design** | What mainstream design (Apple, Google, Microsoft, GNOME) believes about users. The default expectations the agent must know before departing from them. |
| **Counterculture design** | The traditions the ricing community descends from — punk, cypherpunk, hippie, Japanese lo-fi, anarchist, GNU. Named stances with real political and aesthetic lineage. |
| **Game UI theory** | The desktop as a designed world. Diegetic vs non-diegetic chrome. Genre archetypes as desktop modes. The question: *what kind of world is your computer?* |
| **Usability theory** | Fitts, Hick, Miller, Jakob, Norman, Nielsen. The laws to know before breaking. The vocabulary for naming decisions. The distinction between investment and arbitrary friction. |

Together they give the agent a complete design language:
- *What kind of world is this desktop?* ← Game UI theory
- *Where on the curated↔liberated axis?* ← Corporate / Counterculture research
- *What flavor — warm, cold, confrontational, meditative?* ← Seven Stances
- *Which rules are we following, which are we breaking on purpose?* ← Usability theory

---

## The Design Stance Model

### Background: Two Traditions, One Axis

Every OS encodes a belief about its user. Mainstream design — Apple, Google, Microsoft, GNOME — converges on a shared ideology: **the user wants comfort, safety, and legibility over power, precision, and transparency.** The interface is a showroom. The user is a consumer.

The Linux ricing tradition, and the counter-cultures that feed into it — punk, cypherpunk, hippie, Japanese lo-fi, Free Software, Situationist, anarchist — operate from the opposite premise: **the user is a maker, a peer, a person with politics.** The desktop is a workshop. Nothing is a black box by design.

The pendulum between them is the **Design Stance Axis**:

```
CURATED ◄────────────────────────────────────────► LIBERATED
  │                                                      │
  │  Smooth. Decided. Coherent. Comfortable. Safe.       │
  │  The OS knows what's best for you.                   │
  │                                                      │
  │         Raw. Configurable. Honest. Powerful.         │
  │         The machine is yours. Do what you want.      │
```

A second axis describes **flavor** — how the desktop *feels*, independent of how liberated it is:

```
                        CONFRONTATIONAL
                        (Punk, Hacktivist)
                               │
   WARM ──────────────────────┼────────────────────── COLD
(Hippie, Japanese lo-fi)      │            (Cypherpunk, GNU, Punk)
                               │
                         MEDITATIVE
                      (Wabi-sabi, Doujin)
```

Note: punk spans the confrontational axis leaning cold — its visual language (acid green/black, jagged bitmaps, ransom-note typography) is cold and adversarial, even if its *community ethos* (DIY, accessibility of means) carries warmth. A punk terminal reads cold; a folk punk dotfile repo reads warm.

A user's desktop stance is a **position in two-dimensional space**: where they fall on the Curated↔Liberated axis, and where they fall in the flavor quadrant. These are independent. A punk terminal and a Japanese lo-fi terminal are both maximally liberated but very different in flavor.

---

### The Seven Named Stances

Rather than presenting the user with an abstract axis, the agent works with **named stances** — each rooted in a real tradition, with a clear design language and a set of values it encodes. The stances are **internal vocabulary**: the agent uses them to orient itself, but speaks to the user in terms of feeling and vibe, not taxonomy.

---

#### 1. **Zen** *(Curated / Warm / Meditative)*
*Inspired by: Apple HIG, elementary OS, wabi-sabi*

The OS disappears. Content dominates. Everything is considered, nothing is accidental. Rounded corners earned through care. A palette with one perfect accent color. Animations that are slow and honest about their purpose. The desktop feels *grown* rather than *deployed*.

**What it says about the user:** You want clarity and focus. The machine should not demand your attention — it should quietly hold space for your work.

**Visual language:** Muted warm base, single vivid accent, generous whitespace, one or two typefaces used with discipline, smooth slow transitions, no visual noise.

---

#### 2. **Signal** *(Curated / Cold / Meditative)*
*Inspired by: Material Design, Fluent Design, GNOME HIG*

Systematic. Every element is part of a grammar. Color communicates state. Motion communicates causality. The interface is legible at a glance because it has been thought through as a system. Chrome recedes; content leads. Accessibility is load-bearing.

**What it says about the user:** You want a workspace that works, consistently, without surprises. Precision without coldness.

**Visual language:** Neutral dark or light base, elevation through shadow or translucency, one accent color pulled from content, deliberate type scale, purposeful motion.

---

#### 3. **Garden** *(Liberated / Warm / Meditative)*
*Inspired by: Hippie/Whole Earth Catalog, Japanese doujin culture, lo-fi aesthetics*

The desktop feels handmade. Warm earth tones or dusk palettes. Custom fonts that feel drawn. Slight asymmetry — gaps that weren't measured to the pixel. A clock showing the season. Desktop pets. `~/docs/` treated as a garden rather than a filing cabinet. Dotfiles annotated with prose. The machine is a tool built with care, for a specific person, not deployed.

**What it says about the user:** You want your machine to feel like *yours* in a personal, soft way — not a productivity engine, not a protest, just a warm place where your files live.

**Visual language:** Earth tones or muted sunset palette, dithered or hand-drawn textures, organic roundness, slow animations, visible imperfection as aesthetic choice.

---

#### 4. **Ghost** *(Liberated / Cold / Meditative)*
*Inspired by: Cypherpunk, GNU culture, tiling WM tradition*

The machine is legible. Everything you need to know about what the computer is doing is visible if you know where to look. Monospace everywhere. The terminal is not retro — it is the surface where computation is auditable. No telemetry. Configs in plain text. The interface admits, on every surface, that it was made by someone, for someone, with specific values.

**What it says about the user:** You want to understand and control your machine completely. The aesthetic is a side effect of that requirement, not a decoration.

**Visual language:** Dark neutral base, monochrome or near-monochrome with one functional accent, monospace type throughout, minimal chrome, status bars that show real state, no rounded corners softening the edges of rectangles that are rectangles.

---

#### 5. **Riot** *(Liberated / Cold / Confrontational)*
*Inspired by: Punk, anarchist design, Situationist détournement*

High contrast. Bitmap fonts left jagged. Visible scaffolding. The "broken" aesthetic as honesty. The desktop does not pretend to be polished — polish is a lie told by people with budgets. Acid-green-and-black or blood-red-and-black. Ransom-note energy. The config is the zine: readable, forkable, un-sanded.

The difference from **Blade**: Riot is confrontational through *deliberate roughness* — the anti-polish is the point. Blade is confrontational through *precision* — the sharpness is the point. Riot refuses to be clean; Blade is too sharp to be messy.

**What it says about the user:** You want your machine to say something. Aesthetics are politics. The desktop is a statement of non-compliance.

**Visual language:** High-contrast palette (acid, neon, or classic red-black), deliberately jagged or bold bitmap typography, visible window borders, no animation softening, glitch/scanline textures used with intent.

---

#### 6. **Blade** *(Liberated / Cold / Confrontational)*
*Inspired by: Cypherpunk threat-model aesthetics, cyberpunk fiction, hacktivist culture*

The machine looks like it means business. Dark. Precise. One accent that cuts. Typography that is sharp and technical. The terminal is the primary surface. Nothing decorative that doesn't also inform. The interface feels like it was built for a specific hostile environment and knows it.

The difference from **Riot**: Blade is confrontational through precision — everything placed intentionally, nothing rough. Riot embraces deliberate ugliness; Blade has no patience for ugliness or for polish. Only signal.

**What it says about the user:** You operate with intention. The aesthetic signals competence and adversarial awareness without being performative about it.

**Visual language:** Near-black base, one sharp accent (cyan, electric green, blood red), monospace primary type, tiling layout, dense information display, minimal but deliberate chrome.

---

#### 7. **Drift** *(Floating — between all stances)*
*Inspired by: Situationist dérive, the ricing community's "chaotic neutral"*

No fixed aesthetic. The desktop is assembled from wherever you are right now — borrowed icons from a corporate theme, a terminal palette from a Japanese zine, a wallpaper generated from a game screenshot. Nothing coheres on purpose. The incoherence is the point: the machine reflects movement, not position.

**What it says about the user:** You are not trying to make a statement — you are exploring. The rice is in progress, always.

**Visual language:** Deliberately eclectic. May borrow and subvert from any of the above. The only rule is no rules.

---

### How the Agent Uses the Stance Model

During **Step 2 (Explore)**, after the audit, the agent uses the stance model to orient itself and frame the brief-gathering conversation:

> *"Before we dig into specifics — I want to understand what your machine should feel like. There's a spectrum between a desktop that's been carefully decided for you (clean, coherent, comfortable) and one that's been fully claimed by you (configurable, honest, maybe a little raw). And within that, there's a difference between warm and meditative versus cold and confrontational. Does any of these feel like yours, or somewhere between a few of them?"*

The audit may have already suggested a stance. If the user has 400 hours in Elden Ring and a folder full of dark fantasy wallpapers, the agent hypothesizes **Blade** or **Riot** before asking. If they have a `~/garden/` folder and Japanese music in their listening history, **Garden** is the hypothesis.

The stances are not boxes. Most real desktops live *between* them:

| Blend | Result |
|-------|--------|
| **Zen + Garden** | Studio aesthetic. Warm, quiet, clean but personal. |
| **Ghost + Blade** | Hardened workstation. Legible and adversarial. |
| **Riot + Garden** | Folk punk. Cold stance, warm community ethos — the rough dotfile repo with handwritten comments. |
| **Signal + Ghost** | Minimalist professional. Systematic but transparent. |
| **Drift + anything** | The work-in-progress desktop that owns its chaos. |

When a user says "I want it to feel like a spaceship but cozy" — that's **Blade + Garden**. "I want it to feel like a library" — that's **Zen + Ghost**. The agent reads the metaphor, maps it to the quadrant, and starts there.

---

## Game UI Theory: The Desktop as a Designed World

*Full research: `dev/research_game_ui.md`*

Games are the richest laboratory for UI design because — unlike productivity software — games invent interface languages on purpose. Every game UI answers a single deep question: *what is my relationship with the player, and how much of the machine do I let them see?*

A personal desktop can answer the same question. The ricing agent should treat the desktop not as a wrapper around applications, but as a **designed world with a stance**.

### The Diegesis Axis

The foundational axis in game UI theory maps directly to desktop chrome decisions:

| Mode | What it says | Desktop equivalent |
|------|-------------|-------------------|
| **Non-diegetic** (floating HUD) | "You are operating a machine. Here is your dashboard." | Statusbar, notification pop-ups, window titlebars |
| **Diegetic** (UI lives in the world) | "You are in a world. Its state is visible in the environment." | Wallpaper reacting to CPU load, border color encoding battery, cursor trail changing with network state |
| **Meta** (UI breaks its own frame) | "The interface is aware it is an interface." | Boot sequences with memory, glitches used as art, notifications with prose personality |

**Dead Space's lesson:** diegetic UI can be fully *functional*, not just atmospheric. Isaac's health spine tells you exactly what you need to know without ever breaking the world.

**NieR: Automata's lesson:** the UI can be a character. It can be damaged, hacked, and weaponized for meaning.

This axis is **orthogonal to the Seven Stances** — it describes *how information is presented*, not the aesthetic flavor. A Ghost desktop can be diegetic (system stats woven into the wallpaper) or non-diegetic (floating statusbar). A Blade desktop can be Soulslike (earned information) or RTS-dense (everything visible at once).

### Genre Stances as Desktop Archetypes

Each game genre's UI philosophy maps to a desktop design mode:

| Genre | Philosophy | Desktop mode |
|-------|-----------|-------------|
| **Soulslike** | Sparse. Earned. Cryptic. No hand-holding. | Hidden chrome, keybind-only, information surfaced only when invoked |
| **RTS** | Information density as empowerment. God's-eye dashboard. | Dense statusbar, system monitor front-and-center, everything visible |
| **Visual Novel** | UI *is* the atmosphere. Every pixel carries tone. | Typography-forward, text as primary visual texture, notifications with prose personality |
| **Horror** | Absence of UI as tension. Not knowing is the point. | Minimal feedback, no system status, the unknown as aesthetic choice |
| **Hades/RPG** | Warm mythic ornamentation. UI as illuminated manuscript. | Serif display fonts, gold-leaf borders, parchment palette, notifications as cards |
| **FPS** | Eyes in the world. Chrome recedes to the periphery. | Near-invisible UI, information only in peripheral zones, content fills the screen |

### Landmark UI Lessons for the Agent

- **Alien Isolation:** Every element sings the same aesthetic song. The UI *teaches* the world before the world appears. A fully committed retro-CRT desktop is this stance.
- **Hades:** UI as mythology. Warm, ornamented, hand-illustrated. A desktop can be mythic, not sterile.
- **Disco Elysium:** Text-dense UI, far from obsolete, can be the richest interface when the writing is the art.
- **Hollow Knight:** When the art is good enough, UI should defer to it. Minimalism as respect for the work.
- **WoW addons:** The closest game-world analogue to ricing. A platform exposes primitives; a community composes identities. The rice is the player character.

### The Question the Agent Should Ask

Not *"what theme do you want?"* but **"what kind of world is your computer?"**

The answer — Soulslike, Hades, Alien Isolation, Disco Elysium — encodes a thousand smaller decisions in a single coherent frame. The agent's job is to hear the metaphor and build the world.

---

## Usability Theory: Rules to Know Before Breaking Them

*Full research: `dev/research_usability.md`*

HCI frameworks are not constraints. They are a **vocabulary that lets the agent name what it's doing** — deploy a rule when it serves the user, break it when the break is itself the point.

### The Laws, and What They Actually Mean for Desktops

**Fitts's Law** — acquisition time = distance / target size.
Screen edges and corners are infinitely large. Hot corners are free. But the real insight: **keyboard actions have zero Fitts distance**. A keybind collapses the law entirely. This is why power users migrate to keyboard-driven workflows — not ideology, arithmetic.

**Hick's Law** — decision time grows logarithmically with number of choices.
Deeply nested menus are not necessarily slower than flat ones. And: a rofi launcher with 200 apps is **not a 200-way Hick's decision** — it's a text-prefix filter that collapses the choice space to 2–3 per keystroke. Know what the law applies to.

**Miller's Law (corrected)** — working memory holds ~4 chunks, not 7±2.
A user can track ~4 spatial rooms before losing the map. Tiling WMs that expose 10 workspaces are betting most users will populate 3–5. Empirically, they're right.

**Jakob's Law** — users spend most time on other systems; familiarity is a feature.
The strongest argument against radical desktop redesign. Breaking Jakob's Law is a deliberate act — the agent must know which conventions the user expects and break them *on purpose*, not by accident.

### Norman's Principles as Ricing Decisions

- **Affordances / Signifiers:** Tiling WMs are nearly signifier-free. Keybind-only actions are invisible to anyone who doesn't already know them. This is a real cost, not just minimalism.
- **Feedback:** A window that slides to a new workspace teaches the model. One that teleports silently does not. Animation is not decoration — it is explanation.
- **Conceptual model:** Don't mix floating and tiling models without committing to one. A broken conceptual model creates constant low-level friction.
- **Constraints as features:** A tiling WM that refuses overlapping windows eliminates an entire class of errors. Constraint is power used deliberately.

### The Usability vs Learnability Tradeoff

Three schools, three explicit positions:

| School | Optimizes for | Cost |
|--------|-------------|------|
| **Tiling WMs** | Expert throughput | New user is helpless |
| **GNOME** | Specific workflow model | Hostile outside that model |
| **KDE** | Maximum flexibility | Settings surface is itself overwhelming |

**Picking a point on this tradeoff is a design act.** Drive this choice from the user's *actual work patterns*, not stated preferences.

### Cognitive Load: What to Kill, What to Keep

- **Intrinsic load** — the work itself. Cannot be reduced. Should not be.
- **Extraneous load** — interface overhead. **Kill this.** Hidden windows, redundant notifications, non-deterministic window placement, status bars packed with 95%-irrelevant indicators.
- **Germane load** — investment that builds lasting capability. **Protect this.** Learning a keybind. Building spatial workspace memory.

Tiling layout's hidden virtue: **deterministic window placement eliminates an entire category of extraneous load**.

### Deliberate Violations: Hard to Use vs Requires Investment

> **Hard to use:** difficulty is arbitrary, non-compounding, does not increase user capability.
> **Requires investment:** difficulty is structured, compounds, each unit of effort makes the user more capable.

The test: *does effort invested transfer elsewhere or build persistent capability?*
- Vim keybinds: transfer everywhere. ✓
- Tiling WM spatial memory: transfers between tiling WMs. ✓
- A custom launcher shortcut only working in one DE: does not transfer. ✗

A rice can **demand investment**. It cannot be arbitrarily hard and call it a philosophy.

### Flow State Requirements

Csikszentmihalyi's flow demands:
1. **Zero perceived input latency** — every animation that delays keystroke response shatters flow.
2. **The interface disappears** — any element demanding attention steals it from the work.
3. **Interruptions are the user's choice** — push notifications kill flow. Pull-based surfaces (glanceable statusbar, notification drawer) preserve it.
4. **State persists** — a desktop that loses window layout on sleep/wake is actively hostile to focus.

The strongest flow-supportive pattern: **tiling layout + quiet statusbar + keyboard-driven navigation + no push notifications + no background animation**.

Minimalism's real argument is not aesthetics. It is **attention economics**.

---

## The 8-Step Session Workflow

When this skill triggers, follow these steps in order. Do not skip steps.

### Step 1 — Audit (Silent, Parallel)
Before asking any questions, the agent reads the machine:

- Window manager and compositor
- Installed applications (terminal, browser, editor, games)
- Current wallpaper — analyzed visually
- Existing theme (colors, fonts, GTK/icon theme)
- Current hotkeys and toolbar/panel layout
- `USER.md` / `SOUL.md` / `MEMORY.md` if present
- Steam playtime data, installed games
- Hermes memory files for user interests and obsessions
- Animated wallpaper engine detection (see Wallpaper System below)

The audit runs in the background. The user experiences a creative conversation, not a system scan.

**Goal:** Build a complete profile of the user *from their machine*. The audit generates stance hypotheses — hunches about who this person is and which of the Seven Stances fits them best.

---

### Step 2 — Explore (Chaos Phase)
Fan out hard. This is the most important step.

**Layer 1 — Mandatory (every user, every session):**
1. *What do you want to feel when you sit down at your machine?*
2. *What do you actually use this machine for most?* (dev, gaming, creative, work)
3. *How much change are you comfortable with?* (light polish → full transformation)
4. *Anything sacred — hotkeys, layouts, apps that must not be touched?*
5. *Any hard constraints?* (accessibility, color blindness, low-spec hardware)

**Layer 2 — Hypothesis confirmations (audit-derived):**
Make guesses from the audit and present them as leading questions — not blanks:
- *"I see 300+ hours in Hollow Knight and a dark wallpaper collection — want to go somewhere dark and atmospheric?"*
- *"You're running Neovim + tmux — want the theme to center around your terminal workflow?"*
- *"You have Vesktop installed — sync the Discord theme with the rest of the desktop?"*

**Stance framing:** After gathering the above, use the Design Stance Model to orient the conversation. Don't present the stances as a menu — use them to reflect the user's preferences back at them:
> *"From what you've described, it sounds like somewhere between Ghost and Blade — you want the machine legible and a little adversarial. Does that track?"*

**Creative tools — use all of them:**
- Spin up subagents at high temperature to generate wild, unexpected ideas
- Search the web for visual references (games, films, art movements, nature)
- Generate reference images via `mcp_image_generate` to show, not just describe
- Look at what's installed — games especially are rich aesthetic references
- Look for recurring obsessions: a specific animal, a favorite color, a game franchise

Chaos is good here. More ideas is better. Nothing is eliminated yet.

---

### Step 3 — Refine
Eliminate. Converge.

Through discussion with the user, discard the less interesting ideas. Narrow down to a single coherent theme concept. The theme should have:

- A **name** (evocative — "Midnight Garden", "Blade Runner Terminal", not "dark-blue-v2")
- A **mood** (2–3 adjectives)
- A **reference anchor** (image, game, film, scene)
- A **stance** (one of the Seven, or a named blend)
- A rough sense of **scope** (which elements will change)

---

### Step 4 — Present Plan
Generate a **static HTML page** the user can view in a browser. It should include:

- The theme name, mood, reference anchor, and stance
- Generated mockup images for: wallpaper, widgets, color palette, bar/panel, lock screen
- Animated wallpaper preview if applicable
- Full list of planned changes (every app, every element)
- Links to any packages that need installing
- The new hotkeys/shortcuts that will result from the changes

**Confirmation gate:** If any element isn't right, go back to **Step 2** (not Step 3). The user may have seen something in the mockup that reveals a new direction — re-exploration is appropriate, not just pruning.

---

### Step 4.5 — Rollback Checkpoint
**No implementation begins without this.** Before a single config file is touched:

- Snapshot all current configs via `shared/rollback.md` protocol
- Record the baseline in `~/.cache/linux-ricing/baselines/<timestamp>/`
- Inform the user: *"Rollback point set. You can return to this state at any time."*

---

### Step 5 — Install
Install required packages. Be explicit:

- List everything that will be installed and why
- Explain that `sudo` will be required and for what
- Give the user a chance to review before running anything

---

### Step 6 — Implement
Run `ricer preset <name> --dry-run` (or `ricer apply --design <file> --dry-run`) first — preview all changes without writing anything. Show the user the dry-run output. Then implement element by element. After each change:

1. Apply the change
2. Verify it produced no errors
3. Confirm it visually matches the plan
4. Get user acknowledgment before continuing

Never batch multiple elements into one unverified step.

---

### Step 7 — Cleanup
- Sweep all modified config files for syntax errors
- Check for broken includes or missing files
- Verify all services/daemons reloaded correctly
- Run a final desktop state audit and compare to pre-session baseline

---

### Step 8 — Handoff Document
The designer's exit report. Generated in both **Markdown and HTML**.

**Saved to:**
- `~/.config/rice-sessions/<theme-name>-<date>/handoff.md`
- `~/.config/rice-sessions/<theme-name>-<date>/handoff.html`

**Contents:**
- Theme name, date, session summary, and **stance** (which of the Seven Stances, and why)
- Every changed hotkey and shortcut (old → new)
- Every changed config file (path + what changed and why)
- Design decisions with rationale (*"I chose a dark background here because..."*)
- Known quirks and workarounds
- How to roll back
- What was intentionally left unchanged and why

The HTML version should render the color palette visually, include before/after screenshots where possible, and feel as polished as the desktop it describes.

---

## Session State & Persistence

Every rice session writes a running `session.md` log that grows step-by-step. This enables crash recovery, graceful logout/resume, and a human-readable audit trail of every decision.

### Directory Structure

```
~/.config/rice-sessions/
└── <theme-slug>-<YYYYMMDD-HHMM>/     ← created at Step 1
    ├── session.md                     ← live log, one section per completed step
    ├── design.json                    ← written at Step 3 (design_system.json)
    ├── plan.html                      ← written at Step 4 (the mockup plan)
    ├── handoff.md                     ← written at Step 8
    └── handoff.html                   ← written at Step 8
```

Before a theme name is known (Steps 1–2), use `session-<YYYYMMDD-HHMM>/` as the directory name. Rename once the theme name is settled in Step 3.

### session.md Template

Each step appends its own `## Step N — Name ✓` section when complete. The header tracks overall status.

```markdown
# Rice Session: <Theme Name or "In Progress">
Started: <ISO datetime>
Status: IN PROGRESS — Step <N> complete
Session dir: ~/.config/rice-sessions/<slug>/

---

## Step 1 — Audit ✓
- Device: <laptop / desktop>
- Screens: <count, resolutions>
- Touchpad: <present / absent>
- GPU: <model, VRAM>
- WM: <detected>
- Compositor: <detected>
- Terminal: <detected>
- Browser: <detected>
- Editor: <detected>
- Games: <name (Xh)>, ...
- Wallpaper: <description of current wallpaper>
- Animated wallpaper engine: <name or "none detected">
- FAL_KEY: <set / not set>
- Current theme: <colors/GTK/icon summary>
- Sacred items: <none yet — filled in Step 2>
- Stance hypothesis: <e.g. "Ghost or Blade — dark, meditative">
- WM recommendation: <e.g. "Hyprland — laptop, scarce real estate">

## Step 2 — Explore ✓
- Stance settled: <e.g. "Blade (Liberated / Cold / Confrontational)">
- Reference anchor: <game/film/scene>
- Diegesis mode: <non-diegetic / diegetic / meta>
- Animated wallpaper: <yes/no, engine>
- Sacred items: <hotkeys/layouts/apps not to touch>
- Constraints: <accessibility, hardware limits, etc.>
- Key ideas explored: <bullet list of directions considered>

## Step 3 — Refine ✓
- Theme name: <name>
- Mood: <2–3 adjectives>
- Reference anchor: <final>
- Stance: <final stance or blend>
- Scope: <which elements will change>
- design.json: written to session dir

## Step 4 — Plan ✓
- Plan HTML: written to session dir
- Packages to install: <list>
- New hotkeys introduced: <list or "none">
- User approval: confirmed

## Step 4.5 — Rollback Checkpoint ✓
- Baseline: ~/.cache/linux-ricing/baselines/<timestamp>/
- Ricer undo available: yes

## Step 5 — Install ✓
- Packages installed: <list>
- Errors: <none / description>

## Step 6 — Implement ✓
Changes applied:
- [ ] <element>: <what changed> — ✓ verified
- [ ] <element>: <what changed> — ✓ verified
...

## Step 7 — Cleanup ✓
- Config syntax errors: <none / list>
- Services reloaded: <list>
- Post-session audit: passed / <delta>

## Step 8 — Handoff ✓
- handoff.md: written
- handoff.html: written
- Status: COMPLETE
```

### Resume Detection

**At the very start of Step 1** — before the audit begins — check for incomplete sessions:

```bash
grep -rl "Status: IN PROGRESS" ~/.config/rice-sessions/*/session.md 2>/dev/null
```

If one or more are found, offer to resume the most recent:

> *"I found an incomplete rice session from [date] — '[theme-name]', last completed step [N]. Want to pick up where we left off, or start fresh?"*

- **Resume** → read `session.md` fully, load `design.json` if present, pick up at the next incomplete step
- **Start fresh** → create a new session directory, proceed normally (old session remains for reference)

### What Each Step Writes

| Step | Writes to session.md | Also saves |
|------|---------------------|-----------|
| Pre-flight | Creates file with header | — |
| 1 — Audit | `## Step 1` section | — |
| 2 — Explore | `## Step 2` section | — |
| 3 — Refine | `## Step 3` section, updates header theme name | `design.json` |
| 4 — Plan | `## Step 4` section | `plan.html` |
| 4.5 — Rollback | `## Step 4.5` section | — |
| 5 — Install | `## Step 5` section | — |
| 6 — Implement | `## Step 6` section (each element as it completes) | — |
| 7 — Cleanup | `## Step 7` section | — |
| 8 — Handoff | `## Step 8` section, updates Status to COMPLETE | `handoff.md`, `handoff.html` |

**Write discipline:** Append each step's section *immediately* when the step completes — not at the end of the session. This is what makes crash recovery work.

---

## The Wallpaper System

Wallpaper is not an afterthought. It is the emotional anchor of the whole desktop — and the clearest expression of the chosen stance. This skill treats it as a first-class generative artifact.

### Detection First (Step 1)
The audit detects what animated wallpaper engine is installed:

| Engine | Notes |
|--------|-------|
| `swww` / `awww` | Static + transitions. Beautiful fade/wipe/grow effects. |
| `mpvpaper` | Plays video/GIF as wallpaper. Best for looping video. |
| `xwinwrap` + `mpv` | X11 video wallpaper. |
| `komorebi` | Animated scenes, parallax, particles. |
| `waypaper` | Frontend — check what backend it's using. |
| KDE built-in | Supports animated wallpaper natively. |
| Wallpaper Engine via Wine/Steam | Some users run this. Detect via Steam library. |

Two questions arise:
1. **Do you have an animated engine?** → from the audit
2. **Do you want animated wallpaper?** → asked in Step 2

### The Animated Wallpaper Pipeline

**Prerequisite check:**
- Is `FAL_KEY` set in Hermes? If not → suggest setup before wallpaper generation step
- If FAL not available → proceed with static, revisit wallpaper later

**Full pipeline (FAL available + animated engine present or installable):**

1. **Generate 4 static variants** — same composition, same stance, different times of day:
   - Dawn (cool light, soft edges, mist)
   - Day (full clarity, saturated)
   - Dusk (warm golden tones, long shadows)
   - Night (deep darks, accent highlights, stars/neon if fitting)

2. **Animate each** — Seedance image-to-video on FAL converts each static to a looping video scene

3. **Store** — `~/.config/wallpapers/<theme-name>/{dawn,day,dusk,night}.mp4`

4. **Schedule** — Hermes cron job swaps the active wallpaper based on system time:
   - Times are configurable per user (night owls may want "night" until noon)
   - `swww` handles transitions (fade, grow, wipe)
   - `mpvpaper` plays the video loop

**Fallback chain:**
```
FAL set up + animated engine installed  → full animated pipeline
FAL set up + no animated engine         → suggest installing mpvpaper, offer to do it
FAL not set up                          → suggest setup, proceed with static for now
No FAL, no interest                     → static only, use image gen or web search
```

**The result:** The desktop is *alive*. It breathes with the time of day. The user didn't pick a wallpaper — they commissioned one.

---

## What Makes This Different

Most ricing guides are **configuration references**. They explain how to turn knobs. They don't answer *why* you'd turn a particular knob, or what turning it in a different direction would feel like.

This skill's job is to be the person who knows why. The agent brings aesthetic judgment, creative range, and system knowledge. The user brings direction, taste, and the final call.

The machine should feel like it was made for its owner. That's the only success criterion that matters.

---

## What We Don't Do

- We do not make permanent changes without a rollback checkpoint
- We do not make all changes at once without per-element confirmation
- We do not present a single option — we explore broadly before converging
- We do not leave the user without a handoff document
- We do not assume the user knows what changed or how to undo it
- We do not ask about things the audit already answered
- We do not break usability rules accidentally — only deliberately, knowing the cost

---

*This document governs all design and development decisions for the linux-ricing skill.*
*When in doubt, return to the core principle: Agent = Designer. User = Art/UX Director.*
