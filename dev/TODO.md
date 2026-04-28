# linux-ricing TODO

## Open Issues

### Code Review — from Auggie review 2026-04-28

#### 🔴 High Severity (Broken Functionality)

- [ ] **[BUG] Dunst fragment uses double-quoted color values — invalid INI syntax**
  `scripts/ricer.py` `materialize_dunst` fragment uses `frame_color = "#89b4fa"` etc. Dunst's
  INI parser expects raw hex values without quotes. These entries are silently ignored or error.
  **Fix:** strip the surrounding `"..."` from all color values in the dunst fragment.

- [ ] **[BUG] Dunst `include` directive injected inside `[global]` section**
  `scripts/ricer.py` ~L1076–1083: when `[global]` is found, the `include =` line is injected as
  the first key inside the section. Dunst's `include` is a top-level directive that must appear
  outside any `[section]` block — inside `[global]` it is treated as an unknown key and silently
  ignored. **Fix:** inject the `include` line before the `[global]` header, not after it.

- [ ] **[BUG] Infinite retry loop in `implement_node` — no retry counter**
  `workflow/nodes/implement/__init__.py` L72–75: when the user selects `"retry"` at the score
  gate the element is prepended back to the queue with no counter. If it consistently scores below
  the threshold the session loops indefinitely. **Fix:** add a per-element retry count to the
  state or record; interrupt with a hard `"skip"` after N retries.

#### 🟠 Medium Severity (Incorrect Behaviour in Edge Cases)

- [ ] **[BUG] `kdeglobals` ColorScheme regex can match across INI sections**
  `scripts/ricer.py` ~L215–220: `re.search(r"^\[General\].*?^ColorScheme=(.+)$", text,
  re.MULTILINE | re.DOTALL)` — `re.DOTALL` lets `.*?` cross section boundaries. A
  `ColorScheme=` key in any section after `[General]` can produce a false match.
  **Fix:** use a section-aware parser (e.g. `configparser`) or a tighter single-section regex.

- [ ] **[BUG] KDE force-toggle only checks stdout for `"already set"`**
  `scripts/ricer.py` L554: some `plasma-apply-colorscheme` versions emit this string to stderr.
  The code checks only `out_pre` (stdout), so the BreezeClassic bounce is skipped and the theme
  may not re-apply. **Fix:** check both stdout and stderr for the sentinel string.

- [ ] **[BUG] `ChatAnthropic` never receives the API key from Hermes config**
  `workflow/config.py` L90–94: `api_key` is resolved from `~/.hermes/config.yaml` / `.env` but
  never forwarded to `ChatAnthropic(...)`. Falls back to `ANTHROPIC_API_KEY` env var; if unset,
  all LLM calls fail silently. **Fix:** pass `api_key=api_key` to `ChatAnthropic` when non-empty.

- [ ] **[BUG] Package installer is Arch-only with no distro detection or fallback**
  `workflow/nodes/install/resolver.py` `install_packages()` only tries `pacman` and `yay`. The
  skill supports KDE and GNOME, both common on Debian/Ubuntu/Fedora. Non-Arch users get silent
  install failures. **Fix:** detect distro (`/etc/os-release`) and dispatch to `apt-get` /
  `dnf` / `zypper` as appropriate, or warn explicitly that only Arch is supported.

- [ ] **[BUG] `_remove_injected_block` leaves a stray blank line on undo**
  `scripts/ricer.py` L2571–2598: injection prepends `marker\nimport_line\n\n` (trailing blank
  line). The removal strips only the marker line and the next line — the blank line is left
  behind. Repeated apply/undo cycles accumulate blank lines at the top of the config.
  **Fix:** extend removal to also consume a trailing blank line after the injected directive.

