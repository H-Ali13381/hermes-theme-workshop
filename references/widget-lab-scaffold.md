# Widget Lab Scaffold

Use this reference when the full linux-ricing workflow is too broad and widget work needs to be isolated into a reproducible sandbox project.

## Session outcome

A standalone lab was created at:

`/home/neos/Documents/SideProjects/linux-widgets`

The lab intentionally starts with one renderer and one static sandbox gate instead of trying to test the whole rice end-to-end.

## Renderer decision

First renderer: **Quickshell**.

Reasoning:

- Target environment is KDE on Wayland.
- The linux-ricing policy already says Quickshell before EWW for KDE Wayland widget/panel chrome.
- Quickshell `PanelWindow` avoids titlebar/app-window drift seen with ordinary/floating windows.
- QML gives real state, timers, hover/pressed states, layout, and asset references while keeping a plausible promotion path.

## Gate 0 shape

Static sandbox proof only:

```bash
cd /home/neos/Documents/SideProjects/linux-widgets
python3 scripts/render_sample.py --spec samples/simple_clock.json --out out/simple-clock
python3 -m unittest discover -s tests -v
```

Expected generated artifacts:

- `out/simple-clock/sandbox/quickshell/shell.qml`
- `out/simple-clock/sandbox/quickshell/manifest.json`

Expected statuses:

- `quickshell-sandbox: PASS`
- `function-validation: SKIP action commands are decorative by contract` for decorative sample actions
- `artifact-function-validation: PASS`
- `runtime-launch: SKIP not requested by static renderer`
- `desktop-promotion: SKIP no live promotion milestone`

## Static validation invariants

The first gate validates only what it actually proves:

- generated QML contains `PanelWindow`;
- generated QML does not contain `FloatingWindow`;
- generated QML does not contain `hyprctl`;
- system-time widgets contain `Timer`, `new Date()`, and `Qt.formatDateTime(...)`;
- clickable controls contain explicit per-control hitbox markers, `MouseArea`, hover feedback, and pressed feedback;
- manifest records same-artifact `qml_path` and `qml_sha256`;
- manifest records `live_config_write: false`;
- no writes to `~/.config/quickshell`, `~/.config/eww`, `~/.config/ags`, or `~/.config/fabric`.

## Project-local knowledge library

A later refocus session ingested Quickshell/Qt/KDE widget research into the lab as static examples plus project-local callable skills. Before editing a specific widget/UI element in the lab, read:

- `docs/research-sources.md` — distilled source notes from Quickshell v0.3.0 docs, Qt docs, and official `quickshell-examples` commit `c6d1236efe265ae34e8c78a27ee9e196ea19d895`.
- `docs/skill-index.md` — task/UI-element → local skill/example map.
- `skills/<name>/SKILL.md` — project-local skills, not globally installed Hermes skills.
- `examples/quickshell/` — static component and standalone QML examples.

Current local skills cover: `quickshell-panel-window`, `quickshell-clock-label`, `quickshell-game-button`, `quickshell-status-meter`, `quickshell-popup-menu`, `quickshell-process-action`, `quickshell-nine-slice-frame`, and `quickshell-layouts`.

Validation command for the knowledge inventory:

```bash
cd /home/neos/Documents/SideProjects/linux-widgets
python3 scripts/validate_knowledge_inventory.py
```

Expected output after the ingestion session:

```text
validated 8 skills and 8 qml examples
```

This is intentionally a codebase-local skill library: use it to ground future widget work, but do not copy it into `~/.config/quickshell` or treat example existence as live desktop success.

## Agent contract

When continuing from this lab, preserve the ladder:

1. Static sandbox generation from JSON contracts.
2. Framework-neutral component model (`HudRoot`, `PanelFrame`, `GameButton`, `ClockLabel`, `StatusMeter`, `WorkspaceSlot`, `PowerGlyph`).
3. Visual states and semantic action/data contracts in the same generated artifact.
4. Ornate sandbox-local assets / 9-slice frames.
5. Bounded runtime launch and screenshot capture under `--out`.
6. Same-artifact visual/function review HTML.
7. Feature-flagged integration into linux-ricing craft path.
8. Only then live promotion/rollback manifests.

Do not skip from generated QML to live desktop promotion.

## Teaching / handoff style for this lab

The user explicitly rejected verbose terminal explanations while learning this scaffold. For this project, teach in short, concrete chunks:

- Prefer terse pipeline maps: `JSON spec -> renderer -> shell.qml -> manifest -> optional foreground launch`.
- Explain only the next layer the user asked about; avoid full recaps unless requested.
- For command output, translate only the actionable lines and name the next command.
- For QML walkthroughs, group by object (`PanelWindow`, card `Rectangle`, `Timer`, `Text`, `MouseArea`) and explain one purpose per bullet.

## Generated QML comments lesson

QML accepts normal `//` comments. If the user wants commented generated QML, add comments to the renderer template, not only to `out/.../shell.qml`; otherwise the next `make render` discards them. After changing renderer comments, run `make smoke` and note the manifest hash will change because comments are part of the generated artifact bytes.