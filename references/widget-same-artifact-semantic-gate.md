# Widget Same-Artifact Semantic Gate

Use this reference when changing the linux-ricing widget pipeline, especially Quickshell preview-texture/runtime validation.

## Lesson

A widget can appear visually correct while its live behavior is being tested on a different artifact. That invalidates both visual and functional validation. The pipeline must prove that the same generated framework file being rendered/scored also contains the required dynamic bindings and action hitboxes.

## Required stages

- `function-validation`: contract honesty. Checks whether normalized contracts declare real/missing commands, data sources, update intervals, and decorative/unbound status honestly.
- `artifact-function-validation`: identity/semantic gate. Checks the generated framework artifact itself for required bindings/hitboxes and records its path plus SHA-256.

Both stages must appear separately in reports. A contract can have `artifact-function-validation: PASS` because the generated QML contains a hitbox/binding, while `function-validation: SKIP` because the real desktop command is not yet bound or not available.

## Quickshell requirements

For `shell.qml`:

- Record `generated_artifacts.qml_path` and `generated_artifacts.qml_sha256` in `sandbox/quickshell/manifest.json`.
- Treat a user report of "cursor changes but buttons do nothing" as a semantic-action failure first: inspect generated QML for `MouseArea` handlers that only `console.log(...)`, `NULL`/missing command contracts, missing `Quickshell.Io.Process` imports, argv/shell quoting mistakes, or unsupported desktop-state preconditions such as workspace targets that do not exist. Visibility and hover feedback are not sufficient evidence of functionality.
- Treat "click boxes are misaligned" as a geometry-contract failure: inspect generated QML for broad `anchors.fill: parent` over a cropped UI cluster, overlapping MouseAreas, and missing per-control `x`, `y`, `width`, and `height` values derived from normalized action regions. Fix with one explicit MouseArea per action slot/control before tuning visually.
- Reject static dynamic widgets: a clock with `data_source: system_time` cannot be only `text: "12:00"`.
- Require native time update machinery for clocks, e.g. `Timer`, `new Date()`, and/or `Qt.formatDateTime(...)` in the same QML artifact.
- Require explicit action hitboxes such as `MouseArea`, `TapHandler`, or framework equivalent for button/action contracts in the same artifact.
- Require visible game-menu feedback in the same artifact for every non-decorative control: hover (`containsMouse`, `HoverHandler`, `:hover`, or equivalent) plus pressed/active (`containsPress`, `TapHandler.pressed`, `:active`, checked/active class, or equivalent). Transparent flat overlays that only change the cursor fail the interaction-feel gate.
- Action hitboxes must be per-control, not just `anchors.fill: parent` over a broad semantic crop. Workspace groups need one hitbox per slot/action; circular/power controls should get centered bounded hitboxes so cursor changes do not appear over unrelated decorative whitespace.
- Non-decorative actions must carry real, safe desktop behavior in the contract and the generated QML must execute commands through safe argv-style process calls where possible. For KDE workspace slots, `qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop N` is only functional when `/VirtualDesktopManager count >= N`; otherwise the scorecard must show `SKIP`/`FAIL`. A power glyph must toggle an in-artifact power menu/confirmation surface. Do not use `qdbus6 org.kde.krunner /App org.kde.krunner.App.query power`; that opens search and fails the power-menu UX contract. A `MouseArea` that only logs to the console is decorative/unbound, not functional.
- Preview-texture mode may copy target crops for an upper-bound visual test, but it must layer required semantic bindings/hitboxes into that same QML file.

## Manual test rule

When the user asks to see or manually test a widget on screen, launch the current sandbox artifact under validation, not a separate component/demo/surrogate. Verify:

1. `quickshell` and a graphical session are available.
2. The launched process remains running.
3. A screenshot shows the widget is visible.
4. The report identifies which controls are live, skipped, decorative, or unbound.

Concrete safe launch pattern:

```bash
QML=/tmp/widget-pipeline-same-artifact-gate-verify/sandbox/quickshell/shell.qml
command -v quickshell
printf '%s/%s\n' "${XDG_SESSION_TYPE:-unset}" "${XDG_CURRENT_DESKTOP:-unset}"
quickshell --path "$QML" --no-color
```

In Hermes, run the `quickshell --path ...` command as a background PTY process so it remains on screen for the user. Immediately poll the process and capture a screenshot under the same `--out` tree, for example:

```bash
OUT=/tmp/widget-pipeline-same-artifact-gate-verify/screenshots/manual-test-visible.png
mkdir -p "$(dirname "$OUT")"
spectacle -b -n -o "$OUT" || grim "$OUT"
```

If vision analysis is unavailable or the active provider rejects image input, do not claim verification from vision. Fall back to deterministic local evidence: process poll output, Quickshell log lines (`Configuration Loaded`, QML action logs), screenshot existence/size, and if useful a small Pillow/template probe comparing `sandbox/quickshell/assets/full_hud.preview.png` against the screenshot to localize the widget. Report the PID/session id and the current live/decorative status; avoid pretending unbound `MouseArea` logs are real desktop actions.

## Regression command

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python -m pytest tests/test_widget_pipeline_*.py -q
python scripts/widget_pipeline_sample.py \
  --image /home/neos/Pictures/Maplestory-theme/2Xfxjp1WV_KqL9Vf3TJcr_E2kDVaWm.png \
  --out /tmp/widget-pipeline-same-artifact-gate-verify \
  --framework quickshell \
  --renderer quickshell \
  --preview-texture \
  --no-launch \
  --dry-run
```

Expected no-launch signal: `quickshell-sandbox: PASS`, `artifact-function-validation: PASS`, `function-validation: PASS` when safe sample commands are present, and `runtime-launch: SKIP`. If `function-validation: SKIP` appears for missing live commands in an experimental contract, treat it as honest until commands are intentionally supplied; do not describe that widget as functional.

## Pitfall this prevents

Do not validate a visual-only preview-texture QML, then validate functionality against a separate component-mode QML. That proves two different widgets. Every validation claim must name the artifact path/hash it applies to.