- [ ] **[BUG] YIQ threshold inconsistency between GTK dark-mode detection and lock screen**
  `scripts/ricer.py` L2229 (`materialize_gtk`) uses `luminance < 128` to detect dark themes.
  `_lockscreen_lnf_for_palette` (L1650) calls `yiq_text_color` which uses `< 200` (designed for
  text readability, not theme classification). Backgrounds with YIQ 128–200 are misclassified as
  dark for the lock screen. **Fix:** use the same `< 128` threshold consistently, or extract a
  dedicated `is_dark_palette()` helper.

- [ ] **[BUG] `refine.py` silently falls back to KDE recipe for unsupported desktops**
  `workflow/nodes/refine.py` L26: `recipe = recipe if recipe in SUPPORTED_DESKTOP_RECIPES else "kde"`.
  Any unrecognised recipe silently produces a design with KDE-specific fields irrelevant to the
  actual environment. The audit node routes unsupported desktops to `END`, but if this fallback
  fires (e.g. during a resume), the LLM gets misleading instructions.
  **Fix:** raise an explicit error or return an error state rather than silently defaulting.

#### 🟡 Low Severity / Code Quality

- [ ] **[QUALITY] Mid-module `import` violates PEP 8 E402**
  `scripts/ricer.py` L98: `from desktop_utils import discover_desktop` appears after module-level
  constants and function definitions. Move it to the top of the file with other imports and remove
  the `# noqa: E402` comment.

- [ ] **[QUALITY] `_strip_jsonc_comments` is duplicated verbatim in two files**
  Identical 30-line function exists in both `workflow/nodes/implement/score.py` and
  `workflow/nodes/cleanup/reloader.py`. Extract to a shared utility module (e.g.
  `workflow/utils.py`) and import from both.

- [ ] **[QUALITY] `detect_chassis()` spawns a `cat` subprocess for a simple file read**
  `workflow/nodes/audit/detectors.py` L48: `run(["cat", "/sys/class/dmi/id/chassis_type"])`.
  **Fix:** use `Path("/sys/class/dmi/id/chassis_type").read_text()` directly — more portable,
  no subprocess overhead.

