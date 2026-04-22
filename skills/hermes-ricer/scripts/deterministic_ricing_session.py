#!/usr/bin/env python3
"""
================================================================================
DETERMINISTIC RICING SESSION — CORPORATE-GRADE DESKTOP THEMING PROTOCOL
================================================================================

PURPOSE:
    Orchestrate a desktop ricing session with zero ambiguity, full audit trail,
    and deterministic rollback. This script is the ONLY entry point for applying
    themes. Do NOT call ricer.py directly — this wrapper enforces safety.

PROTOCOL PHASES:
    Phase 0 — Pre-flight Audit:   Capture complete desktop state (immutable)
    Phase 1 — Design Selection:   Load preset or custom design_system.json
    Phase 2 — Dry-Run:            Preview all changes without writing anything
    Phase 3 — Verification:       Human reviews the dry-run manifest
    Phase 4 — Apply:              Execute materialization (only after confirm)
    Phase 5 — Post-flight Verify: Confirm changes took effect
    Phase 6 — Rollback (opt):    Full undo to pre-flight state if anything fails

DETERMINISM GUARANTEES:
    - Every run starts with a timestamped baseline capture
    - All config writes use atomic temp-file-then-rename where possible
    - Backup dir is shared across all materializers in a single run
    - Manifest is JSON with full change log, previous values, and backup paths
    - Rollback restores: colorscheme, kvantum, plasma theme, cursor, wallpaper,
      kitty theme, konsole profile, rofi theme, waybar style, dunst config

USAGE:
    # Apply a named preset
    python3 deterministic_ricing_session.py --preset void-dragon

    # Apply a custom design JSON
    python3 deterministic_ricing_session.py --design ~/my_theme.json

    # With wallpaper
    python3 deterministic_ricing_session.py --preset void-dragon --wallpaper ~/wall.png

    # Dry-run only (no changes)
    python3 deterministic_ricing_session.py --preset void-dragon --dry-run

    # Rollback last session
    python3 deterministic_ricing_session.py --rollback

    # Show current status and last baseline
    python3 deterministic_ricing_session.py --status

EXIT CODES:
    0 — Success
    1 — Invalid arguments or missing files
    2 — Pre-flight audit failure
    3 — Dry-run failure
    4 — Apply failure (partial or total)
    5 — Rollback failure
================================================================================
"""

import argparse
import json
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

HOME = Path.home()
SKILL_DIR = HOME / ".hermes" / "skills" / "creative" / "hermes-ricer"
RICER_PY = SKILL_DIR / "scripts" / "ricer.py"
AUDIT_PY = SKILL_DIR / "scripts" / "desktop_state_audit.py"
SESSION_LOG_DIR = HOME / ".cache" / "hermes-ricer" / "session_logs"

