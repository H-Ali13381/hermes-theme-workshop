# Linux-ricing workflow debugging lessons

Use this reference when a running rice session reports secondary failures after an initial fix, especially around Step 6 craft/implement, Step 8 handoff, or `resume-check`.

## Pattern: split the diagnosis with subagents

When logs show multiple symptoms in different subsystems, dispatch independent subagents before editing:

1. Runtime/craft agent: inspect `workflow.log`, generated files, craft scorer, validators.
2. Install/package agent: decide whether package-manager warnings are blockers or already-installed false alarms.
3. Checkpoint/bridge agent: inspect LangGraph state, `pending_messages`, `state.next`, and bridge safety.

Ask for evidence, exact files/functions, and minimal patch recommendations. Then integrate centrally and run regression tests yourself.

## EWW craft scoring false low score

Symptom: `widgets:eww` writes both `eww.yuck` and `eww.scss` but scores around `6/10` and triggers a retry/approval gate.

Root causes to check:
- Scorer compares absolute written paths to relative required templates (`/home/.../eww.yuck` vs `eww.yuck`). Match basenames as well as exact paths.
- Palette scoring should evaluate the file set, not require every palette token in every individual file.
- Log score components (`required_present`, `palette_hits`, totals) so future failures are explainable.

Verification snippet:
```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python - <<'PY'
from workflow.nodes.craft import _score_details
from pathlib import Path
import json
session = Path('/home/neos/.config/rice-sessions/<thread-id>')
design = json.loads((session/'design.json').read_text())
print(_score_details(['/home/neos/.config/eww/eww.yuck','/home/neos/.config/eww/eww.scss'], design, ['eww.yuck','eww.scss']))
PY
```

Expected for a valid KDE EWW craft: total >= 8, both required files present.

## Quickshell token configs after high craft score

Symptom: workflow marks `widgets:quickshell` crafted, but the live desktop has no meaningful widget layer. Root causes observed: generated QML only creates a tiny/default-looking strip, hides the central menu by default, passes file/palette scoring without implementing the plan's promised inventory/rest/ember/menu/log surfaces, or shows buttons/cards that are visible but not actually useful.

Fix: static validation must compare generated QML against `visual_element_plan`. If the plan promises multiple Quickshell widget/panel/launcher/notification surfaces, the QML must define multiple visible `PanelWindow` shell surfaces and include labelled RPG widget grammar. Do not count `FloatingWindow` toward promised shell chrome on KDE/Wayland because it can render as a normal decorated app window with a titlebar. Preview match is not just color usage: parchment launcher surfaces should actually be parchment-toned when the preview shows parchment, blackiron bars should stay low-profile, and fake placeholder cards should not substitute for notification integration.

Functional validation must prove the controls work, not merely render:
- Prefer KDE6-safe commands (`qdbus6`, `kstart`, `kioclient6`, `systemsettings`, `dolphin`, `kitty`) with fallbacks that exist on the audited system; avoid obsolete `kstart5`/`qdbus` assumptions unless verified.
- For every launcher/action button, run or statically validate its command and flag missing binaries.
- For status widgets, ensure probes return non-empty values and do not rely on fake static labels as the main content.
- For notification/quest widgets, either integrate a real notification service/model or label the card as a decorative/session card; do not claim notification support from a hardcoded card that auto-hides.
- Runtime verification must run `quickshell list`, inspect logs for `Configuration Loaded`, capture a screenshot, and compare the screenshot against `plan.html`/`visualize.html` before completion.

## Preview image accidentally used as wallpaper

Symptom: KDE wallpaper becomes the Step 2.5 desktop preview image, including mock UI, instead of a swappable atmospheric wallpaper artifact. Root cause: cleanup inferred a wallpaper target from `visual_element_plan` but downloaded `visualize_image_url` into it when no local file existed. That URL is a full desktop concept preview, not a wallpaper.

Fix: when wallpaper is declared only via `visual_element_plan`, cleanup should generate or source a local wallpaper artifact and only use `visualize_image_url` as fallback for explicit wallpaper paths. Verification must compare hashes/paths to prove the active wallpaper is not the preview mockup.

## EWW runtime parse failures after high craft score

Symptom: `widgets:eww` scores high because files exist and use the palette, but `eww open <window>` fails or logs runtime errors. Known examples:
- `Failed to parse "calc(100% - 48px)" as a length value` from `:geometry :width "calc(...)"`.
- `Failed to turn `` into a value of type f64` after EWW consumes shell `$1`/`$2`/`$3` fields inside `defpoll` commands, causing awk scripts to run malformed.

Prevention:
- EWW geometry lengths must be literal `px`/`%` values; never CSS `calc()`.
- Avoid shell `$` fields in generated Yuck commands; prefer grep/cut/python one-liners, or escape carefully.
- `workflow/nodes/craft/codegen.py::evaluate_files()` statically rejects `.yuck` files containing geometry `calc()` and shell-style `$` variables in command-heavy configs before writing.
- `workflow/nodes/craft/frameworks.py` includes these constraints in the EWW syntax prompt.

Regression tests:
- `tests/test_craft_node.py::TestBuildPromptInjectsTemplates::test_eww_prompt_warns_against_calc_geometry_and_shell_dollar_fields`
- `tests/test_craft_node.py::TestEvaluateFiles::test_rejects_eww_calc_geometry`
- `tests/test_craft_node.py::TestEvaluateFiles::test_rejects_eww_shell_dollar_fields`
- `tests/test_craft_node.py::TestEvaluateFiles::test_rejects_eww_raw_variable_progress_value`

