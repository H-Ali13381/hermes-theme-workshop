# KDE Implementation Verification Lessons

Session: Bonfire Blackiron / `rice-20260503-1016-90bf95` (2026-05-03)

Use this when Step 6 implementation gates fail below 8/10 even though apply reports OK. The recurring class of bug is disagreement between the LLM-generated spec, materializer-written paths, verifier palette detection, and score semantics.

## Core diagnosis pattern

1. Read the Step 6 gate literally: element, score, category breakdown, `files_missing`, and `files_written`.
2. Compare the spec targets with what the materializer actually writes.
3. If apply succeeded but verification is low, suspect verifier/materializer/spec mismatch before assuming the desktop visual output is bad.
4. Patch the workflow at the class boundary, add regression tests, rerun targeted pytest, then retry the element through the bridge.
5. Do not accept a low score merely to progress when the root cause is a workflow bug; foreman mode authorizes patch-and-continue.

## Specific fixes validated in this session

### Palette should be verified across the written file set
Some elements distribute palette evidence across multiple files. A verifier that requires every palette color in every file creates false failures.

Correct behavior:
- collect readable file contents for all written file targets
- skip directories
- verify palette presence across the combined content set

### Accept KDE decimal RGB triplets as palette evidence
KDE `.colors` files store colors as decimal triplets, for example `17,21,19`, not only `#111513`. Palette verification must accept both HEX and `r,g,b` forms.

### Score must not ignore unresolved missing targets
A spec with unresolved `files_missing` should not score 8+ simply because one expected file exists. Score shape/diegesis/usability should penalize missing targets unless the target is a directory that was intentionally created and should be treated differently.

### Add fallback targets for materializer conventions
Common spec/materializer naming mismatches:
- `terminal:kitty`: spec may target `~/.config/kitty/<theme>.conf`; materializer writes `~/.config/kitty/theme.conf` and includes it from `kitty.conf`.
- `launcher:rofi`: spec may target `~/.config/rofi/themes/<theme>.rasi`; materializer writes `~/.config/rofi/hermes-theme.rasi`.
- `icon_theme`: design may name `<theme>` while generator activates `<theme>-icons`; verifier should consider both and inspect SVG contents for palette evidence.
- `window_decorations:kde`: materializer convention is `~/.local/share/color-schemes/hermes-<theme-slug>.colors` plus KWin/KDE config writes.

### Generate custom Kvantum packages for custom palette-backed themes
Do not restrict custom Kvantum generation to names beginning with `hermes-`. If the named theme does not already exist and the design supplies a palette, generate the package (`.kvconfig`, `.svg`, metadata as appropriate) and then select it.

### Do not hallucinate Aurorae window-decoration packages
Current KDE materializers support KDE color scheme / KWin / Breeze decoration settings, not full Aurorae engine package generation. Step 6 specs for `window_decorations:kde` must not target:

`~/.local/share/aurorae/themes/<Theme>/`

unless a dedicated Aurorae materializer exists. Otherwise verification will correctly report a missing target even though the supported implementation path is complete.

## Tests to add or run

Targeted suites from this session:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python -m pytest tests/test_implement_spec.py tests/test_kde_materializers.py -q
```

Regression coverage should include:
- palette matching across a multi-file written set
- directories in `files_written` / `files_missing` not being read as files
- decimal RGB triplet palette matching
- fallback paths for kitty/rofi/icon/window decoration conventions
- Kvantum generation for non-`hermes-` custom names
- spec prompt rule forbidding Aurorae targets without materializer support

## Elements improved in the session

After workflow patches and retries:
- `plasma_theme`: 10/10
- `cursor_theme`: 10/10
- `icon_theme`: 8/10
- `kvantum_theme`: 8/10
- `window_decorations:kde`: 10/10

The next unresolved gate at compaction was `lock_screen:kde` at 5/10; apply the same spec/materializer/verifier mismatch diagnosis before accepting or skipping.
