# Widget Next-Step Gate

Use this reference when resuming widget/dashboard pipeline work after Quickshell v0.3.0 type-doc ingestion.

## Session lesson

The pipeline now has a local Quickshell source of truth under `references/quickshell-v0.3.0-types/` and codegen/research can inject those docs into prompts. That is necessary but not sufficient: schema-correct QML is still only a prerequisite. The next class-level gate is proving one component-mode sandbox artifact through visual and functional validation before defining live promotion/rollback manifests.

## Required next sequence

1. `component-model-synthesis`
   - Consume normalized widget contracts, visual states, action/data bindings, texture intent, and the ingested framework docs.
   - Emit a framework-neutral component tree (`HudRoot`, `PanelFrame`, `GameButton`, `WorkspaceSlot`, `ClockLabel`, `StatusMeter`, `PowerGlyph`, menus/tooltips) with typed roles, layout constraints, state machines, and asset slots.
   - Do not promote screenshot crops, `preview_texture`, or flat Rectangle placeholders as final components.

2. `quickshell-component-codegen`
   - Use `references/quickshell-v0.3.0-types/index.json` / `summary.md` as the source of truth for QML types/properties/imports.
   - Generate sandbox-local Quickshell QML with `PanelWindow` for shell chrome, explicit input handlers, hover/pressed/active visual states, native bindings such as `Timer`/date formatting for clocks, and sandbox-relative assets.
   - Record artifact path and SHA-256 in the sandbox manifest.

3. `same-artifact-validation`
   - Run static validation, bounded launch, screenshot/localization, visual-loss scoring, game-feel scoring, contract-function validation, artifact-function validation, and manual review against the same generated artifact path/hash.
   - Review output must include target crop, rendered crop, diff, hitbox/interaction overlay, component tree summary, function report, and hard failure reasons.

4. `feature-flagged-craft-integration`
   - Only after the sandbox same-artifact gate is green, wire the widget DAG into `craft_node()` behind a feature flag.
   - Integration should still write only under the sandbox/session output root until the later promotion milestone.

5. `promotion-manifest-design` deferred
   - Add live promotion/rollback manifests only after the same-artifact sandbox gate is proven.
   - The later manifest must be dry-run-first, list source artifact hashes, destination paths, backups/restores, restart/liveness checks, and final live screenshot/function gates.

## Hard stop conditions

Stop before live writes if any of these are true:

- validation is visual-only or function-only rather than same-artifact;
- artifact is `preview_texture`, copied crops, or a surrogate/demo not used in runtime review;
- Quickshell generation was not grounded in the local v0.3.0 docs snapshot;
- non-decorative controls lack bounded hitboxes, hover/pressed states, or honest action/data bindings;
- runtime screenshot/localization is skipped but the report claims visual success;
- sandbox output root or managed files can escape via symlinks;
- process groups are not cleaned up after bounded launch.

## Related references

- `references/quickshell-v0.3.0-types/summary.md`
- `references/widget-dag-task-breakdown.md`
- `references/widget-pipeline-quickshell-sandbox-milestone.md`
- `references/widget-same-artifact-semantic-gate.md`
- `references/widget-runtime-validation-hardening.md`
