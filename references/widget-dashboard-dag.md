# Widget / Dashboard DAG for linux-ricing

Use this reference when improving Step 6 custom widgets/dashboard work (`widgets:quickshell`, `widgets:eww`, future `widgets:ags` / `widgets:fabric`). The goal is to replace the current monolithic craft path with a nested DAG that can decompose, build, validate, and promote widgets safely. For the fully expanded node-by-node dependency graph and adapter boundary contract, read `references/widget-dag-task-breakdown.md` next.

## Problem

Current `workflow/nodes/craft/__init__.py::craft_node()` does research → LLM codegen → write files → heuristic score. `_score_details()` mainly checks required file presence and palette coverage. This can produce high scores for widgets that are syntactically present but visually wrong: flat gray boxes, titlebar windows, fake controls, wrong placement, or drift from the Step 2.5/Step 4 visual contract.

## External research signal

Reddit discussion (`r/archlinux`: “What widget system do you use? eww, ags, fabric, or quickshell?”) suggests:

- AGS: often recommended as a practical JS/TS + GTK middle ground with decent performance and ecosystem.
- EWW: many examples/community, but custom language, performance concerns, and slower development.
- Quickshell: promising Qt/QML shell system; newer and docs/examples can be sparse, but especially relevant for KDE/Wayland.
- Fabric/Ignis: attractive to Python users, but smaller ecosystem/documentation.
- Replacing Waybar/Rofi/Dunst is only worth the complexity when integration/customization needs justify it.

Workflow implication: choose frameworks by desktop profile and validation capability, not popularity. KDE Wayland should still prefer Quickshell; EWW/AGS/Fabric should be adapters behind one common widget pipeline.

## Core architecture correction: build game UI components, not screenshot overlays

The widget pipeline must treat Quickshell, EWW, AGS, and Fabric as target runtimes for a game-UI-like component system. A good desktop dashboard is not a cropped preview image with invisible hitboxes. It is a tree of typed controls, assets, state machines, layout constraints, data bindings, and callbacks.

Required mental model:

- **Component tree:** HUD root, panel, button, slot, orb, meter, label, popup/menu, tooltip, confirmation dialog, decorative frame.
- **Control state machine:** default, hover, pressed, active/selected, disabled, focused, opening/closing where relevant.
- **State-specific assets:** 9-slice panel/button/slot frames, icon layers, glow layers, pressed/inset variants, meter fills, masks, shadows, and quiet content fills.
- **Input model:** hit test, pointer enter/leave, pointer down/up, click, click-away dismissal, destructive confirmation, safe command dispatch.
- **Data model:** system time, KWin workspace state, battery/CPU/RAM/network, notifications, media/session state, each with explicit update cadence and stale/error display.
- **Runtime adapter:** Quickshell QML, EWW Yuck/SCSS, AGS JS/TS, or Fabric Python/CSS are codegen targets for the same component contract. They are not separate design philosophies and must not redefine success.

`--preview-texture` is a deliberate cheating upper-bound renderer. It may copy target crops into sandbox-local images to prove screenshot localization, crop mapping, asset containment, and score plumbing. It must be labelled as a plumbing test, **never** a product-quality widget, and **never eligible for live promotion**. Promotion requires component-mode artifacts built from typed controls and validated assets.

## Proposed nested DAG

The outer LangGraph can still treat `widgets:*` as one queued Step 6 element, but internally run:

1. Widget intake
2. Preview source resolution
3. UI element segmentation
4. Control segmentation
5. Element contract normalization
6. Semantic action/data binding
7. Visual state specification
8. Component model synthesis
9. Texture intent extraction
10. Asset bundle generation
11. Asset bundle validation
12. Framework selection
13. Sandbox scaffolding
14. Per-component codegen
15. Static validation
16. Sandbox runtime launch
17. Screenshot capture
18. Visual loss + game-feel scoring
19. Functional validation
20. Interaction replay
21. Integration composition
22. Promotion eligibility gate
23. Desktop promotion
24. Live desktop screenshot + final gate
25. Craft log + manifest

Represent retries as new attempt records (`attempt_001`, `attempt_002`) rather than hidden graph cycles mutating the same state. This preserves acyclic reasoning, debugging, and rollback.

## Dry-run process validation harness

Add `scripts/widget_pipeline_sample.py` so implementers can validate the pipeline spine without running a full rice workflow or touching the live desktop. The canonical fixture is:

`/home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png`

Verified properties: `1376x768`, RGB PNG. It is a Maplestory-like fantasy HUD strip with a full ornate panel, workspace buttons, central clock, CPU/RAM bars, power button, decorative leaves, parchment texture, and border/strap ornaments.

