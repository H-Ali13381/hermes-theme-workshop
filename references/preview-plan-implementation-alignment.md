# Preview → Plan → Implementation Alignment

Use this reference during autonomous or semi-autonomous KDE ricing runs when the approved preview/plan shows custom wallpaper, toolbar/panel chrome, widget menus, or other non-default UI moves.

## Core Contract

The final desktop must materially implement what the preview and plan made visible. Passing element scores is not enough if live KDE still looks like stock Plasma with a recolor.

Required checks when the plan mentions them:

1. **Wallpaper changed**
   - Verify the target image file exists.
   - Verify `plasma-org.kde.plasma.desktop-appletsrc` points to it, or use `plasma-apply-wallpaperimage <path>` and re-check.
   - Do not accept Breeze/Next/default wallpaper unless the approved plan explicitly asked for it.

2. **Custom toolbar/panel visible**
   - If `plan.html`/`design.json` says the stock toolbar/panel is replaced by EWW/Quickshell/widget chrome, prove the widget is running and visible.
   - For Quickshell: `quickshell list` and `Configuration Loaded` are necessary but not sufficient. Inspect the generated QML and live screenshot. A design promising several surfaces must define several visible `PanelWindow` shell surfaces and labelled UI grammar such as inventory/rest/ember/menu/launcher/log. Do not use `FloatingWindow` for promised shell chrome on KDE/Wayland: it can become a normal decorated application window with a titlebar. For visually floating quest/menu cards, prefer `PanelWindow` with corner/edge anchors and margins, but verify screenshot visibility. On this KDE/Quickshell runtime, ignored side/corner overlay panels can silently fail the visual contract: the QML loads and reserves/affects space, yet the actual left/right widget cards remain invisible behind apps/desktop layers. If named widgets are not visible in the screenshot, consolidate launcher/menu, quest board, meters, and inventory into a known-visible edge `PanelWindow` (for example the bottom rest-belt HUD) rather than claiming success. A tiny status strip, invisible side rail, or hidden menu toggled off by default does not satisfy a widget promise.
   - For EWW: `eww -c ~/.config/eww active-windows` must list the intended window; `eww open <window>` must return 0; logs must not show parse/runtime errors.
   - If KDE's stock panel remains for safety, hide or autohide it so the visible toolbar matches the preview. Verify with `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'for (var i=0;i<panels().length;++i){var p=panels()[i]; print(p.id+":"+p.hiding)}'`.

3. **More than palette/icon swap**
   - Cross-check design `originality_strategy.non_default_moves` against live artifacts: wallpaper, widget toolbar/menu, Plasma SVG chrome, launcher theme, terminal theme, fastfetch/prompt, lockscreen/GTK where applicable.
   - If only icons/colors changed, reject the result even when individual files exist.

4. **Live visual proof**
   - Capture a screenshot (`spectacle -b -o /tmp/rice-verify/<theme>-live.png` on KDE if available) and inspect it before claiming completion.
   - Use vision analysis when available to confirm: changed wallpaper, non-default toolbar/widget UI, theme language, and no accidental stock/default chrome dominating the screen.

## EWW Runtime Failures That Scoring Can Miss

High craft score only proves files and palette exist. Always open the generated window.

Known failures and prevention:
- `calc(100% - 48px)` in `:geometry` fails. EWW geometry needs literal `px` or `%` lengths.
- Shell `$1`/`$2`/`$3` in defpoll command strings can be consumed by EWW interpolation and break awk. Prefer grep/cut/python one-liners or careful escaping.
- `(progress :value some_defpoll_var)` can fail on first render if the variable starts empty. Use a numeric fallback or label-based display.
- Commands like `kdotool` may be absent in the EWW runtime environment. Use `shutil.which(...)` or shell fallback logic.

Relevant regression tests currently live in `tests/test_craft_node.py` for calc geometry, shell-dollar variables, and raw progress values.

## When Alignment Fails

Fix the implementation or workflow, then continue. Do not hand-edit `design.json` or checkpoint state to make the plan match reality. If a workflow bug allowed the drift, patch code/tests and record the failure in `references/workflow-debugging-lessons.md`.