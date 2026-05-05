# Widget DAG Task Breakdown

Use this reference when expanding or executing the linux-ricing custom widget/dashboard pipeline for Quickshell, EWW, AGS, or Fabric. It captures the class-level lesson from the widget pain point: widget work must be decomposed into artifact-producing submodules with explicit dependencies and gates, not handled as one broad craft/codegen step.

## Core rule

A custom dashboard is a DAG of contracts, artifacts, validations, and promotion steps. Retry by creating a new attempt record that depends on previous feedback; do not hide cycles by mutating the same artifact in place. Visual validation, functional validation, and manual review must all name the same generated artifact path and hash.

## Detailed DAG

Each node should write a small, inspectable artifact under the session/sandbox output root.

1. `preview-source`
   - Inputs: approved Step 2.5 hero image, Step 4 plan screenshot/HTML, visual element plan.
   - Outputs: resolved source image paths, source dimensions, target desktop profile.
   - Gate: source exists and is the user-approved visual contract, not an unrelated mockup.

2. `ui-cluster-detection`
   - Inputs: source image.
   - Outputs: foreground/dashboard cluster bbox, confidence, diagnostic overlay.
   - Gate: cluster contains actual UI pixels. Do not assume a fixed bottom strip.

3. `element-segmentation`
   - Inputs: cluster bbox, visual element plan, optional masks/edge detection.
   - Outputs: per-element bboxes/crops/contact sheet for panel, workspace group, clock, meters, power glyph, menus, decorative frames.
   - Gate: target crops are not mostly empty background; report `detected preview UI cluster` when auto-localized.

4. `control-segmentation`
   - Inputs: per-element crops.
   - Outputs: one visual bbox and one interactive bbox per clickable control; overlap report; debug overlay.
   - Gate: workspace groups have one bounded hitbox per slot; circular/power controls get centered bounded hitboxes; broad whole-crop hitboxes fail unless intentionally a single control.

5. `contract-normalization`
   - Inputs: segmentation output, design palette, desktop audit, plan semantics.
   - Outputs: `WidgetElementContract` records with role, priority, bbox, crop, palette/material traits, text expectations, data sources, actions, non-goals.
   - Gate: every visible promised control is either non-decorative with a real target or explicitly decorative/unbound.

6. `semantic-action-binding`
   - Inputs: contracts, audited desktop environment, framework policy.
   - Outputs: safe action bindings (`command_argv` preferred), preconditions, expected effects, destructive-action confirmation policy.
   - Gate: KDE workspace actions prove target desktop count; power glyph opens an in-artifact menu/confirmation, never KRunner search; no Hyprland commands on KDE.

7. `visual-state-spec`
   - Inputs: action/control contracts, aesthetic brief.
   - Outputs: default/hover/pressed/focus/disabled visual state requirements.
   - Gate: every clickable non-decorative control has visible hover and pressed feedback; cursor-only feedback fails.

8. `component-model-synthesis`
   - Inputs: normalized contracts, control segmentation, visual states, data/action bindings, texture intent.
   - Outputs: framework-neutral component tree: `HudRoot`, `PanelFrame`, `GameButton`, `WorkspaceSlot`, `ClockLabel`, `StatusMeter`, `PowerGlyph`, `PowerMenu`, `ConfirmAction`, `Tooltip`, decorative layers, and layout constraints.
   - Gate: copied screenshot crops are not accepted as components. Each visible promised control must map to a typed component with state, assets, input behavior, and data/action semantics.

9. `texture-intent-extraction`
   - Inputs: element crops, palette, chrome strategy, aesthetic brief.
   - Outputs: material/border/ornament requirements and forbidden traits.
   - Gate: ornate RPG widgets cannot be represented as flat gray/dark rectangles with only palette changes.

10. `asset-compiler`
   - Inputs: texture intent, palette, target crops.
   - Outputs: sandbox-local 9-slice/tile assets for panels/buttons/slots/plaques, metadata, contact sheet.
   - Gate: seam loss, slice correctness, distinct corners, readable centers, and non-placeholder texture checks pass.

