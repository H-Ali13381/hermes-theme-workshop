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

## 2. Session Workflow — Gateway

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
> fallback, kitty include, profile name, fastfetch suffix) → consolidated in §KDE
> Implementation Pitfalls below.

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

When the user wants a clean slate (delete all past sessions):

```bash
# 1. Remove all session directories and .current symlink
rm -rf ~/.config/rice-sessions/rice-*
rm -f ~/.config/rice-sessions/.current

# 2. Wipe the SQLite checkpoint store
rm -f ~/.local/share/linux-ricing/sessions.sqlite

# 3. Verify clean
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py resume-check
# Should return: []
```

Then launch a fresh session with PTY as usual (RICER_API_KEY, RICER_BASE_URL, RICER_MODEL env vars).

---

### Troubleshooting: LLM Auth Failures (401)

The workflow's `get_llm()` in `workflow/config.py` resolves the API key with this priority:
1. `RICER_API_KEY` / `RICER_BASE_URL` env vars (bypass all file-based config)
2. `config.yaml` → `providers.<provider>.api_key` (inline key)
3. `~/.hermes/.env` → `<PROVIDER>_API_KEY` (only if step 2 returned empty)

**Known pitfall:** If `config.yaml` has a *stale* non-empty API key, the workflow uses it and never falls back to `.env`. The stale key may have worked for Hermes at setup time but since been rotated or invalidated. Hermes itself may resolve keys differently (e.g. credential pool, system env), so the main chat works while the workflow fails with 401.

**Symptoms:** `openai.AuthenticationError: Error code: 401 - {'error': {'message': 'User not found.', 'code': 401}}` during Step 2+ (any LLM call).

**Diagnose:** Compare the two key sources:
```bash
python3 -c "
import sys; sys.path.insert(0, '<skill-dir>')
from workflow.config import _load_hermes_config, _parse_dotenv
from pathlib import Path
h = _load_hermes_config()
env = _parse_dotenv(Path.home() / '.hermes' / '.env')
print(f'config.yaml key length: {len(h[\"api_key\"])}')
print(f'.env key length: {len(env.get(\"OPENROUTER_API_KEY\", \"\"))}')
print(f'Keys match: {h[\"api_key\"] == env.get(\"OPENROUTER_API_KEY\", \"\")}')
"
```
If keys differ, the `.env` key is the working one.

**Fix:** Pass the working key via env var when launching or resuming:
```bash
RICER_API_KEY="$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2-)" \
  python3 workflow/run.py [--resume <thread-id>]
```
Or set `RICER_API_KEY` + `RICER_BASE_URL` permanently in your shell profile.

### Troubleshooting: Invalid Model ID (400)

**Symptoms:** `openai.BadRequestError: Error code: 400 - {'error': {'message': '<model-id> is not a valid model ID', 'code': 400}}` during Step 2 (explore) or any other LLM node.

**Root cause:** `workflow/config.py` resolves the LLM model via `get_llm()`. The old implementation had two defects:
1. The fallback `MODEL` constant was hardcoded to an Anthropic-native identifier (`claude-sonnet-4-5-20251029`) that does not exist on OpenRouter.
2. `get_llm()` only loaded the Hermes config when **both** `RICER_BASE_URL` and `RICER_API_KEY` env vars were missing. If the agent passed `RICER_API_KEY`/`RICER_BASE_URL` to fix auth, the model name from `~/.hermes/config.yaml` was never read, so the invalid fallback was used.

**Diagnose:** Check which model string the workflow is actually sending:
```bash
python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.hermes/skills/creative/linux-ricing'))
from workflow.config import get_llm
llm = get_llm()
print('Model:', llm.model_name if hasattr(llm, 'model_name') else llm.model)
"
```

**Fix:** Ensure `workflow/config.py` always loads Hermes config to fill in the model, even when env vars are present, and that the fallback `MODEL` constant is a valid identifier for the user's provider (e.g. `deepseek/deepseek-v4-pro` for OpenRouter, or `claude-3-5-sonnet-20241022` for Anthropic native).

