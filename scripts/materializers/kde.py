"""KDE Plasma color scheme materializer."""
import time

from core.constants import HOME
from core.colors import hex_to_rgb
from core.process import run_cmd, cmd_exists, _get_kwrite
from core.backup import backup_file
from core.snapshots import snapshot_kde_state


def materialize_kde(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Materialize a KDE Plasma color scheme.  Full pre-flight + undo support."""
    palette = design["palette"]
    changes = []
    colorscheme_name = f"hermes-{design.get('name', 'ricer')}"

    kde_colors_dir = HOME / ".local" / "share" / "color-schemes"
    colorscheme_path = kde_colors_dir / f"{colorscheme_name}.colors"

    # KDE .colors format uses decimal RGB (r,g,b) NOT hex
    p = {k: hex_to_rgb(v) for k, v in palette.items()}

    colorscheme_content = f"""[ColorEffects:Disabled]
Color={p['surface']}
ColorAmount=0.55
ColorEffect=0
ContrastAmount=0.65
ContrastEffect=1
IntensityAmount=0.1
IntensityEffect=2

[ColorEffects:Inactive]
ChangeSelectionColor=true
Color={p['muted']}
ColorAmount=0.025
ColorEffect=2
ContrastAmount=0.1
ContrastEffect=2
Enable=false
IntensityAmount=0
IntensityEffect=0

[Colors:Button]
BackgroundAlternate={p['surface']}
BackgroundNormal={p['surface']}
ForegroundNormal={p['foreground']}
ForegroundInactive={p['muted']}
DecorationFocus={p['primary']}
DecorationHover={p['secondary']}
ForegroundNegative={p['danger']}
ForegroundPositive={p['success']}
ForegroundNeutral={p['warning']}

[Colors:Selection]
BackgroundNormal={p['primary']}
ForegroundNormal={p['background']}
DecorationFocus={p['accent']}
DecorationHover={p['accent']}

[Colors:Tooltip]
BackgroundNormal={p['surface']}
ForegroundNormal={p['foreground']}

[Colors:View]
BackgroundAlternate={p['surface']}
BackgroundNormal={p['background']}
ForegroundNormal={p['foreground']}
ForegroundInactive={p['muted']}
ForegroundNegative={p['danger']}
ForegroundPositive={p['success']}
ForegroundNeutral={p['warning']}
DecorationFocus={p['primary']}
DecorationHover={p['secondary']}

[Colors:Window]
BackgroundNormal={p['background']}
BackgroundAlternate={p['surface']}
ForegroundNormal={p['foreground']}
ForegroundInactive={p['muted']}
ForegroundNegative={p['danger']}
ForegroundPositive={p['success']}
ForegroundNeutral={p['warning']}
DecorationFocus={p['primary']}
DecorationHover={p['secondary']}

[Colors:Complementary]
BackgroundNormal={p['surface']}
ForegroundNormal={p['foreground']}
DecorationFocus={p['accent']}

[Colors:Header]
BackgroundNormal={p['background']}
ForegroundNormal={p['foreground']}
DecorationFocus={p['primary']}

[General]
ColorScheme={colorscheme_name}
Name={colorscheme_name}
shadeSortColumn=true

[WM]
activeBackground={p['background']}
activeForeground={p['foreground']}
inactiveBackground={p['surface']}
inactiveForeground={p['muted']}
activeBlend={p['primary']}
inactiveBlend={p['surface']}
"""

    if dry_run:
        state = snapshot_kde_state()
        changes.append({
            "app": "kde", "action": "dry-run",
            "path": str(colorscheme_path),
            "previous_colorscheme": state["active_colorscheme"],
            "description": f"Would write KDE colorscheme {colorscheme_name} and apply it",
        })
        return changes

    state = snapshot_kde_state()
    prev_scheme = state["active_colorscheme"]

    kdeglobals_path = HOME / ".config" / "kdeglobals"
    kdeglobals_backup = backup_file(kdeglobals_path, backup_ts, "kde/kdeglobals")
    existing_backup = backup_file(colorscheme_path, backup_ts, f"kde/{colorscheme_name}.colors")

    kde_colors_dir.mkdir(parents=True, exist_ok=True)
    colorscheme_path.write_text(colorscheme_content, encoding="utf-8")
    changes.append({
        "app": "kde", "action": "write",
        "path": str(colorscheme_path),
        "backup": existing_backup,
        "kdeglobals_backup": kdeglobals_backup,
        "previous_colorscheme": prev_scheme,
    })

    if cmd_exists("plasma-apply-colorscheme"):
        rc_pre, out_pre, err_pre = run_cmd(["plasma-apply-colorscheme", colorscheme_name], timeout=10)
        if "already set" in (out_pre or "") or "already set" in (err_pre or ""):
            run_cmd(["plasma-apply-colorscheme", "BreezeClassic"], timeout=5)
            time.sleep(0.3)
            rc, out, err = run_cmd(["plasma-apply-colorscheme", colorscheme_name], timeout=10)
        else:
            rc = rc_pre
        changes.append({
            "app": "kde", "action": "reload",
            "command": f"plasma-apply-colorscheme {colorscheme_name}",
            "exit_code": rc,
            "previous_colorscheme": prev_scheme,
        })

    return changes