## KDE lock screen spec over-promises custom LnF package

Symptom: `lock_screen:kde` repeatedly scores `5/10`; verify shows only `~/.config/kscreenlockerrc` written while specs target `~/.local/share/plasma/look-and-feel/<Theme>/contents/lockscreen/*` and require palette colors.

Root cause: current KDE lock-screen materializer only sets `kscreenlockerrc` Greeter Theme to Breeze/BreezeDark and reuses a wallpaper when resolvable. It does not generate custom lock-screen QML or write palette colors directly into `kscreenlockerrc`.

Fix: keep `workflow/nodes/implement/spec.py` honest for `lock_screen:kde`: targets should be only `~/.config/kscreenlockerrc`, `palette_keys` should be `[]`, and notes must describe BreezeDark + wallpaper support instead of claiming parchment/smoked prompt QML. Regression: `tests/test_implement_spec.py::ImplementSpecTests::test_lock_screen_kde_prompt_matches_materializer_limitations`.

## Cleanup directory targets false errors

Symptom: workflow completes, but cleanup reports errors like `BonfireBlackiron: cannot read: [Errno 21] Is a directory` after Plasma theme specs include directory targets.

Root cause: `cleanup_node` validates every spec target with `validate_file()` and previously tried to read directories as files.

Fix: skip `Path.is_dir()` targets during cleanup syntax validation. Regression: `tests/test_cleanup_reloader.py::CleanupNodeValidationTests::test_cleanup_skips_directory_targets_when_validating_specs`.

## Kvantum active theme drifts after cleanup/look-and-feel

Symptom: `kvantum_theme` verifies generated files but final live state shows `~/.config/Kvantum/kvantum.kvconfig` still set to `KvDark` instead of the generated theme.

Root cause: later KDE look-and-feel/finalization actions can leave `widgetStyle=kvantum` while the Kvantum config keeps a stale theme name.

Fix: KDE finalization should re-persist `design["kvantum_theme"]` into `~/.config/Kvantum/kvantum.kvconfig` and keep `kdeglobals[KDE] widgetStyle=kvantum`. Regression: `tests/test_kde_finalization.py::KdeFinalizationTests::test_kde_finalization_runs_safe_idempotent_actions`.

## Fastfetch spec filename drift false low score

Symptom: `fastfetch` writes `~/.config/fastfetch/config.jsonc` and `config.json` compatibility symlink, but the LLM spec targets a theme-specific file such as `~/.config/fastfetch/<theme>.jsonc`; verification reports no files written and scores `2/10`.

Root cause: `materialize_fastfetch()` intentionally writes the default Fastfetch config filenames, while specs may describe a theme-named config. `workflow/nodes/implement/verify.py::_fallback_targets()` must include `~/.config/fastfetch/config.jsonc` and `~/.config/fastfetch/config.json` for the `fastfetch` element so scoring evaluates the real deterministic outputs.

Regression test: `tests/test_implement_spec.py::VerifyElementTests::test_fastfetch_uses_default_config_fallback_when_spec_names_theme_file`.

## Hyprland leakage into KDE EWW

Symptom: generated KDE/Plasma EWW config contains `hyprctl` commands.

Root cause: EWW examples/templates often use Hyprland workspaces. KDE sessions must not inherit those examples.

Fix pattern:
- Pass audited `device_profile` into craft research/prompt context.
- Prompt must explicitly forbid Hyprland/i3/Sway commands unless the active WM is that compositor.
- Keep EWW reference examples desktop-neutral or branch by desktop.

Verification:
```bash
grep -R "hyprctl" ~/.config/eww || true
```
There should be no matches on KDE/Plasma.

## Package install warnings that are not blockers

Pacman warnings such as `is up to date -- reinstalling` can appear during a successful or non-blocking install path. If install command return code is non-zero, verify package presence before declaring failure. Only append an install error if the package remains absent.

## Completed LangGraph sessions showing in resume-check

Symptom: workflow log says `session complete`, `graph.get_state(...).next == ()`, but `scripts/session_manager.py resume-check` still reports the thread as in progress (e.g. `Step 36`).

Root cause: listing latest checkpoints is not the same as listing resumable graph states. Completed threads retain checkpoints but have no next node.

Fix pattern:
- `workflow/run.py --list --json` should call `graph.get_state(config)` for each latest thread.
- Filter out entries where `state.next` is empty.
- Prefer workflow `current_step` from `state.values` over LangGraph metadata step counters for user-facing status.

Verification:
```bash
python3 scripts/session_manager.py resume-check
# Completed-only state should print []
```

## Handoff false missing-elements

Symptom: `handoff.md` claims EWW/widgets were not implemented although craft log shows `widgets:eww` with score >= 8.

Root cause: handoff LLM saw `impl_log` but not `craft_log`.

Fix pattern:
- Include `craft_log` in the handoff payload and merge it into the implementation table source.
- Prompt: craft/widget records count as implemented if verdict is not skipped and score >= 8.
- Add deterministic scrub for contradicted missing-widget claims; don't rely only on the LLM.

Verification:
```bash
grep -nEi 'eww|widget|not implemented|missing' ~/.config/rice-sessions/<thread-id>/handoff.md
```
The handoff should list `widgets:eww` as crafted/verified, not missing.