As a quick workaround, pass the correct model explicitly:
```bash
RICER_MODEL="deepseek/deepseek-v4-pro" \
  RICER_API_KEY="$(grep '^OPENROUTER_API_KEY=' ~/.hermes/.env | cut -d= -f2-)" \
  RICER_BASE_URL="https://openrouter.ai/api/v1" \
  python3 workflow/run.py
```

### Known Platform Bug: Konsole Transparency Broken on KDE Plasma 6 Wayland

**As of 2026-05-01, confirmed on Plasma 6.6.4:**

The `Opacity` key in Konsole `.profile` files is **silently ignored** when Konsole runs as a native Wayland client. This is an upstream KDE regression in the blur-behind Wayland protocol. The following all fail:
- `Opacity=0.75` in `[Appearance]` of the profile file
- `konsoleprofile Opacity=0.75` runtime command
- `BackgroundContrast=true` / `BlurBackground=true`

**Compositor is running fine** — KWin compositing and blur effects are active. The bug is specific to Konsole's Wayland client implementation.

**Workaround:** Use **Kitty** for transparency. Kitty's `background_opacity` works correctly on Wayland. The mossgrown-throne kitty config already sets `background_opacity 0.88`. Recommend Kitty as the primary terminal when transparency is part of the design.

**XWayland workaround** (invasive, not recommended): Force Konsole onto XWayland by overriding `Command=env WAYLAND_DISPLAY= DISPLAY=:1 /bin/bash` in the profile. Breaks Wayland-native features (clipboard, scaling, HiDPI).

**Check for fix:** Run `plasmashell --version` and retest after a future Plasma update. Plasma 6.6.4 was confirmed broken in this environment.

---

### Known Color Application Issues (KDE recipe)

Issues observed during the mossgrown-throne session (2026-05-01) — watch for these:

**1. Kitty: old palette persists alongside theme.conf include**
The implement node appends `include theme.conf` to the existing `kitty.conf` but does NOT remove the inline palette block. Kitty's include overrides values at parse time, so colors are technically correct — but the old cursor color, tab colors, url_color, and section header remain from the previous theme. The file looks wrong and confuses future edits.
Fix: After a kitty implement, manually replace the entire inline palette section with the new colors. The `theme.conf` generated by the workflow is the authoritative source.

**2. Konsole: workflow writes wrong profile**
The workflow targets `hermes-ricer.profile` but `~/.config/konsolerc` may point to a different `DefaultProfile` (e.g. `linux-ricing.profile`). The themed profile is written but never loaded.
Fix: Always check `kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile` before and after theming Konsole. Update THAT profile, not a hardcoded one.

**3. window_decorations:kde: filename mismatch causes false 2/10 score**
The workflow spec targets `~/.local/share/color-schemes/MossgrownThrone.colors` (CamelCase, no prefix) but the apply node writes `hermes-mossgrown-throne.colors` (kebab-case with hermes- prefix). The verify node checks for the spec path, finds nothing, scores 2/10. The file was actually written correctly.
Fix: The convention is `hermes-<theme-name>.colors`. The spec, apply, and verify nodes must all agree on this filename. When you see a 2/10 on window_decorations with `files_missing`, check for the hermes- prefixed file before retrying.

---

### Undoing / Rolling Back a Rice Session

The workflow ships `scripts/ricer_undo.py` which knows how to restore every backed-up file, reapply previous color schemes, clean up injections, and close EWW windows. Prefer it over manual restoration.

**Via the workflow's own undo verb (cleanest):**
```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python3 scripts/ricer.py undo           # undo active manifest only
python3 scripts/ricer.py undo-session   # undo every manifest newest→oldest
python3 scripts/ricer.py simulate-undo  # dry-run preview, no writes
```

**Via baseline JSON (fallback — when the manifest is absent or corrupted):**
The `baseline_node` writes a snapshot to `~/.config/rice-sessions/<thread-id>/baseline_<timestamp>.json` before `install_node` runs. The `"backups"` key maps config names → absolute backup paths under `~/.cache/linux-ricing/baselines/<timestamp>_files/`.

