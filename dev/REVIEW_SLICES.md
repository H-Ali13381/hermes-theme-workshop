# Review Slices for Current Working Tree

This working tree contains several independent changes. Review and commit them
as separate slices so failures can be bisected and reverted without taking down
unrelated workflow areas.

Run the full suite after all slices are applied:

```bash
.venv/bin/python -m pytest
```

## Slice 1: Runtime Configuration and Resume Controls

Purpose: make model/env resolution and CLI resume/list behavior deterministic.

Files:

```bash
git add requirements.txt workflow/config.py workflow/run.py \
  tests/test_env_secret_resolution.py tests/test_llm_config_resolution.py \
  tests/test_resume_control.py references/workflow-bridge-script.md \
  references/workflow-environment-issues.md references/workflow-llm-errors.md
```

Focused checks:

```bash
.venv/bin/python -m pytest \
  tests/test_env_secret_resolution.py \
  tests/test_llm_config_resolution.py \
  tests/test_resume_control.py
```

Review notes:
- Confirm secrets are never logged.
- Confirm `--answer` refuses to resume when there is no pending interrupt.
- Confirm completed sessions do not appear as resumable.

## Slice 2: Step 2.5 Desktop Preview Pipeline

Purpose: introduce AI desktop concept preview generation, analysis, caching,
budget tracking, routing, and deterministic fallback rendering.

Files:

```bash
git add workflow/graph.py workflow/routing.py workflow/nodes/__init__.py \
  workflow/nodes/audit/__init__.py workflow/nodes/audit/detectors.py \
  workflow/nodes/visualize.py workflow/nodes/preview_renderer.py \
  workflow/preview_pipeline \
  tests/test_visualize_preview_prompt.py tests/test_preview_renderer.py \
  tests/test_preview_pipeline_budget.py tests/test_preview_pipeline_cache.py \
  tests/test_preview_pipeline_executor.py tests/test_preview_pipeline_validators.py \
  references/visual-contract-pipeline.md references/reference-grounded-desktop-overviews.md \
  references/visualize-approval-state-pitfalls.md
```

Focused checks:

```bash
.venv/bin/python -m pytest \
  tests/test_visualize_preview_prompt.py \
  tests/test_preview_renderer.py \
  tests/test_preview_pipeline_budget.py \
  tests/test_preview_pipeline_cache.py \
  tests/test_preview_pipeline_executor.py \
  tests/test_preview_pipeline_validators.py \
  tests/test_workflow_audit.py
```

Review notes:
- Confirm cache reuse cannot trigger duplicate paid generations.
- Confirm budget history is cumulative per session.
- Confirm prompt contract targets a full desktop UI, not environment art.

## Slice 3: Plan/Refine Feedback and Preview Honesty

Purpose: carry approved visual context through refine/plan and block misleading
Step 4 previews.

Files:

```bash
git add workflow/nodes/refine.py workflow/nodes/plan.py \
  tests/test_refine_prompt_handoff.py tests/test_plan_feedback_routing.py \
  tests/test_plan_preview_contract.py references/preview-plan-implementation-alignment.md
```

Focused checks:

```bash
.venv/bin/python -m pytest \
  tests/test_refine_prompt_handoff.py \
  tests/test_plan_feedback_routing.py \
  tests/test_plan_preview_contract.py
```

Review notes:
- Confirm plan feedback routes to render/refine/explore as intended.
- Confirm contract violation pages cannot be approved.
- Confirm rounded chrome is allowed only when the design declares an
  implementable method.

## Slice 4: Craft Pipeline and Quickshell Texture Assets

Purpose: make generated widget code more reliable, add evaluator retries, and
support deterministic 9-slice texture assets for ornate Quickshell chrome.

Files:

```bash
git add workflow/nodes/craft/__init__.py workflow/nodes/craft/codegen.py \
  workflow/nodes/craft/frameworks.py workflow/nodes/craft/texture_assets.py \
  tests/test_craft_node.py tests/test_texture_assets.py \
  references/quickshell-kde-shell-chrome.md \
  references/quickshell-ornate-tileable-borders.md \
  .hermes/plans/2026-05-03-quickshell-tileable-texture-subprocess.md
```

Focused checks:

