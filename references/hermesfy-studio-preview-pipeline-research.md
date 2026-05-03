# Hermesfy Studio research — desktop preview pipeline lessons

Session context: investigated https://github.com/Shugar03/hermesfy-studio as a possible fix for /linux-ricing desktop image preview generation difficulties.

## Verdict

Hermesfy Studio is useful as an architectural pattern, not a drop-in dependency for linux-ricing yet.

Best reusable ideas:
- Model paid image generation as an explicit DAG rather than one large visualize node.
- Add a per-flow budget gate and record estimated spend in session metadata.
- Treat prompt edits/regeneration as node edits plus downstream re-run, not ad-hoc reruns.
- Persist workflow status/history and generated artifact identity.
- Validate intermediate images before they poison downstream plan/design generation.
- Support explicit user-approved variant generation with cost gates.

Do not directly depend on Hermesfy without hardening:
- It is product/ad-image oriented, not desktop-theming oriented.
- Existing templates target product studio/catalog/portrait/social workflows.
- Its Fal model registry is small and hardcoded despite README claims of 48+ models.
- It expects `FAL_API_KEY`; linux-ricing resolves `FAL_KEY` through Hermes/env/shell paths.
- It does not include `fal-ai/nano-banana`, which current linux-ricing Step 2.5 uses for desktop overview concepts.
- Packaging omits some non-code assets from `pyproject.toml` package-data, e.g. templates/fonts may be missing in non-editable installs.
- Plugin docs/comments are inconsistent: 7/8 tool comments vs 10 registered tools.
- GitHub license metadata was absent although README says MIT.

## Repo components inspected

Key files:
- `src/hermesfy/plugin.py` — Hermes plugin registration; registers toolset `hermesfy` with 10 tools.
- `src/hermesfy/dag/graph.py` — `Workflow`, `Node`, `Edge`, `NodeType`; node types include `text_prompt`, `image_gen`, `img2img`, `upscale`, `seed`, `inpaint`, `outpaint`, `ip_adapter`, `remove_bg`, `face_restore`.
- `src/hermesfy/dag/executor.py` — topological execution, `{{node}}` reference resolution, seed propagation, budget gate, optional intermediate validation.
- `src/hermesfy/providers/fal.py` — raw `queue.fal.run` HTTP wrapper; aliases include `flux-dev`, `flux-pro`, `flux-schnell`, `clarity-upscaler`, `birefnet`, `codeformer`.
- `src/hermesfy/budget_gate.py` — default `$0.07` per-flow cap.
- `src/hermesfy/intermediate_validator.py` — Gemini Vision step validation.
- `src/hermesfy/composition/*` — local PIL composition helpers for text/badges/callouts/lines/buttons/color grading; useful patterns but currently ad-layout oriented.

Hermesfy tools registered:
- `hermesfy_define_workflow`
- `hermesfy_execute_workflow`
- `hermesfy_workflow_status`
- `hermesfy_edit_node`
- `hermesfy_list_models`
- `hermesfy_list_templates`
- `hermesfy_save_workflow`
- `hermesfy_load_workflow`
- `hermesfy_history`
- `hermesfy_run_agentic_workflow`

## Test results observed

Clone path used: `/tmp/hermesfy-studio`.

Ran tests in a local venv:
- 311 passed
- 3 failed

Failures:
1. `tests/test_agentic.py::TestRunAgenticWorkflow::test_simple_pattern_builds_workflow`
   - `run_agentic_workflow()` directly instantiates `FalProvider()` and fails without `FAL_API_KEY`.
   - `execute_workflow()` has a mock-provider fallback, but `run_agentic_workflow()` does not.
2. `tests/test_cli.py::test_cli_help`
   - test invokes system `python3 -m hermesfy.cli`, not the venv Python, causing `ModuleNotFoundError: hermesfy`.
3. `tests/test_cli.py::test_cli_list_models`
   - subprocess uses system Python/PYTHONPATH and misses installed `httpx`.

Interpretation: early-stage but not broken beyond repair; suitable for borrowing ideas, not a production dependency without cleanup.

## Recommended linux-ricing adaptation

Add an internal desktop preview pipeline rather than adopting Hermesfy wholesale.

Potential module layout:
- `workflow/preview_pipeline/graph.py`
- `workflow/preview_pipeline/nodes.py`
- `workflow/preview_pipeline/budget.py`
- `workflow/preview_pipeline/validators.py`
- `workflow/preview_pipeline/templates/desktop_overview.yaml`

Keep existing `visualize_node` as the LangGraph/user gate, but delegate internals to the preview pipeline.

Suggested node types:
- `desktop_prompt`
- `fal_desktop_concept`
- `vision_palette_extract`
- `desktop_contract_validate`
- `preview_html_render`
- `preview_cache`
- `maybe_refine_prompt`

Desktop-specific validators should reject:
- wallpaper-only images
- cinematic poster/hero framing
- letterbox bars / wrong aspect ratio
- generic dashboards/card grids
- missing visible desktop chrome/panel/window/menu/terminal affordances
- images that violate the user's dark RPG/menu aesthetic
- images whose visible UI cannot map to a declared implementation strategy

Cost policy:
- Default remains one paid hero image.
- Variants require explicit user authorization and a visible budget estimate.
- Preserve `visualize.pending.json` identity semantics so accidental re-entry cannot silently approve a different paid image.

## Integration warning

If using Hermesfy as an external Hermes plugin later, unify credential resolution first:
- Accept current linux-ricing `FAL_KEY` resolution path.
- Avoid logging secret values.
- Add `fal-ai/nano-banana` or any current desktop-overview model to registry.
- Verify non-editable package install includes templates/fonts/skill files.