- [ ] **[QUALITY] `detect_apps()` uses external `which` instead of `shutil.which()`**
  `workflow/nodes/audit/detectors.py` L84: spawns `which` per-app. `shutil.which()` is the
  stdlib equivalent (already used in `ricer.py`'s `cmd_exists`). **Fix:** replace the
  `run(["which", app])` calls with `shutil.which(app) is not None`.

- [ ] **[QUALITY] `implement_node` doesn't guard against an empty element queue**
  `workflow/nodes/implement/__init__.py` L20: `element = queue[0]` raises `IndexError` if
  the queue is empty. **Fix:** add a guard — `if not queue: return {}` — before indexing.

- [ ] **[QUALITY] `_run_loop` catches `StopIteration` — masks real errors**
  `workflow/run.py` L87–88: in Python 3.7+ `StopIteration` escaping a generator becomes
  `RuntimeError`. Catching it explicitly here can mask legitimate errors from `graph.stream()`.
  **Fix:** remove the bare `except StopIteration: pass` branch; `GraphInterrupt` is the correct
  mechanism.

- [ ] **[QUALITY] `discover_desktop()` called independently by each Hyprland materializer**
  `scripts/ricer.py` L1117 and L1208: both `materialize_hyprland` and `materialize_hyprlock`
  call `discover_desktop()` (which runs `ps aux`) on each invocation. **Fix:** cache the result
  or pass it as a parameter from `materialize()`.

- [ ] **[QUALITY] Brace-counting heuristic for `.conf`/`.ini` syntax validation is fragile**
  `workflow/nodes/implement/score.py` L122–126 and `workflow/nodes/cleanup/reloader.py` L65–69:
  counting `{` + `[` vs `}` + `]` produces false failures when config values contain bracket
  characters (e.g. Pango markup in dunst, array syntax). **Fix:** drop the heuristic for
  `.conf`/`.ini` files, or explicitly limit it only to formats where it is reliable (CSS).

---

### Workflow Wiring — from Auggie review 2026-04-28

- [x] **[WIRING] `session_manager.py resume-check` is blind to LangGraph sessions**
  `scripts/session_manager.py:cmd_resume_check` only scans `~/.config/rice-sessions/` for
  `session.md` files. Sessions started via `workflow/run.py` use a separate SQLite checkpoint
  store (`~/.local/share/linux-ricing/sessions.sqlite`) and their session dirs are named by
  LangGraph thread IDs (e.g. `rice-20260428-1234-abc123`). The Pre-flight check in `SKILL.md`
  therefore never surfaces an in-progress LangGraph session to the user.
  **Fix applied:** `_query_workflow_sessions()` calls `workflow/run.py --list` as a subprocess
  and merges the results into `resume-check` output (each entry gains a `"source"` field:
  `"agent"` or `"workflow"`). New `workflow-run [THREAD_ID]` command added. `SKILL.md`
  Pre-flight updated to handle both source types and offer mode selection.

- [x] **[DOC] `manifest.json` `structure.workflow/` says `"verifiers/"` — should be `"validators.py"`**
  The description for the `workflow/` key in `manifest.json:36` lists `"verifiers/"` as a
  subdirectory, but the actual file is `workflow/validators.py` (a flat module, not a package).
  No `verifiers/` directory exists. Cosmetic doc error only — no runtime impact.

- [x] **[DOC] `manifest.json` `requirements.workflow_packages` missing `langchain-openai`**
  `workflow/config.py:get_llm()` imports `langchain_openai.ChatOpenAI` for any non-Anthropic-native
  provider. `workflow/requirements.txt` correctly includes `langchain-openai>=0.3.0`, but
  `manifest.json:42-46` (`workflow_packages` list) omits it. A user following the manifest to
  install deps would miss this package and get an `ImportError` on non-Anthropic providers.

---

### KDE Element Validation — from Auggie review 2026-04-27

Full plan: `dev/kde-validation-plan.md`


########### claude --resume b2cb686a-7c16-4107-8ae2-fef93b595a69





#### Bugs to fix

- [x] **[BUG] materialize_kvantum fallback writes "kvantum-dark" as Kvantum theme name**
  `ricer.py ~L1368`: when design has no `kvantum_theme` key, falls back to the string
  `"kvantum-dark"` as the Kvantum theme name (not a valid installed theme — Kvantum silently
  ignores it). `widgetStyle` is correctly set to `"kvantum"` separately, so the
  silent-Breeze-fallback bug doesn't trigger, but the kvantum.kvconfig is left pointing at
  a nonexistent theme. **Fix:** early-return empty list when `kvantum_theme` is absent.

- [x] **[BUG] kde_lockscreen `break` fires before checking if kreadconfig returned a value**
  `ricer.py ~L1571`: the `break` is inside the `cmd_exists` block but outside the `if rc == 0 and out`
  check. If kreadconfig6 is installed but the key is unset (empty output), kreadconfig5 is never tried.
  Inconsistent with `snapshot_kde_state` pattern which only breaks when a value is found.
  Low practical risk on Plasma 6 (kreadconfig6 is always present and always responds), but should
  be made consistent for correctness.

- [x] **[GAP] `icon_theme` is schema-required for KDE but has no materializer**
  `DEFAULT_DESIGN_SYSTEM` and all presets declare `icon_theme`. `discover_apps()` does NOT register
  an `icon_theme` key. `APP_MATERIALIZERS` has no `icon_theme` entry. Silent no-op — users setting
  this field get nothing.
  **Fix options:** (A) implement `materialize_icon_theme` via `kwriteconfig6 --file kdeglobals --group Icons --key Theme <name>` + KWin reconfigure; (B) explicitly document as SKIP in Quality Bar §11.

- [ ] **[FEATURE][DEFERRED] Generative icon theme via fal.ai style transfer**
  When no suitable installed theme matches the palette, offer to generate a customized icon
  set by style-transferring the palette colors onto a base icon pack (e.g. Papirus) using
  fal.ai image-gen tools. Would live as a new stage in the implement/ pipeline: enumerate
  installed → if best match score is low → call fal.ai with palette + base icons → write
  generated icons to `~/.local/share/icons/<theme-name>/`. Out of scope for the selection
  flow; tracked here for future implementation.

#### Tests to write

- [x] **tests/test_kde_materializers.py** — no dedicated unit tests exist for:
  - `materialize_kde` (colorscheme): decimal RGB check, plasma-apply-colorscheme call, BreezeClassic bounce, kdeglobals backup ordering
  - `materialize_kvantum`: widgetStyle="kvantum" regression guard, fallback behavior, qdbus reconfigure call order, kvconfig-only backup
  - `snapshot_kde_state`: all 7 fields, LookAndFeelPackage fallback, missing kvantum.kvconfig, wallpaper_plugin capture
  - `materialize_cursor`: kcminputrc write, plasma-apply-cursortheme call, skip when no cursor_theme, previous value capture
  - `materialize_plasma_theme`: plasmarc group+key correctness, plasma-apply-desktoptheme call, skip when absent, backup is plasmarc not kdeglobals
  - `materialize_konsole`: colorscheme file location, required sections present, default profile update
  - `discover_apps`: all 4 KDE sub-systems (kvantum, plasma_theme, cursor, kde_lockscreen) registered when KDE detected, absent when not

- [x] **tests/test_kde_undo.py** — no unit tests for KDE-specific undo restore paths:
  - previous colorscheme re-applied via plasma-apply-colorscheme
  - widgetStyle restored via `--delete` not empty string
  - cursor theme restored via plasma-apply-cursortheme
  - plasma theme restored
  - lock screen theme restored
  - manifest marked `undone: True` after success

#### Skill doc to update

- [x] **skills/ricer-kde/SKILL.md** `discover_apps` block is missing `kde_lockscreen`
  The "always ensure this block exists" example shows only 3 keys (kvantum, plasma_theme, cursor).
  Real code at `ricer.py ~L159` registers a 4th: `kde_lockscreen`. Update the example.

---


## ✅ DONE (2026-04-24)

- **`scripts/session_manager.py`** — built and wired into SKILL.md §2. All 9 step directives now invoke real commands. Tested end-to-end: init → append-step 1–8 → rename → append-item → complete → resume-check.
- **`QUICKSTART.md` rewrite** — replaced old single-prompt command reference with 8-step session overview, Seven Stances table, animated wallpaper teaser, and honest prerequisites.
- **§15 Supported Targets** — replaced flat bullet list with annotated table (✅ full / ⚠ partial / 🔲 no doc) for all WMs and apps. No more silent undocumented entries.
- **`shared/wallpaper-generation.md`** — added full Animated Wallpaper Pipeline section at top (FAL + Seedance, 4 variants, cron scheduling, fallback). Static content preserved below.
- **Template `hermes-ricer` → `linux-ricing`** — fixed comment headers in all 13 templates.
- **5 new guide docs** — `shared/polybar.md`, `shared/wofi.md`, `shared/mako.md`, `shared/swaync.md`, `shared/picom.md`. §13 index + §15 coverage table updated (5 apps promoted from ⚠ partial → ✅ full).
- **wezterm + foot deep-dives** added to `shared/terminal.md`. Both promoted to ✅ full in §15. Total ⚠ partial now just: feh/nitrogen.
- **`manifest.json`** — written for skill packaging at `linux-ricing/manifest.json`.
- **Prose quality review (Claude Code)** — 12 issues found and fixed:
  - `Hyprland/setup.md`: fixed rofi-wayland note (AUR, not Arch repos), `otf-firamono-nerd` → `ttf-firacode-nerd`, added `cliphist` to package list, split AUR packages to `yay` line, fastfetch `.json` → `.jsonc`, `pkill plasmashell` → `|| true` guard.
  - `KDE/setup.md`: `plasma-desktop kwriteconfig6 kreadconfig6` → `plasma-desktop kconfig`.
  - `KDE/colorscheme.md`: `inactiveForeground` contrast bug fixed (dark brown → readable gray `98,102,114`).
  - `Hyprland/hyprlock.md`: all `rgba(r, g, b, a)` decimal → `rgba(rrggbbaa)` hex format + pitfall callout added.
  - `shared/rollback.md`: void-dragon preset dict missing `icon_theme` — added. Icon/cursor theme verify commands added.

---

## Live KDE Integration Test — Findings (2026-04-24)

End-to-end test on KDE Plasma 6 / Wayland: `ricer apply --wallpaper X --extract` → `ricer undo`. Baseline at `~/.cache/linux-ricing/baselines/20260424_030101_*`. All code-level findings from that run are below. Color extractor itself worked deterministically and round-trips cleanly. The bugs are downstream in the materializer/undo layer.

### [BUG P0 — FIXED 2026-04-24] `materialize_wallpaper` doesn't register undo info → `ricer undo` leaves the test wallpaper in place

- `scripts/ricer.py:1572-1678` (`materialize_wallpaper`) calls `plasma-apply-wallpaperimage` (and the Hypr/feh/swww variants) but does NOT snapshot the pre-apply wallpaper path. Manifest change entry has no `previous_wallpaper` field.
- `scripts/ricer.py:2316+` (`undo()`) has no `app == "wallpaper"` branch. It silently skips wallpaper restoration.
- Verified live: after apply + undo, `~/.config/plasma-org.kde.plasma.desktop-appletsrc` still points at the test wallpaper.
- Note: `scripts/deterministic_ricing_session.py:309-326` handles wallpaper snapshot manually (reads `Image=` from appletsrc before apply, appends a `previous_wallpaper` change entry with `manual: True`). That logic should move into `materialize_wallpaper` so plain `ricer apply` gets it too.
- **Fix applied:** new helper `_snapshot_current_wallpaper(desktop)` covers KDE (appletsrc regex), awww (`--get last-image`), hyprpaper (conf parse), swww (`swww query`), feh (`~/.fehbg`). Every branch of `materialize_wallpaper` now records `previous_wallpaper`. New `app == "wallpaper"` branch in `undo()` dispatches by `method`. Reproducer `test_p0_wallpaper_restored_on_undo` goes green.

### [BUG P1 — FIXED 2026-04-24] `materialize_plasma_theme` and `materialize_cursor` silently no-op on extractor output

- Extractor JSON has `palette`, `name`, `description`, `mood_tags` only. No `plasma_theme` / `cursor_theme` / `icon_theme` / `gtk_theme` keys.
- `scripts/ricer.py:1474-1475` (plasma_theme): `if not plasma_theme: return changes` — silent skip.
- `scripts/ricer.py:1528-1529` (cursor): `if not cursor_theme: return changes` — silent skip.
- Contrast: `materialize_kvantum:1402-1405` defaults to `"kvantum-dark"` and `materialize_gtk:2046-2048` defaults to `Adwaita-dark/Papirus-Dark/default` — inconsistent contract.
- Result: on `ricer apply --extract`, Plasma panel chrome and cursor stay on whatever was previously set — no visible update for those layers. The skill's 10-layer promise silently collapses to 8.
- **Fix (pick one):**
  - (a) **Extractor emits defaults**: `palette_extractor.extract_palette` appends `plasma_theme: "default"`, `cursor_theme: "breeze_cursors"`, `icon_theme: "Papirus-Dark"/"Papirus"` (by YIQ of bg), `gtk_theme: "Adwaita-dark"/"Adwaita"`, `kvantum_theme: "kvantum-dark"/"kvantum"`. Keeps materializer contracts strict.
  - (b) **Materializers default in-place**: `materialize_plasma_theme` and `materialize_cursor` pick sensible defaults from palette when keys are missing (mirror `materialize_gtk` / `materialize_kvantum`). Keeps design JSON minimal.
  - (a) is cleaner — the design_system JSON is the canonical description, and it should be complete.
- **Fix applied:** `palette_extractor._default_theme_names()` now emits `kvantum_theme`, `cursor_theme`, `icon_theme`, `gtk_theme`, `plasma_theme` defaults based on YIQ luma of `palette["background"]`. Reproducer `test_p1_extract_apply_covers_plasma_theme_and_cursor` goes green; manifests now contain entries for plasma_theme + cursor materializers.

### [BUG P2 — FIXED 2026-04-24] Kvantum's kdeglobals backup is the *only* kdeglobals backup (and it's stale)

- Reproducer `test_p2_kvantum_backs_up_kdeglobals_before_kde_mutates_it` revealed that `materialize_kde` doesn't actually back up kdeglobals to a file — it snapshots the *current colorscheme name* via `snapshot_kde_state()` so undo re-applies the old colorscheme via `plasma-apply-colorscheme`, which rewrites kdeglobals from scratch.
- That's why `kvantum/kdeglobals` is the only kdeglobals backup in the manifest, and it's stale (post-kde-write).
- Today this works because `plasma-apply-colorscheme` is idempotent and reliably re-writes kdeglobals. But it's fragile: if `plasma-apply-colorscheme` fails, the previous colorscheme file is missing, or a user's kdeglobals has hand-edited sections outside `[Colors:*]`, undo leaves kdeglobals partially corrupted.
- **Fix applied:** `materialize_kde` now backs up kdeglobals pre-apply as `kde/kdeglobals` (change entry field `kdeglobals_backup`). `materialize_kvantum` no longer re-captures kdeglobals (kvantum's only contribution is the widgetStyle key, already recorded via `previous_widget_style`). `undo()` generic loop adds `kdeglobals_backup` → `~/.config/kdeglobals` restoration as a file-level fallback. Reproducer `test_p2_kdeglobals_backed_up_once_and_matches_pre_apply` goes green.

### [MINOR P3 — FIXED 2026-04-24] Baseline audit misses `fastfetch/config.json`

- Reproducer `test_p3a_desktop_state_audit_covers_gtk_and_fastfetch` showed: `fastfetch/config.json` is NOT captured by `desktop_state_audit.py`. GTK settings.ini IS captured but under a flattened name (`gtk-3.0-settings`, not `settings.ini`) — test refined to check for that.
- Means baseline-vs-post-undo fidelity checks can't verify fastfetch config rolled back.
- **Fix applied:** added `gtk-4.0-settings`, `fastfetch.config.json`, `dunstrc`, `rofi.config.rasi`, `waybar.style.css` to `desktop_state_audit.py:backup_all_config_files`. Reproducer now checks labels (not filename leaves) and covers every file whose source exists.

### [NON-BUG] DeprecationWarning claim from initial test was a false alarm

- `scripts/ricer.py:193` does call `datetime.utcnow()` which is deprecated in Python 3.12+.
- But Python emits the warning to **stderr**, not stdout. Pipelines like `ricer extract | jq` work fine as long as stderr isn't merged in with `2>&1`.
- Still worth cleaning up (`datetime.now(timezone.utc)`) but NOT a pipe-breaking bug.
- Reproducer `test_p3b_ricer_stdout_is_clean_json` confirms this — currently passes.

### Successes from this run

- Color extractor: 10 slots filled, contrast-correct, deterministic across two runs (byte-identical stdout). Round-trips through `apply --extract --dry-run` → `apply --extract` → `undo` cleanly for all files except wallpaper.
- `materialize_kde`, `materialize_kvantum`, `materialize_gtk`, `materialize_konsole`, `materialize_kitty`, `materialize_rofi`, `materialize_dunst`, `materialize_fastfetch`, `materialize_waybar` all wrote+backed up+reloaded without errors.
- Post-undo fidelity: `kdeglobals`, `kvantum.kvconfig`, `plasmarc`, `kcminputrc` byte-identical to baseline.

---

## Color Extractor (image → 10-key palette)

Goal: close the gap between documented capability ("Image/Wallpaper → Extract dominant colors → Apply everywhere") and real code. Currently the extractor exists only as pseudo-code in `ricer/ricer-wallpaper/SKILL.md:358-396`; nothing in `scripts/ricer.py` imports PIL, colorthief, or any clustering library.

### Findings from review

- [x] `ricer-wallpaper/SKILL.md:394` — `danger <- rotate_hue(Vibrant, 0)` no-op: fixed. Real extractor finds nearest-hue swatch.
- [x] No fallback cascade: implemented in `palette_extractor.py` for all 6 swatch classes.
- [x] No palette-level collision detection: `validate_palette()` enforces uniqueness + contrast.
- [x] `setup.sh` Pillow vs colorthief mismatch: resolved — Pillow-only implementation, no colorthief.
- [x] No alpha handling: `load_and_normalize()` alpha-composites over `#808080` before quantization.
- [x] Determinism guarantee: swatches sorted by `(-frequency, hex_string)` — documented in module.

### What to build

- [x] Create `scripts/palette_extractor.py` — complete: `load_and_normalize`, `quantize_swatches`, `_classify_swatch`, `assign_slots`, `validate_palette`, `infer_mood_tags`, `extract_palette`, `_default_theme_names`.
- [x] Wire to CLI: `ricer extract --image PATH [--out FILE] [--name NAME]` — done.
- [x] `ricer apply --extract` flag — done; derives design_system in-memory from wallpaper.
- [x] Docs alignment: SKILL.md updated with real CLI commands.

### Tests

- [x] `tests/test_palette_extractor.py` — complete. Covers: determinism, 10-slot completeness, contrast, uniqueness, semantic hue, classify thresholds, dark_scenic accent capture.
- [x] Fixtures: synthesized in-memory (no committed binaries) — vibrant, monochrome, dark_scenic.

### End-to-end verification (reversible, on KDE sandbox)

```bash
# Unit tests
python3 -m pytest tests/test_palette_extractor.py -v

# Extract-only — no desktop change
ricer extract --image ~/Pictures/maplestory_bg.png

# Extract + dry-run apply — no desktop change
ricer apply --wallpaper ~/Pictures/maplestory_bg.png --extract --dry-run

# Real apply (reversible)
ricer apply --wallpaper ~/Pictures/maplestory_bg.png --extract
ricer status
# visual check: colorscheme, konsole, kvantum, panel
ricer undo
ricer status
```

Pass criteria: tests green, extraction deterministic on rerun, apply+undo round-trip leaves kdeglobals/kvantum/wallpaper/konsole byte-identical to pre-apply.

### Reused utilities (already in `scripts/ricer.py`)

- `hex_to_rgb_tuple`, `rgb_tuple_to_hex` — line 347-356
- `yiq_text_color` — line 358 (contrast validation)
- `rotate_hue` — line 371 (fallback hue derivation)
- `adjust_lightness` — line 384 (contrast + fallback lightness)
- `simple_render` — line 401 (Jinja2-compatible fallback renderer)

### Out of scope

- Vision-subagent extraction (semantic image understanding beyond clustering) — roadmap.
- OKLab / Lch perceptual color spaces — revisit if extractor quality proves insufficient.
- WCAG AAA contrast — AA-equivalent (YIQ Δ ≥ 128) is sufficient for theming.
- Text-prompt → palette via LLM — separate subskill.
