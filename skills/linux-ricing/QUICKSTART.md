# Linux Ricing — Quickstart

> *The agent is the designer. You are the art/UX director.*

This is not a theme applier. It is a creative session — the agent audits your machine, explores directions with you, generates a plan with mockups, then implements it element by element. You describe what you want to feel; the agent figures out how to get there.

---

## How It Works

**Just say what you want:**

> *"Rice my desktop"*
> *"Make my machine feel like I actually live here"*
> *"I want something dark and unsettling"*
> *"Make it look like a game UI"*

The agent takes it from there. You'll be asked a few questions — not technical ones. Things like:

- *What do you want to feel when you sit down at your machine?*
- *What do you actually use this machine for?*
- *Anything sacred — hotkeys, layouts, apps that must not be touched?*

From your answers, the agent proposes a creative direction. You react to it. Then it builds.

---

## What a Session Looks Like

| Step | What Happens |
|------|-------------|
| **1 — Audit** | Agent reads your machine silently: WM, installed apps, GPU, current theme, game playtime, wallpaper |
| **2 — Explore** | Creative conversation. Wide exploration — vibes, references, wild ideas. Nothing is eliminated yet. |
| **3 — Refine** | You pick a direction. It gets a name, a mood, a reference anchor. |
| **4 — Plan** | Agent generates a static HTML mockup: palette, wallpaper preview, bar design, full change list. You approve or send it back. |
| **4.5 — Rollback** | Immutable snapshot of your current desktop. `ricer undo` restores it at any time. |
| **5 — Install** | Packages listed upfront, explained, installed only after your review. |
| **6 — Implement** | Element by element. Each change is applied, verified, and confirmed before the next. |
| **7 — Cleanup** | Config syntax check, services reloaded, final audit. |
| **8 — Handoff** | Markdown + HTML document: every changed hotkey, every design decision, how to roll back. |

Sessions are crash-safe — if you close the terminal mid-session, the agent can resume exactly where you left off.

---

## The Seven Stances

The agent uses an internal vocabulary of seven named design stances to orient itself. You don't need to use these terms — describe a feeling and the agent maps it. But if you want to speak the language:

| Stance | Feeling | Like |
|--------|---------|------|
| **Zen** | Curated, warm, meditative | macOS, wabi-sabi, morning coffee |
| **Signal** | Curated, cold, information-dense | Bloomberg terminal, dark cockpit |
| **Garden** | Liberated, warm, alive | Botanical, hand-drawn, earthy |
| **Ghost** | Curated, cold, invisible | Minimal, borderless, OS disappears |
| **Riot** | Liberated, cold, confrontational | Punk, acid neon, ransom-note |
| **Blade** | Liberated, cold, precise | Cyberpunk, geometric, adversarial |
| **Drift** | Liberated, warm, dreamy | Lo-fi, soft glitch, ambient |

Stances can blend: *"Ghost with Blade undertones"* is a valid direction.

---

## Animated Wallpaper

If you have an animated wallpaper engine (`swww`/`awww`, `mpvpaper`, KDE built-in), the agent can generate four looping video wallpapers — dawn, day, dusk, night — that auto-swap based on system time via a cron job. Requires a FAL API key for generation.

---

## First-Time Setup

```bash
bash ~/.hermes/skills/creative/linux-ricing/scripts/setup.sh
```

Installs Python deps (`pillow`, `jinja2`), symlinks the `ricer` CLI, verifies your environment.

**Requirements:** Python 3.10+, KDE Plasma or Hyprland (other WMs: partial support, see §15 in SKILL.md).

---

## Rollback — Always Available

At any point during or after a session:

```bash
ricer undo
```

Restores configs to the pre-session baseline. The rollback snapshot is created at Step 4.5, before any changes are made.

---

## Resume an Interrupted Session

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py resume-check
```

Lists any incomplete sessions. Tell the agent to pick up where you left off.

---

## Go Deeper

| Doc | What's In It |
|-----|-------------|
| [SKILL.md](SKILL.md) | Full workflow, architecture, all 16 sections |
| [dev/DESIGN_PHILOSOPHY.md](dev/DESIGN_PHILOSOPHY.md) | The design theory behind all decisions |
| [shared/design-system.md](shared/design-system.md) | The 10-key palette schema and color derivation rules |
| [shared/rollback.md](shared/rollback.md) | The 4-layer backup architecture |
| [KDE/setup.md](KDE/setup.md) | KDE Plasma full rice walkthrough |
| [Hyprland/setup.md](Hyprland/setup.md) | Hyprland full rice walkthrough |
