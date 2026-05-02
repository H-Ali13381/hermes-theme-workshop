# KDE Design JSON Validator Contract

Source: `workflow/validators.py` — `design_complete()` + `_kde_creativity_complete()`
Last verified: 2026-05-01 (ember-vigil session)

## Required top-level keys

BASE (all recipes):
  - name
  - description
  - palette
  - mood_tags

KDE-specific additions:
  - kvantum_theme
  - plasma_theme
  - cursor_theme
  - icon_theme
  - gtk_theme
  - originality_strategy
  - chrome_strategy

## Palette slots (all 10 required, all must be 7-char hex "#rrggbb")

  background, foreground, primary, secondary, accent,
  surface, muted, danger, success, warning

## originality_strategy (dict)

Required sub-fields:
  - vision_alignment: non-empty string
  - non_default_moves: list of >= 3 items

Banned words anywhere in non_default_moves text (case-insensitive):
  "default", "stock", "breeze", "standard", "unchanged", "normal", "generic"

## chrome_strategy (dict)

Required sub-fields:
  - method: non-empty string (e.g. "aurorae+kvantum+eww")
  - implementation_targets: non-empty list (e.g. ["aurorae", "kvantum", "eww", "kitty"])

Optional (good to include but not validated):
  rounded_corners, custom_titlebars, terminal_frames, panel_chrome,
  ornamental_borders, implementation_notes

## panel_layout (optional dict)

If present, text of all values must not contain banned words:
  "default", "stock", "breeze", "standard", "unchanged", "normal", "generic"

## widget_layout (optional list of dicts)

If present, each widget dict MUST contain all four of:
  - name
  - position
  - data        <-- NOTE: NOT "data_source" — the LLM commonly uses the wrong key
  - visual      <-- NOTE: NOT "visual_metaphor" — same issue

## Common LLM mistakes that cause validator failure

1. chrome_strategy missing "method" and/or "implementation_targets"
   → LLM writes narrative fields but omits the two machine-checked ones

2. widget_layout items use "data_source" + "visual_metaphor" instead of "data" + "visual"
   → Always include both the correct keys AND the narrative keys if you want both

3. originality_strategy.non_default_moves contains "default" (e.g. "set to default Plasma panel")
   → Rephrase: "transparent floating bar" not "default panel with transparency"

4. palette has 9 slots (missing one of the 10)
   → Double-check all 10 are present before calling the validator

## Quick validation snippet

```python
import sys, json
from pathlib import Path
sys.path.insert(0, '/home/neos/.hermes/skills/creative/linux-ricing')
from workflow.validators import design_complete

design = json.loads(Path('/home/neos/.config/rice-sessions/<thread>/design.json').read_text())
ok, reason = design_complete(design, {'desktop_recipe': 'kde'})
print(f'ok={ok}, reason={reason!r}')
```