The harness should:

1. Load the image as a local preview source.
2. Require `--dry-run`; Milestone 1 must not offer an implicit live mode.
3. Seed deterministic sample contracts/fixture bboxes.
4. Write crops for `full_hud`, `workspace_group`, `clock`, `status_bars`, and `power_button`.
5. Run contract normalization, texture intent extraction, asset generation/validation, fake or minimal adapter rendering, visual scoring, and function validation where modules exist.
6. Emit `report.json`, `report.md`, crops, comparison images, and asset/contact-sheet artifacts under `--out`.
7. Exit non-zero on hard process failures while marking live-only stages as explicit `SKIP`, not pass.
8. Never write to live config directories.
9. Treat output path safety as part of the dry-run contract: reject a symlinked `--out` root, reject symlinked managed subdirectories such as `crops/` or `reports/`, resolve/validate managed paths under the output root, and route every contract/artifact id through a filename-safe helper before interpolating it into a path.

Canonical commands:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
# Milestone 1: deterministic fake renderer + visual scoring
python scripts/widget_pipeline_sample.py --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png --out /tmp/widget-pipeline-sample-maplestory --framework quickshell --dry-run
# Milestone 2: Quickshell sandbox codegen, no runtime launch/promotion
python scripts/widget_pipeline_sample.py --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png --out /tmp/widget-pipeline-sample-maplestory --framework quickshell --renderer quickshell --no-launch --dry-run
# Milestone 3 target: bounded Quickshell launch + screenshot + real visual scoring
# Exact CLI may change during implementation, but it must still write only under --out.
python scripts/widget_pipeline_sample.py --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png --out /tmp/widget-pipeline-sample-maplestory-runtime --framework quickshell --renderer quickshell --dry-run
```

This harness is the pre-flight proof that node interfaces, crop/artifact production, visual-score plumbing, asset validation, sandbox codegen, and report generation work before attempting Step 6 in a real session.

## Milestone 1 implementation lessons

The first dry-run harness established a useful safety baseline for future widget DAG work:

- Keep Milestone 1 dry-run only. The CLI should fail unless `--dry-run` is supplied; live launch/promotion belongs to later milestones with explicit rollback support.
- Use deterministic fake rendering and image comparisons first. It is enough to prove contracts, artifacts, renderer plumbing, visual scorecards, and reports before integrating real Quickshell/EWW/AGS/Fabric runtimes.
- Return a failing `StageResult` for missing target/rendered crops or image IO errors instead of crashing halfway through report generation. A failed visual stage is debuggable; a partial dry-run is not.
- Path escape bugs are high-severity in a sandbox harness. Reject symlinked output roots/subdirectories and sanitize artifact ids before composing filenames. Add tests that pre-create `out/crops -> /escape` and confirm no files are written outside `--out`.
- Verification should include both tests and a real fixture replay, then check live config paths such as `~/.config/quickshell`, `~/.config/eww`, `~/.config/ags`, and `~/.config/fabric` were not created or modified.

## Milestone 2 implementation lessons

The Quickshell sandbox phase deliberately proves code generation without claiming live visual success. The detailed adapter contract and replay checklist live in `references/widget-pipeline-quickshell-sandbox-milestone.md`. Same-artifact semantic validation details and the regression replay command live in `references/widget-same-artifact-semantic-gate.md`.

- Generate `sandbox/quickshell/shell.qml` and `sandbox/quickshell/manifest.json` under the caller-provided `--out` directory only.
- Use `PanelWindow` for every shell surface. Static validation rejects `FloatingWindow`, KDE-inappropriate `hyprctl`, and live config path references.
- Copy validated texture assets into `sandbox/quickshell/assets/` and reference sandbox-relative asset paths from QML.
- Keep runtime launch conservative. `--no-launch` reports `runtime-launch: SKIP`; missing Quickshell or deferred bounded-launch support must also be explicit `SKIP`, never fake `PASS`.
- Keep screenshot/visual scoring conservative. Generated QML does not equal visual validation; screenshot capture remains `SKIP` until a safe window-target capture path exists.

## Milestone 3 implementation lessons

The first runtime-validation path keeps the same sandbox-only contract while adding bounded launch/capture/scoring:

- `--renderer quickshell` without `--no-launch` attempts a bounded sandbox launch only when `quickshell` and a graphical session are available; otherwise it reports explicit `SKIP` reasons.
- Runtime logs are written to `sandbox/quickshell/runtime.log`; screenshots go to `screenshots/quickshell-sandbox.png`; real cropped render artifacts go to `rendered-real/`; comparisons and review HTML stay under `comparisons/` and `reports/`.
- Screenshot capture currently supports `spectacle` first and `grim` second. Blank/flat/transparent screenshots are hard failures, not weak passes.
- Runtime cleanup terminates the launched process group, not just the parent process, so forked sandbox children do not outlive the bounded run.
- Fixed sandbox artifact paths reject pre-existing symlink files, and copied texture assets must resolve under the caller-provided `--out` root.
- Real visual scoring runs only after screenshot capture succeeds. Generated QML alone still reports `visual-score: SKIP`.
- The review page at `reports/visual-review.html` shows target crop, real Quickshell render, diff, and score for each contract.
- Runtime crop localization should prefer baseline-vs-post-launch screenshot diffing over guessed screen coordinates. Record the detected `runtime_surface_bbox` and compositor scale factors, then map framework-local widget bboxes into screenshot pixels before scoring. This avoids false visual failures when Quickshell places a `PanelWindow` on a scaled or multi-monitor KDE surface.
- Keep a deliberate `--preview-texture` upper-bound renderer for Quickshell runtime validation. It copies each segmented target crop into sandbox-local `Image` textures, positions them with preview-relative geometry, launches the same bounded screenshot path, and should score near-perfect. This is intentionally "cheating" and must be labelled as such; it proves screenshot localization, crop mapping, asset containment, and scoring plumbing before real widget reconstruction/codegen is blamed for visual loss. It is barred from promotion: a near-perfect preview-texture score proves the harness, not the widget. Product candidates must use component mode with typed controls, state machines, real assets, data bindings, and framework-native callbacks.
- Preview-texture mode is only useful if segmentation selected real UI pixels. Do not assume the approved preview's widgets live in a fixed bottom strip: first detect the foreground UI cluster against the border/background color, map fixture-relative widget slots into that detected bbox, and label the report `detected preview UI cluster`. If the target crop contact sheet is mostly uniform gray/empty background, the visual score is meaningless even if it passes; fix segmentation before judging renderer/codegen.
- Dynamic widgets need semantic validation separate from visual matching. A clock contract that only looks like `12:00` is not functional; it must carry `data_source: system_time`, `update_interval_ms`, and `format`, and the generated framework code must contain a native timer/date binding. Static clock text without the binding is a hard validation failure, even if the crop visually resembles the preview.
- Visual and functional validation must target the same generated QML artifact. Do not validate a copied preview-texture widget for visual similarity and then launch a separate component-mode widget for functionality; that proves two different things about two different widgets. Preview-texture mode may still be an upper-bound renderer, but when a contract declares dynamic semantics it must layer functional bindings/hitboxes over the copied texture crops in the same `shell.qml` (for example `Timer`/`new Date()`/`Qt.formatDateTime(...)` over the clock crop). The harness now emits an explicit `artifact-function-validation` stage with the QML path and SHA-256; this stage is the identity gate proving semantic bindings/hitboxes are present in the same artifact that visual/runtime review uses. Contract-level `function-validation` can still be `SKIP` for missing real commands, even when `artifact-function-validation` passes hitbox/binding presence. When the user asks to manually test the widget on screen, launch the current sandbox artifact being validated, verify `quickshell` and a graphical session are available, verify the process remains running, and capture/inspect a screenshot so claims about visibility are grounded.

## Milestone 4 craft_node integration lessons

Integrate the widget pipeline into `workflow/nodes/craft/__init__.py::craft_node()` behind a feature flag only after the bounded runtime harness is green and a component-mode sandbox artifact has passed both visual and functional gates. Do not jump straight from runtime plumbing to live promotion/rollback work: first prove that the same generated artifact path + SHA-256 passes static validation, screenshot-localized visual scoring, game-feel scoring, contract-function validation, artifact-function validation, and manual review. The craft path should consume the same `WidgetElementContract` / `WidgetAttemptResult` records as the harness instead of inventing a second scoring model.

Milestone 4 gate sequence:

1. Detect eligible widget elements from the Step 6 element queue (`widgets:quickshell` first) and approved visual contract.
2. Build normalized contracts, including semantic data fields for clocks/status meters, action declarations for buttons, and explicit per-control `action_regions`/hitboxes derived from the segmented crop.
3. Resolve non-decorative actions to real, safe desktop behavior before rendering. On KDE fixtures, workspace slots may use `qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop N`, but functional validation must first prove `/VirtualDesktopManager count >= N`; otherwise the command is a no-op and the action is `SKIP`/`FAIL`, not `PASS`. A power/menu glyph must toggle a custom in-artifact power menu or confirmation surface. Do not use `qdbus6 org.kde.krunner /App org.kde.krunner.App.query power`: it opens a search bar and fails the power-menu UX contract. `console.log(...)` alone is decorative/unbound.
4. Run the sandbox pipeline under a session artifact root, never under live config paths.
5. Require static, runtime, visual, contract-level functional, action-geometry, and same-artifact semantic scorecards to be explicit `PASS` / `FAIL` / `SKIP`; do not collapse them into the old file/palette craft score.
6. Feed failed visual/function/action-geometry results back into retry/codegen attempts as new attempt records, preserving DAG traceability.
7. Return to the legacy craft path when the feature flag is off or the desktop/framework is unsupported, but log that widget-DAG validation was skipped.
8. Do not promote live desktop widgets until Milestone 5 adds rollback-owned promotion manifests. Milestone 5 is deliberately blocked until a component-mode sandbox artifact has passed visual/function/game-feel review as the same artifact; `preview_texture`, visual-only surrogates, and function-only surrogates must never be promoted.

A craft integration is not complete if it merely calls Quickshell codegen and reports a high craft score. It must preserve the harness's safety invariants: output-root containment, process-group cleanup, runtime screenshot evidence, crop-level visual scoring, clock/data-binding checks, and honest skipped/failed stages.

## Core data contracts

`WidgetElementContract` should include stable id, role, priority, source image, bbox, crop path, anchor/dimensions, visual traits, palette tokens, text expectations, live data binding metadata (`data_source`, `update_interval_ms`, `format`), actions, hard requirements, and non-goals. Each `WidgetAction` should carry the low-level interaction contract: legacy shell `command` or safer `command_argv`, `decorative`, optional per-control `action_region`/hitbox (`x`, `y`, `width`, `height`), `visual_states` (`default`, `hover`, `pressed`, plus optional `focus`, `active/checked`, `disabled`), `preconditions`, and `expected_effect`. Action regions are still treated as part of the element-level contract for scoring, but the current code stores the concrete generated hitbox metadata on each `WidgetAction` so the same QML artifact can be checked against the exact control.

`WidgetAttemptResult` should include attempt id, contract id, framework, sandbox root, generated files, generated artifact hashes, target crop, rendered crop, static/visual/functional/action-geometry scorecards, same-artifact semantic validation result, pass status, and feedback for the next codegen attempt.

## Texture / asset compiler

Ornate widgets need a first-class asset sub-DAG. The pipeline must not ask Quickshell, EWW, AGS, or Fabric to fake carved/thorned/worn-metal borders with flat rectangles. When a contract requires textured chrome, run an asset compiler before framework codegen.

Inputs: normalized widget contract, target crop, palette, `chrome_strategy`, Step 2.5 hero image, and Step 4 plan screenshot.

Outputs:

- `TextureIntent` describing material, border thickness, variants, palette, forbidden traits, and generator policy.
- `TextureBundle` with `panel_ornate_9slice.png`, `button_ornate_9slice.png`, `slot_ornate_9slice.png`, optional `plaque_ornate_9slice.png`, metadata JSON, and `asset_contact_sheet.png`.
- Framework prompt context containing sandbox-relative paths, slice sizes, intended component names, and validation scores.

Generation policy: deterministic local generation is the default. Hybrid or paid AI generation may only provide material guidance/fill behind the normal cost gate; deterministic masks and metadata should preserve 9-slice/tile correctness. Existing `workflow/nodes/craft/texture_assets.py` is the current low-level helper and should be wrapped or extended by `workflow/widget_pipeline/asset_compiler.py` when the nested widget pipeline lands.

Validation must check seam loss, alpha/slice correctness, distinct corners, quiet/readable centers, scale contact sheets, and a hard rejection for flat placeholder rectangles. If ornate assets are required and no validated bundle exists, widget codegen is blocked unless the user explicitly accepts the deviation.

Separate targets clearly:

- `widget_frame_assets`: Quickshell/EWW/AGS/Fabric menu, panel, button, slot, and plaque borders.
- `app_surface_assets`: app-level skins such as terminal/background surfaces.
- `window_decoration_assets`: KDE/Aurorae/KDecoration/Kvantum-style real app/window borders, which need separate materializers and should not be implied by widget frame success.

## Framework policy

- KDE Wayland: default Quickshell; require `PanelWindow` for shell chrome. EWW only if explicitly requested or Quickshell is unavailable.
- Hyprland: default Quickshell; AGS may be viable for GTK-like dashboards if explicitly requested; EWW fallback for small static widgets.
- GNOME: do not pretend shell-level widgets are safe unless a supported extension path exists; AGS/Fabric may run as app windows but must be labelled honestly.
- X11/unknown: EWW fallback first.
- Fabric: optional Python adapter, not default until docs/examples/tests are stronger.

## Visual validation

Compare target crop vs rendered crop using a conservative first pass:

- geometry: bbox size ratio, anchor/margin, silhouette/edge density
- palette: dominant color distance and required token presence
- texture/material: edge/ornament density, local contrast, tiled/border image presence
- text/layout: expected text/section count; OCR optional
- perceptual: SSIM-like grayscale comparison; optional CLIP/vision later
- vision critique: optional multimodal LLM asks for concrete deviations

Initial thresholds:

- critical widget: total >= 8 and no hard violations
- normal widget: total >= 7.5 or user accepted deviation
- decorative widget: total >= 7 if functionality is not promised

Hard violations:

- normal app titlebar appears for shell widget
- large flat gray rectangles dominate where textured/ornate material was required
- visible button has no action and is not labelled decorative
- wrong monitor/edge or not visible
- blank/transparent output for non-empty target

## Functional validation

Every promised control needs either a working target or an honest decorative label. Validate command existence, prefer argv-safe bindings (`command_argv`) when a command can be expressed without shell parsing, qdbus/KDE targets, no Hyprland commands on KDE, no obsolete KDE5 commands unless verified, interaction declarations, data command behavior, and sane polling intervals. Validate action preconditions and expected effects: a KDE workspace button targeting desktop `N` is not functional unless `/VirtualDesktopManager count >= N`, and the validation report must show the before/after state or explicitly mark the action skipped. Validate interaction geometry as a first-class contract: broad `anchors.fill: parent` over a multi-control crop is a failure for action groups, overlapping `MouseArea`s are a failure unless intentionally layered, and cursor-change zones must align with the visible control pixels. Workspace groups need one bounded hitbox per slot/action; circular/power controls need centered bounded hitboxes rather than a whole decorative crop. Validate interaction feel as a first-class scorecard: every clickable control needs visible hover and pressed feedback in the same rendered artifact (`containsMouse`/`:hover`, `containsPress`/`:active`, `TapHandler.pressed`, or framework equivalent). Flat transparent overlays that only change the cursor fail the game-menu UX contract. Clock/time widgets are not visually complete if they render a static preview label such as `12:00`; they need `data_source: system_time`, a sane `update_interval_ms`, a framework-native timer/date binding, and separate semantic validation from visual crop matching. The functional DAG is two-layered: `function-validation` checks the normalized contract is honest about missing/real commands and data sources; `artifact-function-validation` checks that the generated framework file being rendered/scored contains the corresponding bindings or hitboxes in that same artifact, identified by path and SHA-256. A `MouseArea` that only logs to the console is decorative/unbound and must not pass functional validation unless the action is explicitly marked decorative. A power glyph that opens KRunner search for `power` is not a power menu; it must toggle a custom menu/confirmation surface or be marked incomplete.

## Suggested module layout

```text
scripts/
  widget_pipeline_sample.py

