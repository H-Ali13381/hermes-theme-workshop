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

## 2. Requirements

> **This skill requires two things the base workflow does not:**

### FAL (AI image generation)

Step 2.5 uses [fal.ai](https://fal.ai) to generate a full-desktop AI theme concept image
before the design phase — not a landscape painting or generic mood board. The image
should show the whole desktop treatment: wallpaper, window chrome, terminal, launcher,
panel/widgets, borders, menu surfaces, and icon language. Without a concrete image to
anchor the LLM's understanding of the theme, the design defaults to generic — the image
is the secret sauce that makes the palette and chrome decisions feel cohesive.

**Cost control:** FAL/image generation costs money. For this user, generate at most one
hero concept by default, reuse existing previews/artifacts, and ask before any extra
paid generation unless the user explicitly says `regenerate`, `new image`, or `start
fresh and generate again`. Small caveats belong in plan feedback or implementation, not
in another Step 2.5 generation. See `references/cost-control-and-rollback-lessons.md`.

**Setup:**
```bash
# 1. Create a fal.ai account and generate an API key at https://fal.ai/dashboard/keys
# 2. Add it to Hermes env or your shell profile. The workflow resolves FAL_KEY from:
#    live environment → ~/.hermes/.env → ~/.bashrc / ~/.zshrc / login profiles.
#    Shell files are parsed as text, so exports still work below interactive guards.
echo 'FAL_KEY=<your-key>' >> ~/.hermes/.env
# or: echo 'export FAL_KEY=<your-key>' >> ~/.bashrc

# 3. Install the fal client in the skill's venv:
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
pip install fal-client
```

If `FAL_KEY` cannot be resolved from the live environment, `~/.hermes/.env`, or common
shell startup files, or if `fal-client` is not installed, Step 2.5 warns the user via an
interrupt and skips gracefully to Step 3 after acknowledgement. The rest of the pipeline
is unaffected — the design will just be anchored to text alone, which produces weaker
and less spatially coherent results.

**Bridge handling:** This warning still appears as `pending_messages[0]` with type
`conversation` even though the text says it is "Proceeding to design phase." Surface the
message verbatim, then feed an explicit acknowledgement such as `continue` only after
the user agrees (or if the user has already asked to continue). Do not treat it as a
fatal error or restart the workflow.

**Diagnostic nuance:** the pending interrupt may be generic (`Image generation failed. Check your FAL_KEY and account credits.`) while the stream immediately above contains the real cause (for example `fal_client not installed — image generation unavailable`). When reporting the gate, include both the verbatim pending message and any adjacent workflow warnings. Do not claim the key/credits are the only likely fix if stdout names `fal_client` or another concrete dependency.

### Multimodal LLM (vision input)

Step 2.5 sends the generated desktop concept image to the configured LLM for palette
extraction and UI/chrome analysis. This requires a **vision-capable model** — text-only models will fail the
multimodal call and fall back to a text-only analysis stub.

**Confirmed working models (as of May 2026):**
- `claude-sonnet-4-5` / `claude-opus-4` via Anthropic native or OpenRouter
- `gpt-4o` / `gpt-4o-mini` via OpenAI
- `google/gemini-2.5-pro` / `google/gemini-2.5-flash` via OpenRouter
- `qwen/qwen2-vl-72b-instruct` via OpenRouter (budget option)

Text-only models (e.g. `deepseek/deepseek-v3`, `meta-llama/*`) will cause the
multimodal analysis step to fall back to a minimal stub — the design phase still runs,
but without real color extraction or UI guidance from the desktop concept image.

---

## 3. Failure Protocol — Read Before Anything Else


When something goes wrong, **report and stop**. Do not improvise repairs. The workflow is designed to self-heal where it can; the rest is the user's call.

- **On any non-zero exit or unexpected output:** show the literal error to the user, then stop. Do not run remediation commands.
- **Never** run `pip install`, `rm -rf`, or recreate `.venv`. Environment management is out of scope for this skill.
- **Never** call `graph.update_state(...)` directly, write `design.json` by hand, or modify files in `~/.config/rice-sessions/`. Only the workflow and the bridge script may write to session state.
- **Quote workflow output verbatim.** Do not paraphrase interrupt messages, validator reasons, or session metadata. If you don't have the exact text, re-read it before reporting.
- **User input timeout:** If the workflow prompts for input and the user does not reply within a reasonable time (e.g., 30 seconds), do not send an empty line or assume a default. Instead, re-prompt the user, remind them of the pending question, and wait for an explicit answer before proceeding. This avoids the workflow hanging on an EOFError or proceeding with unintended defaults.
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

Quick summary: write a small Python script that loads the graph from the SQLite checkpointer, checks `pending_messages`, and only calls `graph.stream(Command(resume=answer), config)` when an interrupt is actually pending. A no-answer status check must be read-only if `pending_messages` is already non-empty; do **not** call `graph.stream(None)` at an approval gate, because non-idempotent nodes such as Step 2.5 `visualize` can re-run before its return values have been checkpointed. The workflow also caches the pending Step 2.5 preview in `visualize.pending.json`; if accidental re-entry happens anyway, `visualize` must reuse that cached image/context and only clear it for explicit `back`/`regenerate`/feedback. Run it with the skill's venv activated — **no `RICER_*` env vars required**.

**Bridge script location:** Write to `/tmp/rice_bridge.py` at session start (disposable). Template is in `references/workflow-bridge-script.md`. If the file already exists, read it before overwriting; another concurrent agent/session may have refreshed the bridge, and blindly writing it can trigger sibling-modification conflicts. Reuse an existing bridge if it matches the current template, otherwise replace it deliberately with the reference template.

**Resume safety:** Never send an answer like `"skip"`, `"approve"`, or `"retry"` unless the bridge's previous JSON showed a non-empty `pending_messages` array. The current bridge template exits with code 2 instead of starting normal graph execution when no interrupt is pending.

**Model / API resolution:** `workflow.config.resolve_llm_config()` auto-loads model, base URL, and API key from `~/.hermes/config.yaml` and `~/.hermes/.env`. The agent should not pass `RICER_MODEL`/`RICER_BASE_URL`/`RICER_API_KEY` for normal runs; they exist purely as opt-in overrides (e.g. for testing a different model). If Hermes is using `openai-codex`, the workflow uses the same Hermes OAuth token store/refresh path (`~/.hermes/auth.json`) and wraps Hermes Agent's Codex Responses adapter behind the usual `get_llm().invoke(...)` interface. Consumers must not assume that this shim supports LangChain-only conveniences such as `with_structured_output`; Step 6 implement spec generation should keep a JSON-text fallback for invoke-only providers. See `references/workflow-llm-errors.md` for diagnostics, the Codex structured-output pitfall, and regression-test patterns.

**Sudo workaround:** When the bridge hits a `sudo_password` interrupt, feed `"skip"` to skip the package, then install it manually with `sudo pacman -S <pkg>` from the agent terminal (which CAN run sudo). Then resume the workflow via the bridge.

### Presenting Previews to the User

When Step 2.5 generates `visualize.html` or Step 4 generates `plan.html`, open them with
`brave <path>` — do NOT use `open`, `xdg-open`, or start an http.server. The user has
Brave as their default browser.

For Markdown planning/review documents (`.md`), do **not** open the raw file in Brave:
Brave displays local Markdown as plain text unless an extension/converter is involved. For
this user, prefer Ghostwriter for rendered Markdown plan review. Before launching it,
check whether the exact plan file is already open in a Ghostwriter process; Ghostwriter
auto-refreshes already-open files after edits, so do not spawn duplicate windows just to
refresh the review. Use the `plan-review-ghostwriter` helper instead of rewriting the
process check inline:

```bash
python3 /home/neos/.hermes/skills/software-development/plan-review-ghostwriter/scripts/check_ghostwriter_open.py /absolute/path/to/plan.md
```

Exit code `0` means matching PID(s) were printed; `1` means no matching process was found;
`2` means the path was invalid. If the check prints a PID, leave Ghostwriter alone and
tell the user the open document will refresh. If it prints nothing but the user has
already said the file is open in Ghostwriter, trust that and do not relaunch. Only run
`ghostwriter <file.md>` when the check finds no matching process and there is no
user/context signal that the file is already open. Fallbacks only when Ghostwriter is
unavailable: `inlyne view <file.md> --theme dark --page-width 1100 --win-size 1300x900`,
VS Code preview, then `glow -p -w 120 <file.md>` as a terminal fallback. Avoid remote-CDN
`file://` HTML renderers; Brave may block or fail those scripts.

### Pitfall: Real Image References Are Not Wallpapers

When the user asks for concrete/real image references, gather screenshots or artwork as
style evidence for UI grammar — menu borders, panels, icon silhouettes, materials,
lighting, density, and spatial hierarchy. Do not route that request to wallpaper sourcing
and do not treat any reference image as the desktop wallpaper unless the user explicitly
chooses it as wallpaper. Reference-grounded generation should synthesize a new desktop
concept from examples; wallpaper selection is a separate decision/gate. See
`references/reference-grounded-desktop-overviews.md` for the full hierarchy and checks.

### Pitfall: Representative Overview, Not Cinematic Hero Still

The Step 2.5 image is a representative desktop overview concept. Avoid terminology and
prompts that steer image models toward cinematic poster/hero framing. The generated image
must fill its canvas edge-to-edge with the desktop overview: no letterbox bars, no black
bands above/below, and no framed movie-still presentation. If the user reports bars, inspect
the generated image pixels as well as the HTML CSS. Also verify the target aspect ratio:
primary monitor may be 16:9 while the full virtual desktop can be ultrawide/multi-monitor.
See `references/reference-grounded-desktop-overviews.md`.

### Pitfall: Quickshell Before EWW on KDE Wayland

For KDE Wayland custom widget/panel chrome, evaluate Quickshell before committing to EWW.
If `widgets:eww` appears on KDE Wayland, verify that it was explicitly requested or that
Quickshell is unavailable. Repeated EWW syntax/runtime problems (Yuck geometry, shell `$1`
interpolation, empty first-render values, missing helper commands) are a switch-framework
signal, not just a reason to keep patching EWW.

### Pitfall: Hero Image Is the Creative Source of Truth

For creative preview/originality complaints, inspect Step 2.5 first. The desired flow is:
FAL `fal-ai/nano-banana` generates one full-desktop representative overview image (primary-monitor 16:9, or target-aware multi-monitor/ultrawide ratio when screen geometry is available) → multimodal
analysis extracts palette/UI guidance → HTML previews frame that overview and add palette /
terminal color views. Do not let `plan.html` become the primary creative artifact or a
generic card/style-guide mockup. Regression signals: `fal-ai/flux/dev`, `guidance_scale`,
`num_inference_steps`, missing `visual_context` in `plan_node`, or prompts that say
"clean professional concept art" / "generic card layout". Details and tests live in
`references/desktop-preview-generation.md`.

**Preview pipeline architecture:** Step 2.5 is implemented as the local
`workflow/preview_pipeline/` controller, borrowing hermesfy-studio-style DAG, budget,
cache, provider, and validator patterns without depending on hermesfy-studio itself.
Preserve this self-contained pipeline when making changes: keep `nano-banana` as the
single paid overview provider by default, keep explicit user approval before any extra
paid generation, and enforce `PreviewBudgetGate` caps/history instead of ad-hoc retry
loops. Session-specific research lives in
`references/hermesfy-studio-preview-pipeline-research.md`.

### Autonomous Foreman Mode

When the user explicitly delegates the whole run ("do the entire thing autonomously",
"manage it yourself end-to-end", "edit the skill as issues break it, then continue"),
treat that as authorization to operate the workflow as foreman: answer aesthetic gates
from stable user preferences, reject mismatched previews, patch verified workflow bugs,
run targeted tests, then continue. This delegation does **not** allow hand-editing
`design.json`, checkpoints, or session state to force progress. Detailed operating
contract and verification checklist: `references/autonomous-foreman-mode.md`.

In foreman mode, run an explicit **change → check/confirm → next change** loop. Before
final handoff, prove preview-plan-implementation alignment: if the preview/plan shows a
non-default toolbar, the default KDE panel feel must be replaced or hidden behind a
working widget toolbar; the wallpaper must be changed; and the result must implement the
plan's originality moves rather than stopping at icon/palette swaps. Use
`references/preview-plan-implementation-alignment.md` for the live verification contract.

### Pitfall: Bad Wallpaper Means Source Real Candidates, Not Procedural Filler

If the applied wallpaper is rejected as ugly, generic, or unlike the approved direction, switch to `references/wallpaper-sourcing.md`: gather real image-search candidates (Alpha Coders / Wallhaven first), visually rank thumbnails against the design brief, then apply a full-resolution local file. Do not improvise another procedural/generated placeholder unless the user explicitly asks for local generative art. For this user, wallpaper carries the world/ambience; a weak background invalidates the rice even if widgets and palettes technically pass.

### Pitfall: Quickshell Visibility Is Not Quickshell Success

For KDE Wayland, a visible Quickshell rail/bar still fails if it is ugly, fake, non-functional, or implemented as normal app-window chrome. Validate command targets on the audited system, avoid obsolete KDE5-only commands unless verified, ensure promised notification/quest widgets are real integrations or honestly labelled decorative cards, and compare the live screenshot to `plan.html`/`visualize.html`. A high craft score based only on QML existence and palette tokens is not enough.

If the preview/plan promises shell chrome, every promised Quickshell surface should be a `PanelWindow`; do not use `FloatingWindow` for launchers, panels, quest/notification cards, menus, or desktop widgets on KDE/Wayland because it can render as a decorated titlebar window. Use `PanelWindow` with anchors/margins and `exclusionMode: ExclusionMode.Ignore` for visually floating cards. Exact approved palette hexes should remain in generated QML so static alignment checks catch drift. See `references/quickshell-kde-shell-chrome.md`.

For ornate RPG/Diablo/bonfire Quickshell, visible panels must not be built from flat gray/dark `Rectangle` interiors with only palette/icon changes. Use generated texture assets as tiled `Image` fills and `BorderImage` 9-slice frames for panels/buttons/slots; leave `Rectangle` only for transparent borders, shadows, masks, small meter fills, or glints. Live screenshot/vision verification must explicitly reject "gray boxes everywhere" and require at least three physical UI cues such as resource orbs/meters, recessed inventory slots/grid, relic/quickslot belt, gear/equipment altar, or item-detail/stat panes.

For custom dashboards/widgets, a file/palette craft score is not enough. The target architecture is a game-UI-style component DAG lowered into Quickshell/EWW/AGS/Fabric: typed HUD/panel/button/slot/meter/menu components, state machines (`default`/`hover`/`pressed`/`active`/`disabled`), state-specific assets, layout constraints, data bindings, and callbacks. Resolve the approved preview source, detect the actual UI cluster, segment each promised element and per-control action region, normalize contracts, bind safe desktop actions, synthesize a framework-neutral component model, specify hover/pressed visual states, compile/validate ornate assets, choose a framework adapter, scaffold a sandbox, generate the same artifact that will be visually/functionally reviewed, launch/capture/score it, validate buttons/data bindings, compose accepted attempts, then promote to the live desktop with rollback support. The safe milestone order is: dry-run fake renderer → Quickshell sandbox codegen/static validation → bounded Quickshell runtime launch + screenshot + real visual scoring → feature-flagged `craft_node()` integration → live promotion/rollback. Use `references/widget-dag-task-breakdown.md` for the node-by-node DAG and adapter boundary contract. Do not integrate sandbox widgets into the main craft path until bounded runtime visual validation exists: generated QML is not success, and visible Quickshell is not success unless target crop vs real screenshot crop passes visual/function gates. If review artifacts show "gray boxes", inspect target crops first: preview-texture mode may be faithfully copying empty background because segmentation assumed a fixed bottom strip while the preview UI is elsewhere. Detect the foreground UI cluster, label the report `detected preview UI cluster`, and only trust scores when target crops contain real widget pixels. Dynamic widgets need semantic contracts too: clocks/status meters must declare data sources, update intervals, and framework-native bindings; a visually similar static placeholder such as `12:00` is a hard failure. Visual and functional validation must run against the same generated QML artifact: preview-texture mode may copy target crops for visual upper-bound scoring, but it must also carry functional overlays/bindings such as `Timer`/`new Date()`/`Qt.formatDateTime(...)` for clock contracts and explicit action hitboxes for buttons. The harness should emit both `function-validation` (contract honesty: real/missing commands and data sources) and `artifact-function-validation` (same generated file contains the bindings/hitboxes, with QML path + SHA-256). If the user asks to manually test a widget on screen, launch the current sandbox QML artifact being validated, not a separate visual-only or component-only surrogate; verify the process is running and visible via screenshot before claiming it is up, then report PID/session id and which controls are live vs decorative/unbound. If vision analysis is unavailable, verify visibility with process/log evidence plus local screenshot/template probes rather than making an unsupported visual claim. Before any live Quickshell/EWW/AGS/Fabric promotion, run the dry-run sample harness and verify it only writes under `--out`; reject symlinked output roots/subdirectories and unsafe artifact ids because "dry-run" is not a sandbox if paths can escape. Runtime adapters must also clean up whole process groups, localize screenshot crops from runtime evidence instead of guessed coordinates, reject pre-existing symlink artifact files, keep copied assets under `--out`, and record attempted failed launches honestly. See `references/widget-dashboard-dag.md`, `references/widget-dag-task-breakdown.md`, `references/widget-next-step-gate.md`, `references/widget-pipeline-quickshell-sandbox-milestone.md`, `references/widget-runtime-validation-hardening.md`, and `references/quickshell-runtime-localization-replay.md`.

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
handles manifest-owned files. Then verify/remove any manual post-workflow artifacts
that were not captured in manifests (for example generated wallpapers, custom
Plasma desktoptheme directories, Quickshell config/assets, or EWW files). After
`undo-session`, do **not** trust `already undone` alone: run an active-config residue
sweep for generated markers and theme hexes in `~/.config/kitty`, `~/.config/rofi`,
`~/.config/gtk-3.0`, `~/.config/gtk-4.0`, `~/.config/plasma-org.kde.plasma.desktop-appletsrc`,
and active local theme/icon dirs. If the user asked for "default", archive/remove
loaded app overrides such as `kitty.conf`, `theme.conf`, `rofi/config.rasi`,
`rofi/hermes-theme.rasi`, and GTK `gtk.css` so package defaults take over; restore
from backups only when the user asks for the previous pre-rice state rather than
stock defaults. Fall back to the baseline JSON procedure only when the manifest is
missing or corrupt. See §Undoing / Rolling Back a Rice Session below and
`references/cost-control-and-rollback-lessons.md`.

### Pitfall: Visualize Approval — Caveats Need Stage-Aware Handling

Step 2.5 `visualize` only approves on exact approval strings (`approve`, `yes`, `ok`,
`looks good`, `good`). Any other free-form answer — even "looks good, but..." — is
interpreted as feedback and regenerates the FAL hero image. If the user wants to keep
the current menus/chrome but make a caveat such as "wallpaper should be manually
swappable," first feed exact `approve` to lock the hero/context, then carry the caveat
into Step 4 plan feedback or later implementation/handoff. Never pass an approval plus
caveat as one visualize answer unless regeneration is intended.

### Pitfall: Visualize approval can regenerate before approving

Because the image URL/visual context may not be checkpointed until after the
interrupt returns, a bridge call that answers `approve` can re-enter the visualize
node and generate/analyze a fresh image before logging "AI desktop preview approved".
Watch stdout: the image actually approved is the last `FAL image generated:` URL
immediately before `AI desktop preview approved`, not necessarily the one the user
just saw. If this happens and visual identity matters, report the mismatch and open
or regenerate the newly approved preview rather than claiming the older image was
locked in.

### Pitfall: Backtracked visualize can keep stale HTML/context

Observed failure: rejecting a Step 4 plan can route back to Step 2, confirm a new
direction, then Step 2.5 may generate a fresh FAL image URL while `visualize.html`
still contains the previous direction's title, alt text, palette, terminal mock,
style copy, and footer (for example a new dark bonfire image inside stale
`maple-village-questboard` HTML). Do not approve that mixed artifact. Treat it as
stale state, quote the mismatch, and prefer a clean restart/wipe or another
workflow-owned regenerate/backtrack path rather than hand-editing `visualize.html`,
`design.json`, or checkpoint state.

### Pitfall: Explore Proposal — Asking for More Examples Can Still Advance

At Step 2 `explore`, the workflow treats free-form replies to the numbered direction
list as selection/refinement input. A reply like "I like 1 and 2. Can you come up with
new examples similar?" may be interpreted as enough creative direction and route
forward to Step 2.5 instead of surfacing another numbered set. If the user explicitly
asks for more examples/options, feed a stronger instruction such as:

`Do not finalize yet. Generate a new numbered set of directions similar to 1 and 2, then ask me to pick.`

After the bridge call, inspect stdout/JSON. If it advanced to `visualize` anyway, report
that the workflow converged early, open the generated preview, and let the user use
`back` if they still want more exploration.

### Pitfall: Plan Approval — Detailed Critique vs Bare "regenerate"

When the user rejects a preview with specific complaints (e.g., "I don't like the
colors", "doesn't look like a game menu", "style is tacky"), pass their **verbatim
feedback** as the change request rather than the bare keyword `"regenerate"`. The
plan and refine nodes use the content of the answer to steer the next iteration;
detailed critique gives them concrete constraints. Use the user's detailed critique
for style changes; reserve bare `"regenerate"` for cases where the user explicitly
asks for a fresh image with no additional constraints.

If the user rejects the overall style or says to scrap the desktop image/direction,
expect the plan node to classify the feedback as `explore` and route back to Step 2.
That is correct; surface the new numbered directions and let the user pick/combine/tweak.
For this user's dark RPG taste, preserve useful implementation constraints across that
backtrack: thinner Diablo/Dark-Souls-style ornament borders, no bulky frame around the
terminal, atmospheric world/wallpaper first, windows styled like in-game menus, widget
menu replacing toolbar.

### Pitfall: sudo in Agent Terminal

The agent terminal CAN run sudo commands (unlike the bridge script which cannot handle
`sudo_password` interrupts). Try `sudo pacman -U <path>` or `sudo pacman -S <package>`
directly — it may work depending on session credential state. The handoff document's
claim that "user must run workflow directly for sudo step" applies only to the bridge
script pattern.

> **KDE implementation pitfalls** (kwin_wayland --replace, Konsole transparency, cursor
> fallback, kitty include, profile name, fastfetch suffix, EWW craft scoring / hyprctl leakage) → see
> `references/kde-known-issues.md` and `references/kde-post-implementation.md`.
>
> **EWW craft pitfall:** KDE sessions must not inherit Hyprland examples. If `widgets:eww`
> scores low despite writing both `eww.yuck` and `eww.scss`, check whether the score is
> incorrectly looking for palette colors per file instead of across the file set, and inspect
> generated Yuck for `hyprctl` commands. On KDE/Plasma, prompts should explicitly forbid
> `hyprctl` unless the audited WM is Hyprland.

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
| 2.5 | `visualize` | **DAG preview pipeline + FAL image generation + multimodal analysis.** Runs the self-contained `workflow/preview_pipeline/` controller: prompt construction, budget/cache gates, `fal-ai/nano-banana` overview generation, vision analysis, validation, and HTML rendering. Generates a single full-desktop AI theme concept image showing wallpaper, window chrome, terminal, launcher, panels/widgets, borders, menus, and icon language. This image is the hero centerpiece and creative source of truth; HTML previews should frame it and provide palette/terminal views, not replace it with a generic card mockup. Sends it to the configured multimodal LLM for a separate interpretation pass that extracts a 10-key palette, style description, UI/chrome guidance, `visual_element_plan` (visible element → concrete tool/materializer → fallback → config targets), and `validation_checklist` (visual contract probes). Renders `visualize.html` desktop concept preview. Interrupts for user approval; loops on explicit `regenerate`; routes back to `explore` on `back`. Skips gracefully if `FAL_KEY` is unset, `fal-client` is missing, or `PreviewBudgetGate` blocks spending. |
| 3 | `refine` | Produces and validates `design.json` — 10-key palette + recipe-specific fields + the visual execution contract. When `visual_context` is available (Step 2.5 approved), the extracted palette, UI/chrome analysis, visual element decomposition, tool/materializer choices, and validation probes are injected into the seed prompt so the LLM anchors colors, desktop composition, and implementation strategy to the AI concept image. KDE requires `originality_strategy` and `chrome_strategy`; widgets/panels are design-driven, not mandatory. |
| 4 | `plan` | Generates `plan.html` as a secondary validation preview around the approved overview image and visual execution contract: dominant AI desktop overview if available, palette, terminal color views, custom chrome/composition, launcher, optional widgets, and enough detail for the user/foreman to validate that the planned implementation matches the interpreted elements. Interrupts for user approval; loops on `regenerate` or change requests. |
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

If the user has already given an explicit destructive instruction such as "wipe them, start fresh", that counts as approval for step 2 after the dry-run confirms only rice session artifacts are targeted. Run `--yes`, verify `resume-check` returns `[]`, then immediately launch the fresh session.

Then launch a fresh session with PTY as usual (no `RICER_*` env vars needed — the workflow auto-resolves model and API credentials from Hermes config).

---

### Troubleshooting: LLM Errors (400 / 401)

`openai.BadRequestError: 400 — '<model-id> is not a valid model ID'`,
`openai.AuthenticationError: 401 — 'User not found.'`, and
`The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable`
are caused by `workflow/config.py` resolution gaps (stale `config.yaml` key vs `.env`,
hardcoded fallback model, env vars short-circuiting Hermes config, or failures in the `openai-codex` OAuth adapter path). Full
diagnosis snippets, root cause, Codex OAuth behaviour, and env-var override workarounds live in
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

**Plasma theme generation pitfall:** if `plasma_theme` scores 2/10 with every
expected `~/.local/share/plasma/desktoptheme/<Theme>/...` target missing while
apply reports OK, inspect `scripts/materializers/kde_extras.py::materialize_plasma_theme`.
The materializer must generate the custom desktoptheme package (`metadata.desktop`,
`metadata.json`, `colors`, `widgets/panel-background.svg`, `widgets/background.svg`,
`dialogs/background.svg`) before setting `plasmarc[Theme][name]`; merely selecting
a non-existent custom theme via `plasma-apply-desktoptheme` produces a false apply
success and fails verification. Regression coverage: `tests/test_kde_materializers.py::TestMaterializePlasmaTheme`.

**Step 6 verification mismatch pitfall:** if KDE elements score below 8 after apply OK,
first compare the LLM spec targets, materializer-written paths, verifier palette logic,
and score penalties before accepting a deviation. Validated fixes include palette checks
across the combined written file set, directory-safe reads, KDE decimal RGB triplet
matching, fallback targets for kitty/rofi/icon/window-decoration naming conventions,
custom Kvantum generation for non-`hermes-` palette-backed names, and forbidding Aurorae
targets unless an Aurorae materializer exists. Details and regression checklist:
`references/kde-implementation-verification-lessons.md`.

---

### Undoing / Rolling Back a Rice Session

Prefer the workflow's own undo verb — `scripts/ricer_undo.py` restores every
backed-up file, reapplies previous color schemes, cleans up injections, closes
EWW windows, and restarts plasmashell on KDE to flush in-memory color/icon state:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python3 scripts/ricer.py undo                    # undo active manifest only
python3 scripts/ricer.py undo-session            # undo current session's manifests newest→oldest
python3 scripts/ricer.py simulate-undo           # dry-run preview, no writes
python3 scripts/ricer.py simulate-undo-session --all  # dry-run every known manifest across history
python3 scripts/ricer.py undo-session --all -y        # restore all known workflow history when user wants stock/pre-automation defaults
```

After undo completes, tell the user to close and reopen any running Dolphin /
app windows — apps inherit icon tinting from the plasmashell session at launch
time. Also verify the actual restored target; rollback may restore the previous
rice (e.g. Bonfire Hollow), not stock KDE. Rollback must also force restored KDE
panels back to non-autohide via Plasma scripting (`panel.hiding = "none"`) after
plasmashell restarts **and normalize obviously broken panel geometry**: reset ultra-thin
heights (e.g. 12px strips left by a custom toolbar replacement) back to a stock-like
size such as 44px, and on multi-monitor/fractional-scale KDE layouts reset each
horizontal panel's `length`, `minimumLength`, `maximumLength`, `offset`, and alignment
against Plasma's own `screenGeometry(panel.screen)` values. Do not rely on kscreen/KWin
screen index ordering for this normalization; the Plasma scripting API owns the panel
objects and can number screens differently. Otherwise removing an EWW/Quickshell toolbar
can leave the stock Plasma toolbar apparently missing, unusably tiny, or visibly offset
from its clickable button hitboxes.

**Manual post-workflow artifacts:** `undo-session` only restores/deletes what its
manifests know about. If the agent added files after workflow completion, verify and
clean them explicitly: generated wallpaper files, custom Plasma desktoptheme dirs,
Quickshell `~/.config/quickshell/shell.qml`, and EWW `eww.yuck`/`eww.scss` files. If the
user asks for stock/pre-automation KDE, use `simulate-undo-session --all` and
`undo-session --all -y` before manual residue cleanup; ordinary `undo-session` may only
restore the previous rice. For wallpaper restore, rollback code must deterministically read the matching workflow
baseline/snapshot JSON and apply the exact recorded `kde.wallpaper.image_path` with
`plasma-apply-wallpaperimage`; do not substitute a theme wallpaper, generated bonfire
image, or arbitrary KDE stock wallpaper such as Kokkini when the snapshot recorded a
different path such as KDE Next. `scripts/ricer_undo.py::undo_session()` owns this as a
post-manifest guard, including `undo-session --all`, and must fail visibly if the baseline
wallpaper file is missing instead of silently choosing another wallpaper.
Use `references/cost-control-and-rollback-lessons.md` for the verification/removal
checklist.

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
| KDE Step 6 implementation verification lessons (spec/materializer/verifier/score mismatches, RGB triplets, fallback targets, Kvantum, Aurorae) | `references/kde-implementation-verification-lessons.md` |
| KDE post-implementation verification, manual elements, workflow gaps | `references/kde-post-implementation.md` |
| Manual baseline-restore procedure (undo fallback) | `references/baseline-restore-procedure.md` |
| LLM error patterns (400 invalid model, 401 auth) | `references/workflow-llm-errors.md` |
| Workflow environment/import/dependency failures, including missing `fal-client` for Step 2.5 | `references/workflow-environment-issues.md` |
| Konsole transparency on Wayland (broken upstream) | `references/konsole-wayland-transparency.md` |
| Chat-agent bridge (non-TTY resume helper) | `references/workflow-bridge-script.md` |
| Wallpaper sourcing (Alpha Coders + vision analysis; use when a real wallpaper is requested, when the approved design needs an atmospheric background, or when a generated/procedural wallpaper is visually weak/rejected) | `references/wallpaper-sourcing.md` |
| Reference-grounded desktop overviews: real UI references, generated overview hierarchy, letterbox/aspect pitfalls, Quickshell-vs-EWW policy | `references/reference-grounded-desktop-overviews.md` |
| Visual contract pipeline: interpretation → validation → planning/tool selection → execution → evaluation → visual confirmation | `references/visual-contract-pipeline.md` |
| Step 2.5 full-desktop AI preview generation pitfalls, FAL prompt invariants, bridge read-only status checks | `references/desktop-preview-generation.md` |
| Hermesfy Studio research: DAG/budget/validation patterns worth adapting for desktop preview generation, plus why it is not a drop-in linux-ricing dependency yet | `references/hermesfy-studio-preview-pipeline-research.md` |
| Workflow debugging lessons: subagent log triage, EWW craft scoring, Hyprland leakage, resume-check completion filtering, handoff craft-log gaps | `references/workflow-debugging-lessons.md` |
| Diablo II / dark RPG menu motif brief (campfire, carved borders, thorn borders, glyph buttons, black terminal, widget menus) | `references/diablo-rpg-menu-brief.md` |
| Autonomous foreman mode for delegated end-to-end runs, including skill/code patch-and-continue protocol | `references/autonomous-foreman-mode.md` |
| Preview-plan-implementation alignment: wallpaper, widget toolbar/panel replacement, originality beyond palette/icon swap, live screenshot/vision checks | `references/preview-plan-implementation-alignment.md` |
| Quickshell KDE shell chrome: PanelWindow-only contract for promised widgets, FloatingWindow/titlebar drift, restart/verification snippet | `references/quickshell-kde-shell-chrome.md` |
| Quickshell v0.3.0 type docs source of truth: locally ingested index/Markdown snapshot for QML config editing, codegen grounding, and static validation | `references/quickshell-v0.3.0-types/summary.md` + `references/quickshell-v0.3.0-types/index.json` |
| Quickshell ornate tiled borders: BorderImage/9-slice texture subprocess, seam validation, and live visual quality gate | `references/quickshell-ornate-tileable-borders.md` |
| Widget/dashboard DAG: Step 6 widget decomposition, sandboxing, visual-loss scoring, function validation, and framework adapter plan | `references/widget-dashboard-dag.md` |
| Widget DAG task breakdown: detailed node-by-node acyclic submodule plan for segmentation, contracts, asset compilation, framework adapters, runtime scoring, function validation, and promotion | `references/widget-dag-task-breakdown.md` |
| Widget pipeline Quickshell sandbox milestone: dry-run adapter contract, PanelWindow policy, stage-gate honesty, and verification checklist | `references/widget-pipeline-quickshell-sandbox-milestone.md` |
| Widget runtime validation hardening: bounded process-group cleanup, symlink/file safety, asset containment, screenshot/crop scoring caveats | `references/widget-runtime-validation-hardening.md` |
| Quickshell runtime localization replay: baseline/post-launch diffing, `runtime_surface_bbox`, compositor scaling, and real replay verification | `references/quickshell-runtime-localization-replay.md` |
| Widget same-artifact semantic gate: bind visual/runtime validation and functional validation to the exact generated QML artifact via path + SHA-256 | `references/widget-same-artifact-semantic-gate.md` |
| Widget framework interaction examples: Quickshell/EWW/AGS/Fabric references, Rivendell patterns, clicky button templates, hitbox/action/power-menu rules | `references/widget-framework-interaction-examples.md` |
| Widget next-step gate: after Quickshell docs ingestion, prove component-model synthesis and same-artifact sandbox visual/function validation before adding live promotion/rollback manifests | `references/widget-next-step-gate.md` |
| Bonfire Hollow session lessons: Dark Souls in-world desktop, thin ornaments, widget UX, stale visual-image and bridge-gate pitfalls | `references/bonfire-hollow-session-lessons.md` |
| Cost control + rollback lessons: paid FAL generation discipline, reuse-before-regenerate, and manual post-workflow artifact cleanup after undo | `references/cost-control-and-rollback-lessons.md` |