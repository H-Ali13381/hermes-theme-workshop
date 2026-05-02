---
name: linux-ricing
description: AI-native Linux desktop design system. The agent acts as designer — auditing the user's machine, exploring creative directions, generating mockups, and implementing a fully personalized desktop end-to-end. The user is the art/UX director.
trigger: User wants to theme/rice their Linux desktop, mentions changing colors/wallpaper/bar/launcher appearance, asks what their desktop could look like, or invokes /rice.
version: 3.0.0
tags: [linux, ricing, rice, theming, desktop, hyprland, kde, waybar, rofi, kitty, animated-wallpaper, generative]
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

## 2. Failure Protocol — Read Before Anything Else

When something goes wrong, **report and stop**. Do not improvise repairs. The workflow is designed to self-heal where it can; the rest is the user's call.

- **On any non-zero exit or unexpected output:** show the literal error to the user, then stop. Do not run remediation commands.
- **Never** run `pip install`, `rm -rf`, or recreate `.venv`. Environment management is out of scope for this skill.
- **Never** call `graph.update_state(...)` directly, write `design.json` by hand, or modify files in `~/.config/rice-sessions/`. Only the workflow and the bridge script may write to session state.
- **Quote workflow output verbatim.** Do not paraphrase interrupt messages, validator reasons, or session metadata. If you don't have the exact text, re-read it before reporting.
- **When uncertain, ask the user.** A short clarifying question beats an invented fix every time.

If the workflow appears stuck or incoherent, the correct action is to surface the state to the user — not to mutate it.

---

## 3. Session Workflow — Gateway

> **The workflow is the authority.** This skill is the launch gateway. `workflow/` enforces all quality gates, score thresholds, session checkpointing, and deterministic step sequencing. The model's job here is to start or resume the workflow — not to re-implement the protocol manually.