Restore map (backup filename → live destination):

| Backup key | Destination |
|---|---|
| kdeglobals, kcminputrc, konsolerc, ksplashrc, plasmarc | ~/.config/<name> |
| kvantum.kvconfig | ~/.config/Kvantum/kvantum.kvconfig |
| gtkrc-2.0 | ~/.gtkrc-2.0 |
| gtk-3.0-settings | ~/.config/gtk-3.0/settings.ini |
| gtk-4.0-settings | ~/.config/gtk-4.0/settings.ini |
| kitty.conf | ~/.config/kitty/kitty.conf |
| fastfetch.config.json | ~/.config/fastfetch/config.json |
| dunstrc, rofi.config.rasi, waybar.style.css, starship.toml | ~/.config/<app>/... |
| bashrc, zshrc | ~/.<name> |
| konsole_profiles/ | ~/.local/share/konsole/ (full dir copy) |
| color-schemes/ | ~/.local/share/color-schemes/ (full dir copy) |
| kscreenlockerrc | NOT backed up — check/reset manually after restore |

After restoring files, apply KDE state:
```bash
plasma-apply-colorscheme <baseline.kde.colorscheme.active_scheme>
plasma-apply-wallpaperimage "<baseline.kde.wallpaper.image_path stripped of file://>"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "<baseline.kde.cursor.active_cursor>"
```

**Post-restore cleanup checklist:**
1. `kitty.conf` restored but `theme.conf` is NOT backed up separately. If `theme.conf` still has rice colors and no backup exists, **delete it** — kitty falls back to the inline palette in `kitty.conf`.
2. `fastfetch/config.json` may be a symlink → `config.jsonc` written by the rice. Remove the symlink, copy the real backup file in.
3. `rofi/hermes-theme.rasi` is NOT in the baseline backup (it predates the session). Restore it manually to the previous theme's colors, or point `config.rasi` at a different existing theme file.
4. If baseline `color-schemes/` did not include a file the baseline's `konsole_profiles/` references, restore it separately from an older session or recreate it.
5. Confirm no `*mossgrown*` (or current theme name) artifacts remain: `find ~/.config ~/.local/share -name "*<theme>*"`.
6. **`kscreenlockerrc` is NOT backed up** — the rice modifies it (lock screen wallpaper + theme). Check and reset manually if needed (`Theme=org.kde.breezedark.desktop`).
7. **Restart plasmashell after restore** — even when all config files are correct, plasmashell caches the color scheme in memory. UI elements (folder icons, window chrome) will still show rice colors until restarted: `kquitapp6 plasmashell; sleep 1; killall plasmashell 2>/dev/null; plasmashell &`

Full step-by-step baseline restore with copy-paste code → `references/baseline-restore-procedure.md`

### Undoing a Rice (Restoring Baseline)

`undo_session()` in `scripts/ricer_undo.py` handles all config file restoration and
automatically restarts plasmashell at the end on KDE. The restart flushes the
in-memory color scheme and icon tinting that KDE holds even after config files on disk
are fully restored — this was the root cause of folder icons staying green after an undo.

Tell the user to close and reopen any running Dolphin/app windows after the undo
completes — apps inherit icon tinting from the plasmashell session at launch time.

---

### Bypassing a Stuck Refine Node (design JSON loop)

**Symptom:** The bridge returns `next: ['refine']` with `[Refine][WARN] Sentinel found but design JSON could not be parsed — asking for retry.` This may happen on the FIRST attempt (right after explore confirms direction) or after repeated retries. Either way the fix is the same — do NOT try to feed bridge answers. Go directly to state injection (below). Feeding "confirm" or the full JSON as a bridge answer does not help because the parse failure is inside the node, not at an interrupt gate the bridge can resolve.

**Root cause:** The refine node uses the LLM's raw output to extract design JSON. If the LLM's response doesn't pass `_validate_design()`, the node interrupts for user feedback — but the user's reply just gets appended to messages and the LLM tries again. Feeding answers via the bridge cannot fix a validator failure; only a correctly-structured design can. This can happen on the very first refine attempt (right after explore locks direction) — there is no need to wait for multiple retries before bypassing.

