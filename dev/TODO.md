# linux-ricing TODO

## Open Issues

- **`sudo` in install step needs Hermes propagation** — `install_packages()` in `workflow/nodes/install/resolver.py` runs `sudo pacman` and `yay` as bare subprocesses. Hermes has a mechanism to propagate sudo auth requests back to the user through the chat. The install step should use that mechanism instead of running `sudo` directly, so the user gets an authentication prompt in the chat when packages need to be installed.

- **KDE lock screen materializer missing** — `lock_screen:kde` is queued for KDE users (`detectors.py:137`) but `scripts/ricer.py` has no KDE lock screen entry in `APP_MATERIALIZERS`. Need to add `materialize_kde_lockscreen()` that applies a theme to kscreenlocker (via `kwriteconfig6` or a color scheme file). Register in `APP_MATERIALIZERS` at `scripts/ricer.py:2278`.

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
