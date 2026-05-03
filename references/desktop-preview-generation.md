# Desktop Preview Generation Pitfalls

Use this when troubleshooting Step 2.5 (`visualize`) or Step 4 (`plan`) preview quality.

## Session signal

The user rejected a Step 2.5 preview because it behaved like a mood-board/reference-image workflow instead of an AI preview of the entire desktop theme. The old prompt asked for a cinematic environment and explicitly said `no UI chrome`; the generated image therefore showed atmosphere rather than desktop windows, panels, widgets, menu borders, or icon language.

## Root cause pattern

If the preview looks like a landscape, shrine, room, wallpaper, or generic concept-art image rather than a desktop screenshot/concept:

1. Inspect `workflow/nodes/visualize.py` first.
2. Check the FAL prompt builder for anti-UI language such as:
   - `no UI chrome`
   - `environment`
   - `cinematic atmospheric digital painting`
   - `landscape`
   - instructions that omit windows/panels/widgets/launchers/icons.
3. Check `PREVIEW_SYSTEM_PROMPT`; it must not reduce the preview to a hero image plus a tiny terminal/panel mockup.
4. Check `workflow/nodes/refine.py`; approved visual context must seed both palette and UI/chrome decisions, not palette alone.

## Required Step 2.5 intent

Step 2.5 should be grounded in concrete visual references before generation. Those
references are not wallpapers. They are evidence for visual grammar: border thickness,
menu hierarchy, surface materials, icon silhouettes, ornament density, lighting, and
how game UI elements sit in space. The generated image should synthesize a new desktop
shell from those references; it must not paste or reinterpret a reference image as the
background wallpaper unless the user explicitly selected that image as wallpaper.

Step 2.5 should generate one full-desktop AI theme concept image before structured design refinement. The image is the primary creative artifact — a hero overview that the HTML preview frames rather than competes with. It should depict:

- wallpaper/background treatment
- window chrome and borders
- terminal window
- launcher/menu panel
- top/bottom system panel
- widgets or widget menus when the brief asks for them
- icon language / glyph silhouettes
- application surface materials
- theme-specific ornamentation such as thorns, carved frames, runes, bronze, ember glow, etc.

For RPG/game-menu briefs, explicitly ask for ornate window borders, thorn-like menu frames, rune/glyph button silhouettes, layered panels, readable UI labels, terminal/menu/panel text affordances, and high-contrast readable regions. Do not ban readable text: a desktop preview needs labels and terminal/menu affordances to read as an operating system. Avoid copied proprietary logos/trademarks, but allow original glyph marks and icon emblems.

## Prompt invariant

A healthy FAL prompt includes language like:

```text
Full Linux desktop theme concept preview ... Generate one single representative overview image: a complete desktop screenshot-style overview that becomes the centerpiece of the design system ... Fill the canvas edge-to-edge with the desktop overview; no cinematic letterbox bars, no black bands above or below, no framed movie-still presentation ... Show the entire desktop UI as a coherent screenshot-style mockup: ornate window borders, themed terminal window, launcher/menu panel, top or bottom system panel, widget menus, icon style, wallpaper background, and custom application chrome all designed as one unified theme ... no default desktop chrome, not a landscape-only painting.
```

And must NOT include:

```text
no UI chrome
landscape-only
environment only
mood painting only
```

## Bridge/status pitfall: preserve the approval target

When using the bridge script, a no-answer status check must be read-only if `pending_messages` is already non-empty. Do not call `graph.stream(None)` at an approval interrupt. At Step 2.5 this can re-enter `visualize` before the node's return values have been checkpointed; older code then saw no `visualize_image_url`, ran a second FAL generation, and replaced the preview the user was trying to approve.

Bridge template invariant:

```python
state = graph.get_state(config)
pending = pending_interrupts(state)

if answer is None and pending:
    print(json.dumps(session_status(state), indent=2, default=str))
    sys.exit(0)

if answer is not None and not pending:
    # refuse unsafe resume
```

Workflow invariant: `workflow/nodes/visualize.py` persists the pre-interrupt preview identity to `visualize.pending.json` in the session directory (`image_url`, `html_path`, `visual_context`) before interrupting. If accidental re-entry happens anyway, the node must load that cache and reuse the same preview instead of calling FAL again. Clear the cache only on explicit `back`, `regenerate`, or free-form feedback that intentionally requests a new preview.

Regression test pattern: add/keep tests in `tests/test_visualize_preview_prompt.py` proving `_save_pending_preview()` + `_load_pending_preview()` preserve the image URL and visual context across re-entry, and ignore malformed cache files.

## Nano Banana / HTML Hero Regression Pattern

When previews become bland after previously working with Nano Banana, check for these
specific regressions before tuning prompts:

- Step 2.5 model drifted from `fal-ai/nano-banana` to a different text-to-image endpoint
  such as `fal-ai/flux/dev`.
- The FAL argument schema still contains legacy Flux controls (`guidance_scale`,
  `num_inference_steps`, `image_size`) instead of Nano Banana's `aspect_ratio`,
  `safety_tolerance`, and `limit_generations`.
- The generated Step 2.5 image is approved, but `plan_node` does not pass
  `state["visual_context"]` / `reference_image_url` into `_render_preview`, causing
  `plan.html` to invent a separate generic style guide.
- Prompts demote the image to a decoration instead of saying it is the hero centerpiece
  and creative source of truth.

Corrective invariant: Nano Banana owns the full-desktop overview. HTML frames it and
adds palette/terminal implementation views; it must not replace the generated image.

## Internal DesktopPreviewPipeline

Step 2.5 uses `workflow/preview_pipeline/` for the paid AI preview flow:

- `prompts.py` owns desktop-overview prompt invariants and LLM prompt text.
- `providers.py` owns the `fal-ai/nano-banana` call schema.
- `budget.py` records paid generation estimates and blocks over-budget flows.
- `cache.py` owns `visualize.pending.json` and `preview_pipeline.history.jsonl`.
- `validators.py` owns deterministic prompt/context contract checks.
- `executor.py` coordinates the pipeline and returns `PreviewRunResult`.
- `templates.py` describes the default DAG and future opt-in variants.

`workflow/nodes/visualize.py` remains the LangGraph approval gate. It should not reimplement pipeline internals.

## Variant generation policy

Variant generation is supported only as an explicit opt-in pipeline. The default Step 2.5 flow runs one paid `fal-ai/nano-banana` hero generation. A variant pipeline may create 2-4 paid concept images, but must show/record a budget estimate first and must not run because of ambiguous approval text such as "looks good, but...".

## Verification

Run focused tests after changing preview logic:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python -m pytest tests/test_preview_pipeline_budget.py tests/test_preview_pipeline_cache.py tests/test_preview_pipeline_executor.py tests/test_preview_pipeline_validators.py -q
python -m pytest tests/test_visualize_preview_prompt.py tests/test_refine_prompt_handoff.py tests/test_preview_renderer.py tests/test_resume_control.py -q
```

Expected evidence from the regression test should prove that the FAL prompt contains `entire desktop UI`, `screenshot-style mockup`, `ornate window borders`, `themed terminal window`, `launcher/menu panel`, `widget menus`, `icon style`, `representative overview image`, `edge-to-edge`, `no cinematic letterbox bars`, and does not contain `no UI chrome`. The generation call should use `fal-ai/nano-banana` with `aspect_ratio="16:9"` and loose `safety_tolerance="6"`, not legacy Flux parameters such as `guidance_scale` / `num_inference_steps`.