**KDE validator requirements (exact fields checked by `workflow/validators.py`):**
- `BASE_REQUIRED_KEYS`: `name`, `description`, `palette`, `mood_tags`
- `RECIPE_REQUIRED_KEYS` for kde: `kvantum_theme`, `plasma_theme`, `cursor_theme`, `icon_theme`, `gtk_theme`, `originality_strategy`, `chrome_strategy`
- `palette` must contain all 10 slots: `background`, `foreground`, `primary`, `secondary`, `accent`, `surface`, `muted`, `danger`, `success`, `warning` — all valid 7-char hex
- `originality_strategy` must have: `vision_alignment` (non-empty) + `non_default_moves` (list of ≥3 items with no banned words: "default", "stock", "breeze", "standard", "unchanged", "normal", "generic")
- `chrome_strategy` must have: `method` (non-empty string) AND `implementation_targets` (non-empty list)
- `widget_layout` items (if present) must each have: `name`, `position`, `data`, `visual` — note these are `data` and `visual`, NOT `data_source` and `visual_metaphor` (the LLM commonly uses the wrong key names)

**Fix:** Write a valid design.json manually, verify it passes the validator, then inject it directly into the graph checkpoint:

```python
# 1. Verify design passes validator
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/neos/.hermes/skills/creative/linux-ricing')
from workflow.validators import design_complete
design = json.loads(Path('/home/neos/.config/rice-sessions/<thread-id>/design.json').read_text())
ok, reason = design_complete(design, {'desktop_recipe': 'kde'})
print(f'ok={ok}, reason={reason!r}')

# 2. Inject state and advance to plan node
from langgraph.checkpoint.sqlite import SqliteSaver
from workflow.config import DB_PATH
from workflow.graph import build_graph

thread_id = '<thread-id>'
config = {'configurable': {'thread_id': thread_id}}
with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
    graph = build_graph(checkpointer)
    graph.update_state(config, {'design': design, 'current_step': 3}, as_node='refine')
    state = graph.get_state(config)
    print('next:', list(state.next))  # should be ['plan']
```

Run this from the skill venv (`source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate`) with the RICER_* env vars set. After the state update, call the bridge with no answer to trigger the plan node.

**Must-run from terminal tool (not execute_code):** LangGraph imports require the skill venv — use `python3 -c "..."` in the terminal tool, not the sandbox.

---

### Troubleshooting: Stale "Preview Contract Violation" Flag on Fresh Sessions

**Symptom:** After plan node generates plan.html, `pending_messages[0].message` includes:
```
PREVIEW CONTRACT VIOLATION — do not approve this preview.
Reason: previous preview was rejected for misleading unimplemented window chrome
Type 'regenerate' so the workflow produces an honest preview.
```

**Root cause:** This flag is carried over from a *previous session's* rejection state, not from the current session's plan.html. The SQLite checkpointer or the plan node's state includes a rejection flag from a prior thread. On a fresh session this is always stale.

