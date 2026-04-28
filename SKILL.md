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

## 2. Session Workflow — Gateway

> **The workflow is the authority.** This skill is the launch gateway. `workflow/` enforces all quality gates, score thresholds, session checkpointing, and deterministic step sequencing. The model's job here is to start or resume the workflow — not to re-implement the protocol manually.

### Pre-flight — Start or Resume

Check for any incomplete sessions (agent-guided or LangGraph):

```bash
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py resume-check
```

Returns a unified JSON list. Each entry has a `"source"` field: `"agent"` (legacy) or `"workflow"`.

If incomplete sessions exist:
> *"I found an incomplete rice session from [started] — '[theme]', step N. Resume it or start fresh?"*

**Resume a workflow session** (`"source": "workflow"`):
```bash
python3 ~/.hermes/skills/creative/linux-ricing/workflow/run.py --resume <thread-id>
```
The workflow restores from its last SQLite checkpoint and continues automatically.

**Legacy agent sessions** (`"source": "agent"`) pre-date the workflow. Offer to start fresh.

**Start a new session:**
```bash
python3 ~/.hermes/skills/creative/linux-ricing/workflow/run.py
```

That's it. The workflow drives Steps 1–8, pausing at approval and score gates for user input. This SKILL.md serves as reference for the workflow's behaviour, quality standards, and environment pitfalls — not as a step-by-step manual.

---

### Non-Negotiable Gates (enforced by the workflow)

- **Privacy:** the `audit` node reads only non-sensitive system facts silently. Personal history, memory files, and screenshots require explicit user consent before the workflow accesses them. Secrets are never logged — only `set` / `not set`.
- **Visual preview:** `plan_node` must produce a real HTML mockup (`plan.html`) before any config is written. A text plan is not a preview.
- **Baseline:** `baseline_node` runs `desktop_state_audit.py` before `install_node` starts. No implementation begins without an immutable rollback snapshot.
- **Element gate:** every element in `implement_node` must score ≥ 8/10 across the 5-category scorecard (Palette, Shape, Diegesis, Usability, Preview integration — each 0–2). Below threshold, the workflow interrupts and the user must explicitly accept the deviation or retry. Silent skips are not possible.
- **Quality Bar:** every applicable theming checklist item (terminal, bar, launcher, notifications, window decorations, GTK, wallpaper, lock screen, fastfetch, cursor, shell prompt, widgets, Hermes skin) ends the session in one logged terminal state — `✓ verified`, `✓ accepted-deviation`, or `SKIP <reason>` — before `handoff_node` runs.

---

### Workflow Stage Map

The 8-step pipeline in `workflow/graph.py`:

| Step | Node | What it does |
|------|------|--------------|
| 1 | `audit` | Silent machine scan: WM, GPU, screens, apps, FAL key. Classifies desktop recipe (kde / hyprland / gnome / other). Builds element queue. Routes to END immediately for unsupported desktops. |
| 2 | `explore` | Multi-turn creative dialogue (LLM, temperature 0.7). Converges on stance, mood, reference anchor. Loops until `<<DIRECTION_CONFIRMED>>` sentinel detected. |
| 3 | `refine` | Produces and validates `design.json` — 10-key palette + recipe-specific fields. Loops until schema passes `validator.design_complete()`. Writes `design.json` to session dir. |
| 4 | `plan` | Generates self-contained `plan.html` mockup (palette board, terminal, bar, launcher). Interrupts for user approval; loops on `regenerate` or change requests. |
| 4.5 | `baseline` | Runs `desktop_state_audit.py`. Immutable pre-implementation snapshot. Warns but does not abort on failure. |
| 5 | `install` | Resolves required packages from design + profile. Shows list, interrupts for confirmation. Handles sudo via env var → cached creds → masked prompt escalation. |
| 6 | `implement` | Processes one element per invocation: spec → apply → verify → score → gate. Interrupts below threshold. Loops via `_after_implement` until element queue is empty. |
| 7 | `cleanup` | Validates written config files, reloads only the services that were changed (waybar, dunst/mako/swaync, hyprland). |
| 8 | `handoff` | LLM-generated `handoff.md` + `handoff.html`. Marks session complete in `session.md`. |

Stage routing and conditional edges → `workflow/graph.py`
Node implementations → `workflow/nodes/`
State schema → `workflow/state.py`
Validation gates → `workflow/validators.py`
Full session state spec → `dev/DESIGN_PHILOSOPHY.md §Session State & Persistence`

**Reference docs** → `README.md` (directory layout, presets, CLI reference, supported targets, safety model, pitfalls, doc index)
