"""session_phases.py — Late phases (4-6) of the deterministic ricing session.

Extracted from scripts/deterministic_ricing_session.py to keep that file
within the 300-line budget.  Depends on session_helpers for log/run utilities.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from session_helpers import log, run, HOME, RICER_PY

# =============================================================================
# PHASE 4: APPLY
# =============================================================================

def phase4_apply(design: dict, wallpaper: str | None, force: bool = False) -> dict | None:
    log("=== PHASE 4: APPLY ===")
    if not force:
        response = input("CONFIRM APPLY? Type 'yes' to proceed: ")
        if response.strip().lower() != "yes":
            log("APPLY ABORTED BY USER.")
            return None

    cmd = [sys.executable, str(RICER_PY)]
    if design.get("preset_name"):
        cmd += ["preset", design["preset_name"]]
    else:
        cmd += ["apply", "--design", design["source"]]

    rc, out, err = run(cmd)
    if rc != 0:
        log(f"FATAL: Apply failed (exit {rc}): {err}")
        return None

    try:
        manifest = json.loads(out)
    except json.JSONDecodeError:
        log(f"FATAL: Apply output is not valid JSON:\n{out[:500]}")
        return None

    if wallpaper:
        appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
        prev_wallpaper = None
        if appletsrc.exists():
            m = re.search(r"^Image\s*=\s*(.+)$", appletsrc.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
            if m:
                prev_wallpaper = m.group(1).strip()
        log(f"APPLYING WALLPAPER: {wallpaper}  (previous: {prev_wallpaper})")
        run(["plasma-apply-wallpaperimage", wallpaper])
        manifest.setdefault("changes", []).append({
            "app": "wallpaper", "action": "set", "path": wallpaper,
            "previous_wallpaper": prev_wallpaper,
            "method": "plasma-apply-wallpaperimage", "manual": True,
        })

    log("APPLY COMPLETE.")
    return manifest


# =============================================================================
# PHASE 5: POST-FLIGHT VERIFICATION
# =============================================================================

def phase5_postflight(baseline: dict) -> bool:
    log("=== PHASE 5: POST-FLIGHT VERIFICATION ===")
    rc, out, err = run([sys.executable, str(RICER_PY.parent / "desktop_state_audit.py")])
    if rc != 0:
        log(f"WARNING: Post-flight audit failed: {err}")
        return False

    baselines_dir = HOME / ".cache" / "linux-ricing" / "baselines"
    manifests = sorted(baselines_dir.glob("*_baseline.json"))
    if not manifests:
        log("WARNING: No post-flight baseline found.")
        return False

    current = json.loads(manifests[-1].read_text(encoding="utf-8"))
    old_kde = baseline.get("kde", {})
    new_kde = current.get("kde", {})

    checks = [
        ("colorscheme",  old_kde.get("colorscheme", {}).get("active_scheme"),   new_kde.get("colorscheme", {}).get("active_scheme")),
        ("kvantum_theme",old_kde.get("kvantum", {}).get("kvantum_theme"),        new_kde.get("kvantum", {}).get("kvantum_theme")),
        ("widget_style", old_kde.get("kvantum", {}).get("widget_style"),         new_kde.get("kvantum", {}).get("widget_style")),
        ("plasma_theme", old_kde.get("plasma_theme", {}).get("active_theme"),    new_kde.get("plasma_theme", {}).get("active_theme")),
        ("cursor",       old_kde.get("cursor", {}).get("active_cursor"),         new_kde.get("cursor", {}).get("active_cursor")),
        ("wallpaper",    old_kde.get("wallpaper", {}).get("image_path"),         new_kde.get("wallpaper", {}).get("image_path")),
    ]

    print("\n" + "-" * 60 + "\nPOST-FLIGHT COMPARISON\n" + "-" * 60)
    changed = []
    for name, old_val, new_val in checks:
        status = "CHANGED" if old_val != new_val else "SAME"
        if old_val != new_val:
            changed.append(name)
        print(f"  {name:20s} {status:10s}  {old_val} -> {new_val}")
    print("-" * 60)

    if not changed:
        log("WARNING: No visible changes detected post-flight. Theme may not have applied correctly.")
    else:
        log(f"POST-FLIGHT: {len(changed)} change(s) confirmed: {', '.join(changed)}")
    return True


# =============================================================================
# PHASE 6: ROLLBACK
# =============================================================================

def phase6_rollback() -> bool:
    log("=== PHASE 6: ROLLBACK ===")
    rc, out, err = run([sys.executable, str(RICER_PY), "undo"])
    if rc != 0:
        log(f"FATAL: Rollback failed (exit {rc}): {err}")
        return False
    try:
        result = json.loads(out)
    except json.JSONDecodeError:
        log(f"FATAL: Rollback output is not valid JSON:\n{out[:500]}")
        return False

    log(f"ROLLBACK STATUS: {result.get('status')}")
    for item in result.get("restored", []):
        log(f"  RESTORED: {item}")
    for item in result.get("failed", []):
        log(f"  FAILED:  {item}")
    for item in result.get("skipped", []):
        log(f"  SKIPPED: {item}")
    return result.get("status") in ("success", "partial")
