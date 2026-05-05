# Quickshell KDE Shell Chrome Contract

Session-derived failure mode: a generated `FloatingWindow` in `~/.config/quickshell/shell.qml` can appear on KDE/Wayland as a normal decorated application-style window with a titlebar. This creates preview/plan drift when the approved concept showed integrated shell chrome.

## Contract

When `design.json` / `visual_element_plan` promises Quickshell widgets, launchers, panels, notification/quest cards, or menu chrome:

- Use `PanelWindow` for every promised shell surface.
- Do not count `FloatingWindow` toward promised widget/shell surfaces.
- For visually floating cards or corner widgets, still use `PanelWindow` with anchors, margins, and `exclusionMode: ExclusionMode.Ignore`.
- Generated QML should include visible plan grammar, e.g. `inventory`, `launcher`, `rest`, `menu`, `ember`, `log`, when those concepts are promised.
- Keep exact approved palette hexes in generated QML; near-match hand-tuned colors can fail static palette alignment.
- If the design says ornate, thorned, carved, Diablo/RPG, relic, blackiron, or inventory-frame chrome, implement panel/button/slot frames with QtQuick `BorderImage` 9-slice/tiled assets. Plain `Rectangle` borders are a failure mode: they read as cheap dashboard boxes even if labels and colors are correct. `BorderImage` syntax alone is also not enough: assets must be generated/sourced through a texture subprocess, accompanied by metadata (`slice_px`, variants, asset paths), pass seam/tile validation, and survive live screenshot review as non-placeholder art. See `references/quickshell-ornate-tileable-borders.md`.

## Live verification snippet

```bash
python - <<'PY'
from pathlib import Path
import re
qml = Path('~/.config/quickshell/shell.qml').expanduser().read_text()
print('PanelWindow', len(re.findall(r'\bPanelWindow\s*\{', qml)))
print('FloatingWindow', len(re.findall(r'\bFloatingWindow\s*\{', qml)))
print({w: w in qml.lower() for w in ['inventory','launcher','rest','menu','ember','log']})
PY
quickshell list
quickshell log --no-color | tail -80
```

Current Quickshell runtime does not provide a `quickshell reload` subcommand. After editing `shell.qml`, restart explicitly:

```bash
quickshell kill || true
quickshell --path ~/.config/quickshell/shell.qml --daemonize --no-color --log-times -v
```

## Regression coverage

The linux-ricing workflow should reject QML that combines a Quickshell widget promise with `FloatingWindow`, and should require enough `PanelWindow` surfaces for promised widgets. Relevant test area: `tests/test_craft_node.py` Quickshell evaluator tests.
