# Widget Runtime Validation Hardening

Use this reference when extending the widget/dashboard DAG runtime stage after the Quickshell sandbox milestone.

## Session signal

Milestone 3 added bounded Quickshell runtime validation: sandbox-only launch, screenshot capture, real crop extraction, visual scoring, and review HTML. Independent review found the important hardening items that should be treated as class-level requirements for future EWW/AGS/Fabric adapters too.

## Runtime launch rules

- Launch only sandbox-local artifacts under the caller-provided `--out`; never launch or reference `~/.config/quickshell`, `~/.config/eww`, `~/.config/ags`, or `~/.config/fabric`.
- Use `shutil.which()` and launch the resolved executable path, not a literal command name after discovery.
- Start the runtime in a new session/process group and terminate/kill the whole group during cleanup. Killing only the parent process can leave forked shell/widget children alive.
- Runtime logs belong under `--out/sandbox/<framework>/runtime.log`.
- Manifest `launch.attempted` means a launch attempt actually reached process start, not that the launch passed.
- Missing executable, missing GUI session, or missing capture tooling must be explicit `SKIP` statuses, not weak `PASS` results.

## Artifact safety rules

- Managed output directories must reject symlinked roots/subdirs.
- Fixed artifact files such as `shell.qml`, `manifest.json`, `runtime.log`, screenshots, and review HTML must reject pre-existing symlink files before writing.
- Asset-copy inputs must resolve under the caller-provided `--out` root. A malicious/buggy bundle with `../` or absolute paths must not copy arbitrary readable files into the sandbox.
- Route contract/element IDs through filename-safe helpers before composing paths.

## Screenshot and visual scoring rules

- Capture screenshots only under `--out/screenshots/`.
- Reject blank, flat-color, transparent, corrupt, or missing screenshots as failures.
- Extract rendered crops under `--out/rendered-real/`; compare against target crops under `--out/comparisons/`.
- Generate a review page under `--out/reports/visual-review.html` showing target crop, real render, diff, and score.
- Generated QML/code alone is never visual success.

## Runtime crop localization contract

The runtime mapper must not use preview-image contract bboxes directly against a full-desktop screenshot. A compositor can place a `PanelWindow` at an arbitrary screen origin and can scale logical QML dimensions into larger physical screenshot pixels.

The Quickshell adapter now captures a baseline screenshot immediately before launching the sandbox, captures again after launch, computes a before/after diff component for the sandbox surface, records `runtime_surface_bbox` in `sandbox/quickshell/manifest.json`, and crops each widget from framework-local render geometry translated through that bbox. Crop mapping must account for compositor scale (`runtime_surface_bbox.width / render_geometry.surface.width`, same for height). If a runtime surface cannot be localized when render geometry is present, the crop stage must fail instead of silently cropping unrelated desktop pixels.

## Regression tests worth keeping

- Happy-path bounded launch with mocked runtime and screenshot tool.
- Missing executable / no GUI session / missing capture tool returns `SKIP`.
- Process exits early / `Popen` raises returns `FAIL` and records attempted launch correctly.
- Process-group cleanup calls group termination.
- Symlinked managed directory and symlinked fixed files are rejected.
- Escaping texture asset paths are rejected.
- Screenshot success-without-file, timeout, nonzero exit, blank/transparent/corrupt files fail.
- Review HTML and all artifacts remain under `--out`.
- Runtime crop tests cover localized surface origin, missing-surface failure, and compositor-scaled surface bboxes.
- Clock/data-binding tests cover both halves of the gate: static validation rejects a `contract_clock` hardcoded to `12:00`, and function validation skips clock contracts missing `data_source: system_time` instead of treating a visually matching placeholder as functional.
