#!/usr/bin/env python3
"""
================================================================================
HERMES-RICER DESKTOP STATE AUDIT
Corporate-grade baseline capture for KDE Plasma (and generic fallback)
================================================================================

PURPOSE:
    Capture the COMPLETE current state of the desktop environment before any
    ricing operation. READ-ONLY with respect to the live desktop — never touches
    ~/.config or running processes. Writes only to ~/.cache/linux-ricing/baselines/.

OUTPUT:
    1. JSON manifest: ~/.cache/linux-ricing/baselines/<timestamp>_baseline.json
    2. Config backup dir: ~/.cache/linux-ricing/baselines/<timestamp>_files/

CAPTURED STATE:
    - Desktop Environment / Session type
    - Active colorscheme
    - Active wallpaper (path, mode, plugin)
    - Plasma theme (panel, tasks, dialogs)
    - Kvantum widget style
    - Cursor theme
    - Icon theme
    - GTK theme (if applicable)
    - Splash screen theme
    - Konsole default profile
    - Panel configuration (appletsrc snapshot)
    - All relevant config file contents

USAGE:
    python3 desktop_state_audit.py
    python3 desktop_state_audit.py --output /custom/path/baseline.json

DETERMINISM:
    All values are read via kreadconfig6/5 or direct file parsing. No guesses.
================================================================================
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from desktop_utils import discover_desktop          # noqa: E402
from core.audit_utils import run_cmd, cmd_exists, kread, read_ini_key, copy_to_baseline  # noqa: E402
from core.state_capture import (                   # noqa: E402
    capture_kde_colorscheme, capture_kde_wallpaper, capture_kde_plasma_theme,
    capture_kvantum_state, capture_cursor_theme, capture_icon_theme,
    capture_gtk_theme, capture_splash_screen, capture_konsole_state,
    capture_panel_config, backup_all_config_files,
)

HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "linux-ricing"
BASELINES_DIR = CACHE_DIR / "baselines"

# All capture and backup functions are imported from core.state_capture above.

# =============================================================================
# MAIN AUDIT
# =============================================================================

def run_full_audit(output_path: str | None = None) -> dict[str, Any]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    baseline_dir = BASELINES_DIR / f"{timestamp}_files"
    baseline_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== HERMES-RICER DESKTOP STATE AUDIT ===")
    print(f"Timestamp : {timestamp}")
    print(f"Baseline  : {baseline_dir}")
    print("")

    # 1. Desktop discovery
    print("[1/8] Discovering desktop environment...")
    desktop = discover_desktop()
    print(f"  WM/DE   : {desktop['wm']}")
    print(f"  Session : {desktop['session_type']}")

    # 2. KDE-specific state
    print("")
    print("[2/8] Capturing KDE colorscheme...")
    colorscheme = capture_kde_colorscheme()
    print(f"  Active  : {colorscheme['active_scheme']}")

    print("")
    print("[3/8] Capturing wallpaper...")
    wallpaper = capture_kde_wallpaper()
    print(f"  Plugin  : {wallpaper.get('plugin')}")
    print(f"  Image   : {wallpaper.get('image_path')}")
    print(f"  Fill    : {wallpaper.get('fill_mode')}")

    print("")
    print("[4/8] Capturing Plasma theme / Kvantum / Cursor / Icons...")
    plasma_theme = capture_kde_plasma_theme()
    kvantum = capture_kvantum_state()
    cursor = capture_cursor_theme()
    icons = capture_icon_theme()
    print(f"  Plasma  : {plasma_theme['active_theme']}")
    print(f"  Kvantum : {kvantum['kvantum_theme']} (widgetStyle={kvantum['widget_style']})")
    print(f"  Cursor  : {cursor['active_cursor']}")
    print(f"  Icons   : {icons['active_icon_theme']}")

    print("")
    print("[5/8] Capturing GTK theme / Splash...")
    gtk = capture_gtk_theme()
    splash = capture_splash_screen()
    print(f"  GTK     : {gtk['gtk_theme']}")
    print(f"  Splash  : {splash['active_splash']}")

    print("")
    print("[6/8] Capturing Konsole state...")
    konsole = capture_konsole_state()
    print(f"  Profile : {konsole['default_profile']}")
    print(f"  All     : {konsole['all_profiles']}")

    print("")
    print("[7/8] Capturing panel/widgets configuration...")
    panel = capture_panel_config()
    if "error" in panel:
        print(f"  ERROR   : {panel['error']}")
    else:
        print(f"  Panels  : {len(panel['panels'])}")
        for p in panel['panels']:
            print(f"    [{p['containment_id']}] {p['plugin']} — {len(p['applets'])} applets")
            for a in p['applets']:
                print(f"      - {a['plugin']}")

    print("")
    print("[8/8] Backing up config files...")
    backups = backup_all_config_files(baseline_dir)
    backed_count = sum(1 for v in backups.values() if v is not None)
    print(f"  Backed up {backed_count}/{len(backups)} items")

    # Assemble manifest
    manifest = {
        "audit_version": "1.0.0",
        "timestamp": timestamp,
        "hostname": os.uname().nodename,
        "user": os.environ.get("USER", "unknown"),
        "desktop": desktop,
        "kde": {
            "colorscheme": colorscheme,
            "wallpaper": wallpaper,
            "plasma_theme": plasma_theme,
            "kvantum": kvantum,
            "cursor": cursor,
            "icons": icons,
            "splash": splash,
        },
        "gtk": gtk,
        "konsole": konsole,
        "panel": panel,
        "backups": backups,
        "baseline_dir": str(baseline_dir),
    }

    # Write manifest
    if output_path:
        manifest_path = Path(output_path)
    else:
        manifest_path = BASELINES_DIR / f"{timestamp}_baseline.json"

    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    print("")
    print(f"=== AUDIT COMPLETE ===")
    print(f"Manifest  : {manifest_path}")
    print(f"Files     : {baseline_dir}")
    print("")
    print("THIS BASELINE IS IMMUTABLE. STORE IT SAFELY.")

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Hermes Ricer — Desktop State Audit (reads desktop state, writes to ~/.cache only)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Custom output path for the JSON manifest"
    )
    args = parser.parse_args()
    run_full_audit(output_path=args.output)


if __name__ == "__main__":
    main()