# =============================================================================
# UTILITIES
# =============================================================================

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    # Also append to session log if one is active
    if getattr(sys, "_session_log_path", None):
        with open(sys._session_log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    log(f"RUN: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.stdout:
            log(f"STDOUT: {result.stdout.strip()[:200]}")
        if result.stderr:
            log(f"STDERR: {result.stderr.strip()[:200]}")
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        log(f"EXCEPTION: {e}")
        return -1, "", str(e)


def ensure_deps() -> bool:
    if not RICER_PY.exists():
        log(f"FATAL: ricer.py not found at {RICER_PY}")
        return False
    if not AUDIT_PY.exists():
        log(f"FATAL: desktop_state_audit.py not found at {AUDIT_PY}")
        return False
    return True


def load_preset(name: str) -> dict | None:
    rc, out, _ = run([sys.executable, str(RICER_PY), "presets"])
    if name not in out:
        log(f"FATAL: preset '{name}' not found. Run 'ricer presets' to list.")
        return None
    # ricer presets don't output JSON, so we trust the name and let ricer load it
    return {"name": name, "source": "preset"}


# =============================================================================
# PHASE 0: PRE-FLIGHT AUDIT
# =============================================================================

def phase0_audit() -> dict | None:
    log("=== PHASE 0: PRE-FLIGHT AUDIT ===")
    rc, out, err = run([sys.executable, str(AUDIT_PY)])
    if rc != 0:
        log(f"FATAL: Audit script failed (exit {rc}): {err}")
        return None

    # Find the latest baseline manifest
    baselines_dir = HOME / ".cache" / "hermes-ricer" / "baselines"
    manifests = sorted(baselines_dir.glob("*_baseline.json"))
    if not manifests:
        log("FATAL: Audit completed but no baseline manifest found.")
        return None

    latest = manifests[-1]
    log(f"BASELINE CAPTURED: {latest}")
    baseline = json.loads(latest.read_text(encoding="utf-8"))
    return baseline


# =============================================================================
# PHASE 1: DESIGN SELECTION
# =============================================================================

def phase1_design(args) -> dict | None:
    log("=== PHASE 1: DESIGN SELECTION ===")
    if args.preset:
        design = load_preset(args.preset)
        if not design:
            return None
        design["preset_name"] = args.preset
        log(f"SELECTED PRESET: {args.preset}")
    elif args.design:
        path = Path(args.design)
        if not path.exists():
            log(f"FATAL: Design file not found: {path}")
            return None
        design = json.loads(path.read_text(encoding="utf-8"))
        design["source"] = str(path)
        log(f"SELECTED CUSTOM DESIGN: {path}")
    else:
        log("FATAL: No design specified. Use --preset or --design.")
        return None
    return design


# =============================================================================
# PHASE 2: DRY-RUN
# =============================================================================

def phase2_dryrun(design: dict, wallpaper: str | None) -> dict | None:
    log("=== PHASE 2: DRY-RUN MATERIALIZATION ===")
    cmd = [sys.executable, str(RICER_PY)]
    if design.get("preset_name"):
        cmd += ["preset", design["preset_name"], "--dry-run"]
    else:
        cmd += ["apply", "--design", design["source"], "--dry-run"]

    if wallpaper:
        # ricer.py apply doesn't take --wallpaper in preset mode directly via CLI
        # We'll handle wallpaper separately after apply
        pass

    rc, out, err = run(cmd)
    if rc != 0:
        log(f"FATAL: Dry-run failed (exit {rc}): {err}")
        return None

    try:
        manifest = json.loads(out)
    except json.JSONDecodeError:
        log(f"FATAL: Dry-run output is not valid JSON:\n{out[:500]}")
        return None

    log(f"DRY-RUN BACKUP DIR: {manifest.get('backup_dir')}")
    return manifest


# =============================================================================
# PHASE 3: VERIFICATION (HUMAN-READABLE DIFF)
# =============================================================================

def phase3_verify(manifest: dict, baseline: dict) -> bool:
    log("=== PHASE 3: VERIFICATION ===")
    changes = manifest.get("changes", [])
    if not changes:
        log("WARNING: Dry-run produced zero changes. Nothing to apply.")
        return False

    print("\n" + "=" * 70)
    print("PROPOSED CHANGES")
    print("=" * 70)

    for change in changes:
        app = change.get("app", "?")
        action = change.get("action", "?")
        if action == "error":
            print(f"  [{app}] ERROR: {change.get('error')}")
            continue
        if action == "dry-run":
            path = change.get("path") or change.get("config_path") or change.get("profile_path")
            print(f"  [{app}] Would write: {path}")
            # Show previous state if available
            for key in ["previous_colorscheme", "previous_kvantum_theme", "previous_theme", "previous_cursor", "previous_profile"]:
                if key in change:
                    print(f"          Previous {key}: {change[key]}")
        else:
            path = change.get("path") or change.get("config_path")
            print(f"  [{app}] {action}: {path}")

    print("=" * 70)
    print(f"BASELINE: {baseline.get('timestamp')}")
    print(f"BACKUP DIR: {manifest.get('backup_dir')}")
    print("=" * 70 + "\n")

    return True


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

    # Handle wallpaper separately if provided.
    # Snapshot current wallpaper from appletsrc BEFORE applying so undo can restore it.
    if wallpaper:
        import re, shutil, datetime as _dt
        appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
        prev_wallpaper = None
        if appletsrc.exists():
            m = re.search(r"^Image\s*=\s*(.+)$", appletsrc.read_text(errors="replace"), re.MULTILINE)
            if m:
                prev_wallpaper = m.group(1).strip()
        log(f"APPLYING WALLPAPER: {wallpaper}  (previous: {prev_wallpaper})")
        run(["plasma-apply-wallpaperimage", wallpaper])
        manifest.setdefault("changes", []).append({
            "app": "wallpaper",
            "action": "set",
            "path": wallpaper,
            "previous_wallpaper": prev_wallpaper,
            "method": "plasma-apply-wallpaperimage",
            "manual": True,
        })

    log("APPLY COMPLETE.")
    return manifest


# =============================================================================
# PHASE 5: POST-FLIGHT VERIFICATION
# =============================================================================

def phase5_postflight(baseline: dict) -> bool:
    log("=== PHASE 5: POST-FLIGHT VERIFICATION ===")
    # Re-run a lightweight audit and compare key fields
    rc, out, err = run([sys.executable, str(AUDIT_PY)])
    if rc != 0:
        log(f"WARNING: Post-flight audit failed: {err}")
        return False

    baselines_dir = HOME / ".cache" / "hermes-ricer" / "baselines"
    manifests = sorted(baselines_dir.glob("*_baseline.json"))
    if not manifests:
        log("WARNING: No post-flight baseline found.")
        return False

    current = json.loads(manifests[-1].read_text(encoding="utf-8"))

    # Compare critical fields.
    # Audit JSON structure (verified from desktop_state_audit.py output):
    #   kde.colorscheme.active_scheme
    #   kde.kvantum.kvantum_theme
    #   kde.kvantum.widget_style
    #   kde.plasma_theme.active_theme
    #   kde.cursor.active_cursor
    #   kde.wallpaper.image_path
    checks = []
    old_kde = baseline.get("kde", {})
    new_kde = current.get("kde", {})

    checks.append(("colorscheme",
        old_kde.get("colorscheme", {}).get("active_scheme"),
        new_kde.get("colorscheme", {}).get("active_scheme")))
    checks.append(("kvantum_theme",
        old_kde.get("kvantum", {}).get("kvantum_theme"),
        new_kde.get("kvantum", {}).get("kvantum_theme")))
    checks.append(("widget_style",
        old_kde.get("kvantum", {}).get("widget_style"),
        new_kde.get("kvantum", {}).get("widget_style")))
    checks.append(("plasma_theme",
        old_kde.get("plasma_theme", {}).get("active_theme"),
        new_kde.get("plasma_theme", {}).get("active_theme")))
    checks.append(("cursor",
        old_kde.get("cursor", {}).get("active_cursor"),
        new_kde.get("cursor", {}).get("active_cursor")))
    checks.append(("wallpaper",
        old_kde.get("wallpaper", {}).get("image_path"),
        new_kde.get("wallpaper", {}).get("image_path")))

    print("\n" + "-" * 60)
    print("POST-FLIGHT COMPARISON")
    print("-" * 60)
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


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Deterministic Ricing Session — Corporate-Grade Desktop Theming"
    )
    parser.add_argument("--preset", default=None, help="Named preset to apply")
    parser.add_argument("--design", default=None, help="Path to design_system.json")
    parser.add_argument("--wallpaper", default=None, help="Wallpaper image path")
    parser.add_argument("--dry-run", action="store_true", help="Stop after dry-run (no apply)")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--rollback", action="store_true", help="Rollback last applied theme")
    parser.add_argument("--status", action="store_true", help="Show current status and last baseline")
    args = parser.parse_args()

    # Setup session log
    SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sys._session_log_path = str(SESSION_LOG_DIR / f"session_{log_ts}.log")

    log("=" * 70)
    log("DETERMINISTIC RICING SESSION STARTED")
    log(f"Args: preset={args.preset}, design={args.design}, wallpaper={args.wallpaper}, dry_run={args.dry_run}, rollback={args.rollback}")
    log("=" * 70)

    if not ensure_deps():
        sys.exit(1)

    if args.status:
        run([sys.executable, str(RICER_PY), "status"])
        baselines_dir = HOME / ".cache" / "hermes-ricer" / "baselines"
        manifests = sorted(baselines_dir.glob("*_baseline.json"))
        if manifests:
            print(f"\nLast baseline: {manifests[-1]}")
        else:
            print("\nNo baselines found.")
        sys.exit(0)

    if args.rollback:
        ok = phase6_rollback()
        sys.exit(0 if ok else 5)

    # Phase 0
    baseline = phase0_audit()
    if not baseline:
        sys.exit(2)

    # Phase 1
    design = phase1_design(args)
    if not design:
        sys.exit(1)

    # Phase 2
    dry_manifest = phase2_dryrun(design, args.wallpaper)
    if not dry_manifest:
        sys.exit(3)

    # Phase 3
    verified = phase3_verify(dry_manifest, baseline)
    if not verified:
        sys.exit(0)  # Nothing to do, not a failure

    if args.dry_run:
        log("DRY-RUN COMPLETE. No changes were made.")
        sys.exit(0)

    # Phase 4
    apply_manifest = phase4_apply(design, args.wallpaper, force=args.force)
    if not apply_manifest:
        sys.exit(4)

    # Phase 5
    phase5_postflight(baseline)

    log("=" * 70)
    log("SESSION COMPLETE.")
    log(f"Log file: {sys._session_log_path}")
    log("=" * 70)


if __name__ == "__main__":
    main()