11. `framework-selection`
   - Inputs: desktop profile, user preference, installed tools, contract needs.
   - Outputs: chosen adapter and explicit fallback reason.
   - Gate: KDE Wayland defaults to Quickshell; EWW/AGS/Fabric are adapter choices behind the same contracts, not separate pipelines.

12. `sandbox-scaffold`
   - Inputs: output root, framework, contracts, asset bundle.
   - Outputs: isolated sandbox directory, manifest skeleton.
   - Gate: no live config writes; reject symlinked output roots/subdirs and unsafe artifact ids.

13. `per-component-codegen`
   - Inputs: component model, assets, visual state spec, framework adapter prompt/context.
   - Outputs: generated framework files plus manifest with artifact hashes.
   - Gate: generated code uses sandbox-relative assets and contains declared typed components, state transitions, hitboxes, callbacks, and data bindings in the same artifact.

14. `static-validation`
   - Inputs: generated files.
   - Outputs: lint/static scorecard.
   - Gate: reject unsupported shell surfaces (for example Quickshell `FloatingWindow` for shell chrome), unsafe shell strings, live config paths, obsolete commands, framework syntax errors, preview-crop-as-final-component shortcuts, and fake `internal:*` shell commands.

15. `bounded-runtime-launch`
   - Inputs: sandbox artifact.
   - Outputs: process id/group id, runtime log, exit/cleanup record.
   - Gate: launch only with bounded timeout/process-group cleanup; missing display/framework is `SKIP`, not `PASS`.

16. `screenshot-capture-localization`
   - Inputs: pre-launch baseline screenshot, post-launch screenshot, runtime metadata.
   - Outputs: screenshot path, runtime surface bbox, compositor scale, localized widget crops.
   - Gate: blank/flat/transparent screenshots fail; localize from runtime evidence rather than guessed coordinates.

17. `visual-loss-and-game-feel-scoring`
   - Inputs: target crops, rendered crops, component model, generated artifact.
   - Outputs: per-element visual scorecards, game-feel scorecards, diff/contact sheets.
   - Gate: score geometry, palette, silhouette, texture/material, text/layout, perceptual loss, tactile affordance, state-specific visuals, menu behavior, and hard violations. A copied preview texture may pass plumbing but fails game-feel/product eligibility.

18. `contract-function-validation`
   - Inputs: normalized contracts, audited desktop commands/state.
   - Outputs: `function-validation` report.
   - Gate: contract honesty: real/missing commands, data source availability, preconditions, expected effects, decorative status.

19. `artifact-function-validation`
   - Inputs: same generated artifact used for runtime/visual review.
   - Outputs: artifact path, SHA-256, semantic binding/hitbox report.
   - Gate: clocks contain native time update bindings; buttons contain explicit hitboxes and handlers; hover/pressed states exist in the same file.

20. `interaction-replay`
   - Inputs: running sandbox artifact, action regions.
   - Outputs: optional click/hover replay logs/screenshots; before/after desktop state for safe actions.
   - Gate: only replay safe/non-destructive actions automatically; destructive power actions stop at confirmation surface.

21. `composition`
   - Inputs: accepted per-element attempts.
   - Outputs: composed dashboard shell artifact and manifest.
   - Gate: no overlap regressions, all accepted deviations documented.

22. `promotion-eligibility`
   - Inputs: composed sandbox artifact, manifest, render mode, scorecards.
   - Outputs: eligibility decision and reasons.
   - Gate: reject `preview_texture` artifacts, copied-crop final components, missing component tree, missing state-specific assets, or any failed static/visual/game-feel/function stage.

23. `promotion-plan`
   - Inputs: promotion-eligible composed sandbox artifact, current live config audit.
   - Outputs: copy/install plan, manifest entries, rollback plan.
   - Gate: user/session approval for live writes; dry-run must show exact paths.

