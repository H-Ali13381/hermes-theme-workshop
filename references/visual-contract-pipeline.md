# Visual Contract Pipeline

Use this reference when Step 2.5 generated an AI desktop overview and the workflow must avoid collapsing into a palette/icon swap.

## Required sequence

1. Generate representative desktop overview
   - Full desktop canvas, not cinematic art, not a mood board.
   - Must show wallpaper/background, panel/widget chrome, launcher/menu, terminal, window borders, icons/menu language.

2. Interpret with vision
   - Multimodal LLM reads the generated image separately from text direction.
   - Output must include `visual_element_plan` and `validation_checklist`, not only palette/mood.

3. Decompose into implementable elements
   Each `visual_element_plan[]` item should contain:
   - `id`
   - `source_visual_description`
   - `desktop_element`
   - `implementation_tool`
   - `fallback_tool`
   - `config_targets`
   - `validation_probe`
   - `acceptable_deviation`

4. Validate the interpretation before implementation
   - Step 4 plan preview must expose the implementation contract.
   - If the concept shows a distinctive toolbar/panel, the plan must name how stock KDE panel behavior will be hidden/replaced.
   - If the concept shows custom widgets, KDE Wayland should prefer `widgets:quickshell`; `widgets:eww` is fallback or explicit override.

5. Plan and queue concrete tools
   - `refine` should carry `visual_element_plan` into `design.json`.
   - Recognized `implementation_tool` values may enter `element_queue`.
   - Unknown free-form tool names stay metadata only; do not poison the queue.

6. Execute element-by-element
   - Each element gets spec → apply/craft → verify → score.
   - Failures stop at the workflow gate; do not hand-edit session state.

7. Evaluate and visually confirm
   - Final handoff should compare live state to `validation_checklist`.
   - Strong next hardening target: add a screenshot/vision confirmation gate that captures the live desktop and scores each `visual_element_plan` item.

## Regression signals

- `visual_context` has palette only, no `visual_element_plan`.
- `plan.html` is a decorative style guide but does not list the implementation contract.
- Preview shows custom toolbar/widgets, but `element_queue` lacks `widgets:quickshell` or an explicit fallback.
- Final result changes colors/icons only while KDE panel/default layout remains the main UX.
- Validation language is vague (`looks nice`) instead of probe-based (`Quickshell toolbar visible; Plasma panel hidden/autohide`).

## Current implementation anchors

- `workflow/nodes/visualize.py`: Step 2.5 multimodal prompt/output schema.
- `workflow/nodes/refine.py`: carries visual contract into design prompt and queue extraction.
- `workflow/nodes/plan.py`: prompts for implementation-contract section in preview.
- `workflow/state.py`: documents `visual_context` as palette + style + `visual_element_plan` + `validation_checklist`.
- Tests: `tests/test_visualize_preview_prompt.py`, `tests/test_refine_prompt_handoff.py`.