### Activate the virtual environment

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
```

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

> **CRITICAL — PTY required:** The workflow's `_run_loop` calls Python's `input()` at every user gate (Steps 2, 4, 5, 6, 8). This blocks silently with zero output when run via `background=true` or without `pty=true`. The agent MUST launch these commands with the terminal tool's `pty=true` parameter and **never** with `background=true`. A hung process at Step 0 with an empty log is the diagnostic signature. If the agent accidentally backgrounded the workflow, kill it and relaunch with `pty=true`.

That's it. The workflow drives Steps 1–8, pausing at approval and score gates for user input. This SKILL.md serves as reference for the workflow's behaviour, quality standards, and environment pitfalls — not as a step-by-step manual.

### Driving the Workflow Programmatically (bridge script)

The terminal tool's PTY mode cannot feed interactive stdin to the workflow — `input()` gets `EOFError` and the process exits immediately. To drive the workflow through the agent chat (collecting user answers in conversation and feeding them to the workflow), use the **bridge script pattern** documented in `references/workflow-bridge-script.md`.

Quick summary: write a small Python script that loads the graph from the SQLite checkpointer and calls `graph.stream(Command(resume=answer), config)` to resume from interrupts. Run it with the skill's venv activated and the usual `RICER_API_KEY`/`RICER_BASE_URL`/`RICER_MODEL` env vars.

**Bridge script location:** Write to `/tmp/rice_bridge.py` at session start (disposable). Template is in `references/workflow-bridge-script.md`.

**Important:** The bridge reference example uses placeholder model names — always check your actual model in `~/.hermes/config.yaml` under `providers.<provider>.model`. Pass the correct model via `RICER_MODEL`.

**RICER_MODEL for this user:** `anthropic/claude-sonnet-4-6` (OpenRouter). Always use this unless the user specifies otherwise.

**Sudo workaround:** When the bridge hits a `sudo_password` interrupt, feed `"skip"` to skip the package, then install it manually with `sudo pacman -S <pkg>` from the agent terminal (which CAN run sudo). Then resume the workflow via the bridge.

### Presenting Previews to the User

When the plan node generates `plan.html`, open it with `brave <path>` — do NOT use `open`, `xdg-open`, or start an http.server. The user has Brave as their default browser.

### Post-Workflow Manual Implementation

After the workflow completes Step 6, Step 7 cleanup/finalization handles KDE
post-implementation actions deterministically. Do not improvise manual commands
outside the workflow unless cleanup reports a skipped/unsupported action.

The workflow now owns:

1. Wallpaper application when a local `wallpaper_path`/`wallpaper` is present
2. KDE color-scheme reapply and active-state audit
3. Cursor/icon/Kvantum/Plasma/LnF theming through materializers
4. KDE custom EWW chrome (`widgets:eww`) when the design calls for widgets, terminal frames, borders, or overlays
5. Fastfetch `config.jsonc` plus `config.json` compatibility symlink
6. Plasmashell/KWin liveness checks
7. Handoff reporting of cleanup actions and effective state

Do **not** broadcast terminal signals such as `pkill -SIGUSR1 kitty`; terminal
configs apply on next launch unless a user explicitly asks for a targeted reload.
Do **not** run raw `kwin_wayland --replace`.

When the user asks to undo/revert/rollback the rice, check `scripts/ricer_undo.py`
FIRST. If the session's manifest is intact, `python3 scripts/ricer.py undo-session`
handles everything. Fall back to the baseline JSON procedure only when the manifest
is missing or corrupt. See §Undoing / Rolling Back a Rice Session below.

### Pitfall: sudo in Agent Terminal

The agent terminal CAN run sudo commands (unlike the bridge script which cannot handle
`sudo_password` interrupts). Try `sudo pacman -U <path>` or `sudo pacman -S <package>`
directly — it may work depending on session credential state. The handoff document's
claim that "user must run workflow directly for sudo step" applies only to the bridge
script pattern.

> **KDE implementation pitfalls** (kwin_wayland --replace, Konsole transparency, cursor
> fallback, kitty include, profile name, fastfetch suffix) → see
> `references/kde-known-issues.md` and `references/kde-post-implementation.md`.

---

### Non-Negotiable Gates (enforced by the workflow)

- **Privacy:** the `audit` node reads only non-sensitive system facts silently. Personal history, memory files, and screenshots require explicit user consent before the workflow accesses them. Secrets are never logged — only `set` / `not set`.
- **Visual preview:** `plan_node` must produce a real HTML mockup (`plan.html`) before any config is written. A text plan is not a preview.
- **Preview honesty:** `plan.html` must not show app/window chrome the workflow will not implement. macOS traffic-light titlebar controls are rejected unless a matching window-decoration implementation exists; rounded windows, terminal frames, and custom borders are allowed only when `chrome_strategy` names an implementable method.
- **Baseline:** `baseline_node` runs `desktop_state_audit.py` before `install_node` starts. No implementation begins without an immutable rollback snapshot.
- **Element gate:** every element in `implement_node` must score ≥ 8/10 across the 5-category scorecard (Palette, Shape, Diegesis, Usability, Preview integration — each 0–2). Below threshold, the workflow interrupts and the user must explicitly accept the deviation or retry. Silent skips are not possible.
- **KDE originality gate:** KDE `design.json` is invalid unless it includes `originality_strategy` and `chrome_strategy`: at least three user-specific non-default moves, and an implementable plan for any previewed rounded corners, custom borders, titlebars, terminal frames, widgets, or panel chrome. Widgets are optional; originality is mandatory.
- **Quality Bar:** every applicable theming checklist item (terminal, bar, launcher, notifications, window decorations, GTK, wallpaper, lock screen, fastfetch, cursor, shell prompt, widgets, Hermes skin) ends the session in one logged terminal state — `✓ verified`, `✓ accepted-deviation`, or `SKIP <reason>` — before `handoff_node` runs.

---

### Workflow Stage Map

The 8-step pipeline in `workflow/graph.py`:

| Step | Node | What it does |
|------|------|--------------|
| 1 | `audit` | Silent machine scan: WM, GPU, screens, apps, FAL key. Classifies desktop recipe (kde / hyprland / gnome / other). Builds element queue. Routes to END immediately for unsupported desktops. |
| 2 | `explore` | Multi-turn creative dialogue (LLM, temperature 0.7). Converges on stance, mood, reference anchor. Loops until `<<DIRECTION_CONFIRMED>>` sentinel detected. |
| 3 | `refine` | Produces and validates `design.json` — 10-key palette + recipe-specific fields. KDE requires `originality_strategy` and `chrome_strategy`; widgets/panels are design-driven, not mandatory. Loops until schema passes `validator.design_complete()`. Writes `design.json` to session dir. |
| 4 | `plan` | Generates self-contained `plan.html` full desktop mockup (palette, terminal, custom chrome/composition, launcher, optional widgets). Interrupts for user approval; loops on `regenerate` or change requests. |
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

### Deleting All Sessions and Starting Fresh

When the user wants a clean slate, use the `wipe-sessions` verb. It removes
every rice session dir, the `.current` symlink, and the LangGraph SQLite
checkpoint DB (incl. `-wal`/`-shm` siblings) in one call, and prints a JSON
summary of what it touched. Default behavior is dry-run; pass `--yes` to act.

```bash
# 1. Preview what would be removed (no writes)
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py wipe-sessions