24. `desktop-promotion`
   - Inputs: approved promotion plan.
   - Outputs: live config files, running process/service updates, rollback manifest.
   - Gate: writes are manifest-owned and reversible; no unrelated active settings are overwritten.

25. `live-final-validation`
   - Inputs: live desktop screenshot, manifest, contracts.
   - Outputs: final visual/function/action report and handoff excerpt.
   - Gate: live result matches approved preview enough or records explicit accepted deviations.

## Framework adapter boundaries

All adapters implement the same contract layers:

- Quickshell: `PanelWindow`, `PopupWindow`, `MouseArea`/`TapHandler`, argv-style `Quickshell.execDetached`, QML `Timer`/date bindings.
- EWW: `defwindow`, `button`/`eventbox`, SCSS `:hover`/`:active`, explicit geometry separate from content.
- AGS: `Widget.Window`, `Widget.Button`, popup/overlay surfaces, JS/TS state and service bindings.
- Fabric: `WaylandWindow`, `Button`, `EventBox`, CSS hover/focus/active states, Python callbacks.

Adapters are not allowed to redefine success. They must produce the same scorecard classes: static validation, visual-loss scoring, contract-function validation, artifact-function validation, interaction geometry, runtime evidence, and promotion manifest.

## Retry policy

For each failed gate, create `attempt_N+1` with machine-readable feedback:

- segmentation failure → improve cluster/control masks before codegen.
- visual loss failure → pass crop diffs, material/geometry deltas, and target contact sheet to codegen/asset compiler.
- function failure → fix contract binding or mark decorative; do not paper over with console logs.
- artifact-function failure → regenerate the same artifact so bindings/hitboxes/states are in the rendered file.
- runtime failure → fix launch/surface/windowing before visual scoring.

Stop and surface the report when a gate requires user art direction, destructive-action approval, missing framework installation, or live promotion approval.

## Minimum implementation slice

The next useful implementation slice is not full desktop promotion. It is:

1. deterministic preview-source + cluster/element/control segmentation,
2. normalized contracts with `command_argv`, `action_region`, `visual_states`, preconditions, and expected effects,
3. framework-neutral component-model synthesis for the sample HUD (`HudRoot`, `PanelFrame`, `WorkspaceSlot`, `ClockLabel`, `StatusMeter`, `PowerGlyph`, `PowerMenu`),
4. Quickshell component-mode sandbox codegen into one `shell.qml` using typed controls/state machines/assets, not copied preview crops,
5. static validation plus `artifact-function-validation` and promotion-eligibility rejection for `preview_texture`,
6. bounded launch/screenshot/localization when available,
7. visual-loss + game-feel report against target crops,
8. no live writes.

## Next-step gate before promotion manifests

Do not spend the next slice on `desktop-promotion` or rollback manifests. The immediate gate is proving that a component-mode sandbox artifact can satisfy visual and functional review simultaneously:

1. The generated artifact is component-mode, not `preview_texture` and not a copied crop masquerading as a widget.
2. The same artifact path + SHA-256 is used for static validation, bounded runtime launch, screenshot capture/localization, visual-loss scoring, game-feel scoring, contract-function validation, artifact-function validation, and manual review.
3. All non-decorative controls have typed components, bounded hitboxes, hover/pressed states, and real or honestly skipped actions/data sources.
4. The review report includes target crop, rendered crop, diff, interaction geometry overlay, component tree summary, function report, and hard failure reasons.
5. No live config paths are written, symlink escapes are rejected, and runtime process groups are cleaned up.

Only after this gate is green should the DAG add a live promotion/rollback manifest contract. That later manifest should be a dry-run-first install plan with exact source artifact hashes, destination paths, backups/restores, process restart commands, liveness checks, and final live screenshot/function gates. Promotion remains ineligible for `preview_texture`, visual-only, or function-only surrogates.

Only after the sandbox gate is green should `craft_node()` call the widget DAG behind a feature flag, and only after rollback manifests exist should widgets be promoted live.