```bash
.venv/bin/python -m pytest tests/test_craft_node.py tests/test_texture_assets.py
```

Review notes:
- Confirm Pillow is lazy-loaded and only required on texture generation paths.
- Confirm Quickshell generated code is rejected for unsupported `IconImage`,
  `FloatingWindow` shell chrome, undeclared texture paths, and flat ornate
  interiors.
- Confirm EWW fallback skipping only happens when Quickshell has already passed.

## Slice 5: KDE Materialization, Finalization, and Undo

Purpose: improve KDE-generated themes, post-implementation finalization, and
rollback determinism.

Files:

```bash
git add scripts/materializers/kde_extras.py scripts/ricer_undo.py \
  workflow/nodes/cleanup/__init__.py workflow/nodes/cleanup/kde_finalize.py \
  tests/kde_test_helpers.py tests/test_kde_materializers.py \
  tests/test_kde_undo.py tests/test_kde_finalization.py tests/test_kde_finalize.py \
  references/kde-post-implementation.md \
  references/kde-implementation-verification-lessons.md \
  references/cost-control-and-rollback-lessons.md
```

Focused checks:

```bash
.venv/bin/python -m pytest \
  tests/test_kde_materializers.py \
  tests/test_kde_undo.py \
  tests/test_kde_finalization.py \
  tests/test_kde_finalize.py
```

Review notes:
- Confirm tests isolate HOME/config writes through `tests/kde_test_helpers.py`.
- Confirm `visualize_image_url` is never applied as wallpaper.
- Confirm cursor rollback remains success when live KDE restore succeeds and
  temp HOME writes are isolated.
- Confirm generated Kvantum/Plasma themes do not overwrite system themes.

## Slice 6: Implement/Install Verification Hardening

Purpose: improve spec/apply/verify scoring, package install confirmation, and
post-apply diagnostics.

Files:

```bash
git add workflow/nodes/implement/__init__.py workflow/nodes/implement/spec.py \
  workflow/nodes/implement/verify.py workflow/nodes/implement/score.py \
  workflow/nodes/install/__init__.py workflow/nodes/install/resolver.py \
  workflow/nodes/handoff.py tests/test_implement_spec.py \
  tests/test_install_resolver.py tests/test_improvement_safety.py \
  tests/test_cleanup_reloader.py tests/test_visual_artifacts.py
```

Focused checks:

```bash
.venv/bin/python -m pytest \
  tests/test_implement_spec.py \
  tests/test_install_resolver.py \
  tests/test_improvement_safety.py \
  tests/test_cleanup_reloader.py \
  tests/test_visual_artifacts.py
```

Review notes:
- Confirm fallback target resolution does not hide genuinely missing files.
- Confirm install failures are rechecked against final package state.
- Confirm scoring penalizes missing files and syntax issues.

## Slice 7: Explore UX and Creative-Diversity Notes

Purpose: refine creative intake behavior and capture follow-up design research.

Files:

```bash
git add workflow/nodes/explore.py tests/test_explore_fast_flow.py \
  tests/test_explore_revise_stage.py dev/TODO.md \
  references/autonomous-foreman-mode.md references/bonfire-hollow-session-lessons.md \
  references/diablo-rpg-menu-brief.md references/handling-user-timeout.md \
  references/workflow-debugging-lessons.md
```

Focused checks:

```bash
.venv/bin/python -m pytest \
  tests/test_explore_fast_flow.py \
  tests/test_explore_revise_stage.py
```

Review notes:
- Confirm the test now documents the current six-line brief.
- Confirm new creative-diversity backlog entries are actionable and not mixed
  with completed runtime work.

## Slice 8: Skill Metadata and Documentation Refresh

Purpose: update skill docs, manifest metadata, gitignore entries, and general
reference notes that support the workflow changes.

Files:

```bash
git add .gitignore SKILL.md manifest.json dev/REVIEW_SLICES.md \
  references/wallpaper-sourcing.md references/workflow-bridge-script.md
```

Focused checks:

```bash
.venv/bin/python -m pytest tests/test_workflow_logging.py
```

Review notes:
- Keep documentation-only changes separate from behavior changes unless the
  docs are required to explain a new public contract.
- Confirm manifest version/metadata changes match the behavioral slices being
  published.