**What to do:** Open the plan.html and evaluate it directly (`brave <path>`). If the mockup is honest and matches the design, feed `"approve"` — ignore the stale violation message. If the mockup genuinely shows unimplemented chrome (macOS traffic-light buttons, rounded windows that won't be delivered, etc.), feed `"regenerate"`.

---

### Troubleshooting: Stale Session Checkpoints

Crashed or hung workflow runs (e.g. from the PTY pitfall above) leave behind:
- Session directories at `~/.config/rice-sessions/<thread-id>/`
- A stale `.current` symlink pointing to the last session dir
- SQLite checkpoint entries at `~/.local/share/linux-ricing/sessions.sqlite`

`session_manager.py resume-check` queries both filesystem dirs and the SQLite checkpoint store, so orphaned entries survive directory cleanup. To fully remove a stale session:

```bash
# Remove session directory and .current symlink
rm -rf ~/.config/rice-sessions/<thread-id>
# If .current points to the stale session, remove it too
[ -L ~/.config/rice-sessions/.current ] && rm ~/.config/rice-sessions/.current
```

SQLite checkpoints are automatically pruned when a new session is run with a fresh invocation — the stale entries from killed processes won't interfere. If `resume-check` still lists deleted sessions, they exist only in the SQLite checkpointer's WAL and are harmless; a fresh workflow run will rotate them out.

### Pitfalls: KDE Implementation Quirks

**Fastfetch config.json vs config.jsonc:** The workflow may write `config.jsonc` but
fastfetch looks for `config.json`. Fix: `ln -sf ~/.config/fastfetch/config.jsonc
~/.config/fastfetch/config.json`.

**grim fails on KDE Wayland:** `grim` may fail with *"compositor doesn't support the
screen capture protocol"*. Use `spectacle --background --fullscreen -o <path>` as
fallback for screenshots.

> Other KDE pitfalls (kwin_wayland --replace, Kitty include behavior, Konsole profile
> selection, Konsole transparency bug) are covered in §Known Color Application Issues
> and §Post-Implementation: Manual Elements.

**Reference docs** → `README.md` (directory layout, presets, CLI reference, supported targets, safety model, pitfalls, doc index)
**KDE validator contract** → `references/kde-design-validator-contract.md` (exact required fields, banned words, widget key names, quick validation snippet, state-injection bypass)
**LLM error patterns** → `references/workflow-llm-errors.md` (400 invalid model, 401 auth, diagnosis snippets)
**Chat-agent bridge** → `references/workflow-bridge-script.md` (non-TTY resume helper for agent orchestration)
**Wallpaper sourcing** → `references/wallpaper-sourcing.md` (Alpha Coders + vision analysis workflow for game-themed wallpapers)

### Post-Implementation Verification (Agent Responsibility)

The workflow's scorecard validates structure and palette presence, but can miss cases where old config values remain (e.g. kitty appending `include theme.conf` while old colors stay inline). After the workflow finishes Step 6 (implement), the agent MUST verify each written config actually reflects the design palette:

```bash
# Quick palette audit — grep actual color values in each config
echo "=== kitty ===" && grep -E "^(foreground|background|color[0-9]|cursor )" ~/.config/kitty/kitty.conf 2>/dev/null
echo "=== starship ===" && head -6 ~/.config/starship.toml 2>/dev/null
echo "=== rofi ===" && cat ~/.config/rofi/hermes-theme.rasi 2>/dev/null | head -10
echo "=== fastfetch ===" && python3 -c "import json; d=json.load(open('$HOME/.config/fastfetch/config.jsonc')); print(d.get('color',{}))" 2>/dev/null
```

If any config still has colors from a previous theme (e.g. Shiva Temple's `#0a0b1a` or `#5b4fcf`), replace them inline. Don't rely on `include` files overriding old values — some terminals parse includes differently.

### Post-Implementation: Manual Elements

#### KWin Replace — CRITICAL
**NEVER run `kwin_wayland --replace` standalone.** It kills plasmashell on Wayland,
leaving the user with a bare desktop (no panel, no widgets, no taskbar).

If KWin restart is needed (e.g. to apply cursor theme), always follow immediately with:
```bash
kwin_wayland --replace &
sleep 3
plasmashell &
```
Or skip the kwin restart entirely — cursor theme changes apply on next login anyway.

#### Konsole Theming — Read the Right Profile File
Konsole uses the profile named in `~/.config/konsolerc` under `[Desktop Entry] DefaultProfile=`.
**Always check konsolerc first** before editing any profile:
```bash
grep DefaultProfile ~/.config/konsolerc
```
Then edit that `.profile` file, not a guess.

The `Opacity` key belongs in `[Appearance]` of the `.profile` file — NOT in the `.colorscheme` file.
The `.colorscheme` file's `Opacity` key is ignored by Konsole.

Correct profile structure:
```ini
[Appearance]
ColorScheme=hermes-mossgrown-throne
Font=JetBrainsMono Nerd Font,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1
Opacity=0.75
BlurBackground=false
BackgroundContrast=false

[General]
Name=linux-ricing
Parent=FALLBACK/
```

#### Konsole Transparency Broken on Plasma 6 Wayland
See §Known Platform Bug above for the full diagnosis. Quick check that Konsole is native
Wayland (not XWayland): `xlsclients | grep -i konsole || echo "Native Wayland — broken"`.
Workaround: use Kitty (`background_opacity` works correctly on Wayland).
Reference: `references/konsole-wayland-transparency.md`.

#### AUR Package Install via Agent Terminal
`yay -S` builds the package but fails the final `sudo pacman -U` step (no TTY for password).
The built package is left in `~/.cache/yay/<pkg>/`. Install it directly:
```bash
sudo pacman -U ~/.cache/yay/<pkg>/<pkg>.pkg.tar.zst
```
This works from the agent terminal without PTY issues.

### Workflow Gaps: Elements Requiring Attention

The audit node builds an initial `element_queue` from detected apps. Step 3 may then
add design-driven elements such as `widgets:eww` when the user vision calls for EWW
widgets, terminal frames, custom borders, or overlay chrome. Do not add generic widgets
just to satisfy a checklist; use them when they make the concept less boring and more true.

| Element | In queue? | Notes |
|---------|-----------|-------|
| wallpaper | No | Must be sourced separately (see wallpaper-sourcing.md). Applied during implement, not shown in plan.html. |
| widgets / EWW chrome (KDE Plasma) | Design-driven | `widgets:eww` is added after `design.json` only when `widget_layout` or `chrome_strategy` calls for custom overlays, frames, borders, or widgets. |
| notifications (dunst/mako/swaync) | No | May not be installed. Install + configure manually if needed. |
| panel/bar (KDE panel) | Design-driven | Use `panel_layout` when the concept changes panel composition. Prefer original overlay/dock/rail chrome over the normal KDE toolbar when it fits the user brief. |
| cursor theme | No | design.json defaults to "default". Override manually. Catppuccin cursor themes are pre-installed and palette-matched (see below). Bibata requires AUR install + sudo. |
| Hermes skin | No | Only relevant if user has custom Hermes CLI. |

When the user asks about widgets, panels, rounded windows, or custom borders, treat them
as visual promises. Collect preferences during explore/plan, preview them in `plan.html`,
and ensure `chrome_strategy` maps the promise to an implementable target such as EWW
frames, Kitty decoration settings, Kvantum, or KDE color/window decoration settings.

### Post-Workflow: KDE-Specific Implementation Notes

**Cursor theme:** Bibata-Modern-Classic requires AUR install (`yay -S bibata-cursor-theme-bin`)
plus `sudo pacman -U` to install the built package. If sudo is unavailable, Catppuccin cursor
themes are pre-installed and palette-matched. Use the variant that best matches the theme's
primary/accent color:
```bash
# Set cursor via kwriteconfig (no sudo needed)
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme --type string "catppuccin-macchiato-green-cursors"
# Cursor change takes effect on next login (KDE requirement)
```

**Notifications:** KDE Plasma has its own notification system (plasmashell). No external daemon
(dunst/mako/swaync) is needed. The color scheme automatically applies to notifications.

**Originality/chrome composition:** KDE Plasma color inheritance is not enough. The
workflow requires `originality_strategy` and `chrome_strategy`; optional `panel_layout`
and `widget_layout` are used only when they serve the user vision. If the preview shows
rounded windows, custom terminal frames, ornamental borders, or non-stock panel chrome,
the final output must implement them through EWW frames, terminal config, Kvantum, or KDE
decoration/color settings. Do not call a palette-only panel “done.”

**Wallpaper:** Use `plasma-apply-wallpaperimage <path>` to set wallpaper on all desktops.
This is NOT in the element_queue and must be done manually after the workflow finishes.

**Color scheme naming:** The workflow's implement node may write the color scheme file under
a different name than what `plasma-apply-colorscheme` searches for. Check
`~/.local/share/color-schemes/` for the actual filename and verify with:
```bash
plasma-apply-colorscheme <scheme-name> 2>&1
# "already set" = working. "does not exist" = name mismatch.
```