workflow/widget_pipeline/
  __init__.py
  models.py
  pipeline.py
  preview_sources.py
  segmentation.py
  contract_normalizer.py
  asset_compiler.py
  asset_score.py
  framework_selection.py
  sandbox.py
  codegen.py
  static_validate.py
  runtime.py
  screenshot.py
  visual_score.py
  function_validate.py
  compose.py
  promote.py
  sample_fixtures.py
  prompts/
    segment_widgets.md
    generate_widget.md
    visual_feedback.md
    generate_texture_assets.md
  adapters/
    __init__.py
    base.py
    quickshell.py
    eww.py
    ags.py
    fabric.py
```

## Milestone 1

Keep the first implementation narrow: “KDE Wayland Quickshell visual-validation pipeline for one widget surface.”

Scope: Quickshell only; one contract/surface only; fixed sample replay harness before live workflow execution; deterministic segmentation from `visual_element_plan` only; first-class validated asset bundle for ornate frames when required; static validation + sandbox screenshot + basic visual score + command validation; feature flag off by default except tests.

Definition of done for the full class: KDE Wayland `widgets:quickshell` no longer relies only on file/palette scoring; dashboards decompose into named contracts; ornate widgets receive validated 9-slice/tiled frame assets before codegen; one widget can be sandboxed, rendered, scored, function-checked, and promoted; low scores produce retry feedback; promotion is reversible; handoff reports real/decorative/deviation controls honestly; non-widget Step 6 elements remain unchanged.