# 2. Show the preview to the user, get explicit approval, then:
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py wipe-sessions --yes

# 3. Verify clean
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py resume-check
# Should return: []
```

Then launch a fresh session with PTY as usual (RICER_API_KEY, RICER_BASE_URL, RICER_MODEL env vars).

---

### Troubleshooting: LLM Errors (400 / 401)

`openai.BadRequestError: 400 — '<model-id> is not a valid model ID'` and
`openai.AuthenticationError: 401 — 'User not found.'` are both caused by
`workflow/config.py` resolution gaps (stale `config.yaml` key vs `.env`,
hardcoded fallback model, env vars short-circuiting Hermes config). Full
diagnosis snippets, root cause, and the env-var workaround live in
**`references/workflow-llm-errors.md`**.

### Known Platform Bug: Konsole Transparency on KDE Plasma 6 Wayland

The `Opacity` key in Konsole `.profile` files is silently ignored on native
Wayland (Plasma 6.6.4 confirmed broken). Use Kitty when transparency is part
of the design. Full diagnosis and workarounds in
**`references/konsole-wayland-transparency.md`**.

---

### Known Color Application Issues

Recurring quirks (kitty include + stale inline palette, Konsole themed-profile
swap, window_decorations filename mismatch causing false 2/10 scores) are
documented in **`references/kde-known-issues.md`**.

---

### Undoing / Rolling Back a Rice Session

Prefer the workflow's own undo verb — `scripts/ricer_undo.py` restores every
backed-up file, reapplies previous color schemes, cleans up injections, closes
EWW windows, and restarts plasmashell on KDE to flush in-memory color/icon state:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python3 scripts/ricer.py undo           # undo active manifest only
python3 scripts/ricer.py undo-session   # undo every manifest newest→oldest
python3 scripts/ricer.py simulate-undo  # dry-run preview, no writes
```

After undo completes, tell the user to close and reopen any running Dolphin /
app windows — apps inherit icon tinting from the plasmashell session at launch
time.

**Manual baseline-JSON restore (fallback when the manifest is absent or
corrupted):** the full restore-map table, KDE live-state commands, and
post-restore cleanup checklist live in **`references/baseline-restore-procedure.md`**.

---

### Refine Node — Self-Healing

The refine node retries internally when the LLM fails to emit a parseable
design JSON (see `MAX_REFINE_RETRIES` in `workflow/nodes/refine.py`). If every
retry fails, the node interrupts with the LLM's last output for the user to
read. **Do not inject a hand-crafted `design.json` or call `graph.update_state`
to "rescue" the node** — that violates the Failure Protocol (§2). Surface the
interrupt message verbatim and let the user decide.

Validator field requirements and common LLM mistakes are documented in
**`references/kde-design-validator-contract.md`** for diagnostic reading only.

---

### Troubleshooting: Stale Session Artifacts

Stale "Preview Contract Violation" flags on fresh sessions, and orphaned
session directories / SQLite checkpoint entries from crashed runs, are both
documented in **`references/kde-known-issues.md`**.

### Post-Implementation Verification & Manual Elements

After Step 6 the agent should run a palette audit, verify Konsole/Kitty/cursor
theming took effect, and apply elements the queue does not own (wallpaper,
cursor, manual widgets). The full procedure, palette-audit snippets, AUR
install workaround, KDE-specific implementation notes, and the workflow-gaps
table live in **`references/kde-post-implementation.md`**.

---

## 4. Reference Index

| Topic | File |
|---|---|
| Directory layout, presets, CLI, safety model | `README.md` |
| Full design philosophy + session state spec | `dev/DESIGN_PHILOSOPHY.md` |
| KDE design.json validator field reference | `references/kde-design-validator-contract.md` |
| KDE known issues (color application, stale flags, fastfetch/grim quirks, kwin replace) | `references/kde-known-issues.md` |
| KDE post-implementation verification, manual elements, workflow gaps | `references/kde-post-implementation.md` |
| Manual baseline-restore procedure (undo fallback) | `references/baseline-restore-procedure.md` |
| LLM error patterns (400 invalid model, 401 auth) | `references/workflow-llm-errors.md` |
| Konsole transparency on Wayland (broken upstream) | `references/konsole-wayland-transparency.md` |
| Chat-agent bridge (non-TTY resume helper) | `references/workflow-bridge-script.md` |
| Wallpaper sourcing (Alpha Coders + vision analysis) | `references/wallpaper-sourcing.md` |