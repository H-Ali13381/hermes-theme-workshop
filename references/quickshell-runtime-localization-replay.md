# Quickshell Runtime Localization Replay

Use this reference when debugging Milestone 3+ widget/dashboard runtime validation on KDE Wayland or any compositor that places/scales Quickshell surfaces unpredictably.

## Session signal

A real Quickshell replay initially produced incorrect rendered crops because the cropper treated preview-image/widget coordinates as desktop screenshot coordinates. The visual comparison was therefore scoring unrelated desktop pixels instead of the sandbox Quickshell surface. Installing Quickshell and replaying against the live compositor exposed the bug; mocked tests alone did not.

## Fix pattern

1. Capture a baseline screenshot immediately before launching the sandbox runtime.
2. Launch only the generated sandbox Quickshell QML under the caller-provided `--out` directory.
3. Capture a post-launch screenshot.
4. Diff baseline vs post-launch screenshots and find the changed component representing the sandbox surface.
5. Record that component as `runtime_surface_bbox` in `sandbox/quickshell/manifest.json`.
6. Crop each widget from framework-local render geometry translated through `runtime_surface_bbox`.
7. Account for compositor scaling by deriving physical scale from `runtime_surface_bbox.width / render_geometry.surface.width` and height ratio.
8. If render geometry exists but no runtime surface can be localized, fail the crop stage. Do not silently fall back to desktop-origin cropping.

## Verified replay outcome

Representative successful real replay after the fix:

- runtime launch: `PASS`
- screenshot capture: `PASS`
- runtime crop extraction: `PASS`
- visual score: `PASS`
- desktop promotion: `SKIP` dry-run
- `runtime_surface_bbox`: `[1596, 1128, 1924, 620]`
- visual scores:
  - `full_hud`: `9.4075`
  - `workspace_group`: `8.5833`
  - `clock`: `9.3543`
  - `status_bars`: `8.6038`
  - `power_button`: `8.6803`

The important sanity check was visual and semantic, not just numeric: rendered-real crops showed the actual Quickshell HUD sections (live system-time clock surface, workspace slots, full HUD panel) instead of unrelated desktop pixels. Current generated clock QML uses a `Timer`, `new Date()`, and `Qt.formatDateTime(...)`; a visible static `12:00` placeholder is no longer enough to pass the clock functional gate.

## Verification commands

From the skill root:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python -m pytest tests/test_texture_assets.py tests/test_widget_pipeline_*.py -q
python scripts/widget_pipeline_sample.py \
  --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png \
  --out /tmp/widget-pipeline-m3-quickshell-real-replay \
  --framework quickshell \
  --renderer quickshell \
  --dry-run
```

Then inspect:

- `sandbox/quickshell/manifest.json` has `runtime_surface_bbox` and `live_config_written: false`.
- `sandbox/quickshell/shell.qml` contains `PanelWindow`, not `FloatingWindow`.
- `sandbox/quickshell/shell.qml` contains no `hyprctl`.
- `rendered-real/*.png` are actual widget crops from the Quickshell surface.
- all artifacts stay under `--out`.
- no lingering `quickshell` process remains after the run.

## Regression coverage to preserve

- localized surface origin crop mapping
- missing-localization failure when render geometry exists
- compositor-scaled surface bboxes
- manifest render geometry propagation
- process-group cleanup and honest launch status
