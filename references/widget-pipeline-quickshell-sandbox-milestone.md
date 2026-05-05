# Widget Pipeline Quickshell Sandbox Milestone

Use this reference when continuing the Step 6 widget/dashboard DAG after the first dry-run and Quickshell sandbox milestones.

## Proven milestone boundary

The safe second milestone is code generation only, not live launch:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python scripts/widget_pipeline_sample.py \
  --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png \
  --out /tmp/widget-pipeline-sample-maplestory \
  --framework quickshell \
  --renderer quickshell \
  --no-launch \
  --dry-run
```

Expected artifacts under `--out`:

- `sandbox/quickshell/shell.qml`
- `sandbox/quickshell/manifest.json`
- sandbox-local copied texture assets
- report JSON/Markdown with live-only stages marked `SKIP`

Do not write or symlink into `~/.config/quickshell`, `~/.config/eww`, `~/.config/ags`, or `~/.config/fabric` during this milestone.

## Adapter contract

Quickshell sandbox generation should:

1. Accept normalized widget element contracts and validated texture bundle outputs.
2. Copy texture assets into `sandbox/quickshell/assets/`.
3. Emit QML that references only sandbox-relative assets.
4. Emit a manifest recording framework, sandbox root, generated files, copied assets, live-config status, launch status, and policy checks.
5. Return explicit stage results so the sample harness can report what was proven and what was deferred.

## KDE / Wayland policy checks

Static validation should reject:

- `FloatingWindow` for shell widgets, panels, launchers, menus, quest/notification cards, and desktop cards.
- `hyprctl` in KDE paths.
- absolute or expanded live config references.
- static clock placeholders (`contract_clock` rendering `12:00`) without a live `system_time` timer/date binding.
- file paths outside the sandbox root.
- symlinked output roots or managed subdirectories.

Use `PanelWindow` with anchors/margins and `ExclusionMode.Ignore` for visually floating cards on KDE/Wayland.

## Stage-gate honesty

Generated QML is not visual success. Runtime visual validation may report `PASS` only after the bounded sandbox process stays alive long enough for capture, a screenshot is written under `--out/screenshots/`, rendered crops are extracted under `--out/rendered-real/`, and target-vs-real comparisons/review artifacts are produced under `--out/comparisons/` / `--out/reports/`.

Expected conservative statuses:

- `quickshell-sandbox: PASS` after static sandbox generation/validation succeeds.
- `runtime-launch: SKIP` when `--no-launch`, no graphical session, or missing `quickshell`; `PASS` only for bounded sandbox launch.
- `screenshot-capture: SKIP` when runtime launch is skipped or capture tooling is missing; `PASS` only for a non-blank screenshot artifact.
- `runtime-rendered-crops: PASS` only when screenshot regions are cropped for every contract.
- `visual-score: PASS/FAIL` only from real screenshot crops when runtime capture exists; otherwise `SKIP`.
- `desktop-promotion: SKIP` until the later live-promotion milestone.

Never convert missing runtime, deferred launch, missing screenshot support, or generated QML alone into fake `PASS` results.

## Verification checklist

Run both automated tests and a real fixture replay:

```bash
python -m pytest tests/test_texture_assets.py tests/test_widget_pipeline_*.py -q
python scripts/widget_pipeline_sample.py --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png --out /tmp/widget-pipeline-sample-maplestory --framework quickshell --renderer quickshell --no-launch --dry-run
# When Quickshell and a GUI session are available, also run the bounded real-runtime replay:
python scripts/widget_pipeline_sample.py --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png --out /tmp/widget-pipeline-m3-quickshell-real-replay --framework quickshell --renderer quickshell --dry-run
```

Then verify:

- tests pass;
- generated `shell.qml` contains `PanelWindow`;
- generated `shell.qml` does not contain `FloatingWindow` or `hyprctl`;
- generated clock contracts use `Timer`, `new Date()`, and `Qt.formatDateTime(...)` instead of a static `text: "12:00"` placeholder;
- `manifest.json` records no live config writes;
- live config dirs for Quickshell/EWW/AGS/Fabric were not created or modified.

## Next milestone guidance

Milestone 3 now has an initial bounded runtime path: `--renderer quickshell` without `--no-launch` attempts a sandbox-only launch when `quickshell` and a graphical session are available, captures via `spectacle` or `grim`, rejects blank/transparent screenshots, crops per-contract real render artifacts, scores target crop vs real crop, and writes a review HTML under `--out/reports/visual-review.html`.

The next gate is component-mode sandbox proof, not live promotion. Before adding promotion/rollback manifests or wiring live desktop writes, generate the Quickshell artifact from the typed component model rather than `--preview-texture`, then prove that exact artifact path + SHA-256 passes static validation, bounded launch, localized screenshot scoring, game-feel scoring, contract-function validation, artifact-function validation, and manual review. The review artifact must show target crops, real rendered crops, diffs, hitbox overlays, component tree summary, and function results. Only after that same-artifact visual/function gate is green should Milestone 5 define dry-run-first promotion manifests with backups, restore actions, restart/liveness checks, and final live screenshot/function gates.

Current boundary remains conservative:

- Launch only the generated sandbox QML, never a live `~/.config/quickshell` config.
- Wrap launch with timeout, stdout/stderr capture, and guaranteed process cleanup.
- If `quickshell` is missing, report `runtime-launch: SKIP quickshell executable not found`.
- If no graphical session is available, report `runtime-launch: SKIP no graphical session detected`.
- If capture tooling is missing or unsafe, report `screenshot-capture: SKIP <reason>`.
- Write baseline screenshots, post-launch screenshots, real rendered crops, diff images, and review HTML only under `--out`.
- Localize the sandbox surface with before/after screenshot diffing and record `runtime_surface_bbox`; map framework-local render geometry through compositor scale before cropping.
- Score target crop vs real Quickshell crop; generated QML alone is still not visual success.
- Fail blank/transparent screenshots, missing crops, process crashes, titlebar/app-window drift, and any live config writes.

Only after this path is hardened in real desktop sessions should `craft_node()` integration be feature-flagged. For EWW/AGS/Fabric expansion, keep the same adapter interface and sandbox/reporting semantics. Compare frameworks by desktop profile, launch/capture feasibility, static validation surface, and ability to use generated texture assets — not by popularity alone.
