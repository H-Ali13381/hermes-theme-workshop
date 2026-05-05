# Quickshell Ornate Tileable Borders

This document records the current Quickshell widget-chrome failure mode and the process we need to bake into the linux-ricing workflow.

## Why this exists

The bonfire-blackiron Quickshell pass initially failed because the implementation confused three different things:

1. **Presence**: QML contains labels such as `QUEST WIDGET BOARD`, `INVENTORY RUNES`, or `REST BELT`.
2. **Surface correctness**: shell chrome uses `PanelWindow` instead of `FloatingWindow` so KDE/Wayland does not decorate it like a normal app window.
3. **Ornate visual craft**: panels/buttons/slots use actual carved/tiled border construction that reads like RPG menu chrome.

The first two are necessary but not sufficient. The user explicitly wants Diablo II / Dark Souls / blackiron menu language: thin thorned forged borders, inventory-slot framing, worn metal, soot, parchment, ember focus, and in-world widget menus. Plain `Rectangle { border.color: ... }` boxes are not ornate, even when labelled correctly and palette-matched.

## Current live stopgap

The live shell was patched to use QtQuick `BorderImage` assets:

- `/home/neos/.config/quickshell/assets/panel_ornate_9slice.png`
- `/home/neos/.config/quickshell/assets/button_ornate_9slice.png`
- `/home/neos/.config/quickshell/assets/slot_ornate_9slice.png`

The QML uses `BorderImage` with slice values and repeat tile modes. That correctly proves the technique: Quickshell can render 9-slice/tiled frame construction for panels/buttons/slots.

However, the current texture assets were procedurally sketched with PIL during debugging. They are not good enough as final art. They are too crude, too noisy, too synthetic, and too much like placeholder MMO chrome. The code path must learn to generate or source better tileable textures, validate them, and only then wire them into Quickshell.

## Correct target

For an ornate Quickshell RPG widget/menu implementation, the workflow should produce:

- A tileable horizontal edge texture.
- A tileable vertical edge texture, or a 9-slice atlas where vertical edges tile cleanly.
- Four distinct corner pieces that do not smear when scaled.
- A center/inset texture or transparent fill strategy that leaves content readable.
- Separate variants for:
  - large panel frames,
  - launcher/menu buttons,
  - inventory/rune slots,
  - optional header plaques.
- Metadata describing slice sizes, intended QML component names, and visual prompt/source.

Preferred output shape:

```text
~/.config/quickshell/assets/<theme>/
  panel_9slice.png
  button_9slice.png
  slot_9slice.png
  plaque_9slice.png
  border_metadata.json
```

The workflow-owned version should write into the generated framework config output first, then the materializer/craft application should copy to the active Quickshell config directory.

## Visual quality requirements

A generated texture is acceptable only if it satisfies all of these:

- Corners are visually distinct from edges.
- Edge segments tile without obvious seams.
- Border thickness is thin enough to avoid bulky terminal cages.
- The result reads as forged/thorned/carved/worn material, not flat orange triangles.
- Interior content remains readable at desktop scale.
- Texture does not introduce copyrighted/logo-specific Diablo assets.
- Texture is not just a palette recolor of a rectangle.
- Screenshot verification confirms it is visible in the live shell.

## Candidate subprocess: texture generation + validation

Add a subprocess before Quickshell QML generation when the design asks for ornate/tiled/RPG chrome:

1. **Texture intent extraction**
   - Input: `design.json`, `visual_context`, `chrome_strategy`, `visual_element_plan`.
   - Output: `TextureIntent` with material, mood, palette, asset variants, border thickness, and forbidden traits.

2. **Asset generation**
   - Default no-cost path: deterministic local generator creates a conservative high-quality base using PIL/SVG primitives, Perlin/noise, bevels, erosion masks, and seamless tile wrapping.
   - Optional paid path: FAL/image model creates a 9-slice UI border atlas only when cost gate allows and user approval exists.
   - Reference-assisted path: if real UI reference images exist, crop/derive motif guidance but do not copy proprietary assets.

3. **Tileability validation**
   - Compare opposite edge strips for seam distance.
   - Validate alpha margins and slice dimensions.
   - Ensure corners differ from edges.
   - Ensure center area is not visually noisy.
   - Produce a contact-sheet preview for human/vision inspection.

4. **QML asset injection**
   - Generate reusable QML components:
     - `OrnatePanelFrame`
     - `OrnateButtonFrame`
     - `OrnateSlotFrame`
     - `HeaderPlaque`
   - Components use `BorderImage`, declared slice metadata, repeat tile modes, and palette-compatible content overlays.

5. **Live verification**
   - Restart Quickshell.
   - Capture screenshot.
   - Vision-check for tiled border visibility and readability.
   - Reject if it reads as basic rectangles, synthetic placeholder art, or noisy/bulky frames.

## Codebase integration points

Likely files/modules:

- Create `workflow/nodes/craft/texture_assets.py`
  - Owns texture intent extraction, deterministic texture generation, atlas writing, metadata writing, and validation helpers.

- Modify `workflow/nodes/craft/codegen.py`
  - Before building/generating Quickshell files, determine if ornate texture assets are required.
  - Inject generated asset metadata into the LLM prompt.
  - Extend `evaluate_files()` so `BorderImage` is not enough; referenced assets and metadata must exist in the output file set or generated asset bundle.

- Modify `workflow/nodes/craft/frameworks.py`
  - Add syntax guidance and an example of `BorderImage` 9-slice frame components.
  - Avoid encouraging plain rectangles for ornate designs.

- Modify `workflow/nodes/craft/__init__.py`
  - Ensure generated asset files are written alongside QML outputs.
  - Include assets in craft logs and handoff.

- Add tests in `tests/test_craft_node.py` or a new `tests/test_texture_assets.py`
  - Reject ornate Quickshell configs with only rectangle borders.
  - Reject `BorderImage` QML that references missing asset files.
  - Accept valid generated 9-slice assets with metadata.
  - Validate seam-score helper catches non-tileable edges.

## Lessons from this session

- `PanelWindow` solved decorated-window drift but did not solve visual quality.
- `BorderImage` solved the plain-rectangle mechanism but not texture quality.
- Procedural placeholder assets can pass static checks and still look bad.
- The workflow needs a dedicated asset subprocess, not ad-hoc PIL snippets inside a live debug session.
- The final gate must be visual: screenshot + explicit question: “Do these buttons/panels look ornate, or are they still cheap dashboard boxes?”

## Immediate next step

Implement the plan in `.hermes/plans/2026-05-03-quickshell-tileable-texture-subprocess.md` task by task. Do not treat the current assets as final. They are scaffolding only.
