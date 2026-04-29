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
import sys
import textwrap
from datetime import datetime
from pathlib import Path

from session_helpers import (
    log, run, ensure_deps, SESSION_LOG_DIR, HOME, RICER_PY, set_session_log,
    phase0_audit, phase1_design, phase2_dryrun, phase3_verify,
)
from session_phases import phase4_apply, phase5_postflight, phase6_rollback


# =============================================================================
# PHASE -1: BACKUP RECOMMENDATION
# =============================================================================

def phase_minus1_backup_prompt() -> bool:
    """Prompt user to back up before starting. Returns True if user confirms backup is done."""
    print(textwrap.dedent("""
        ╔══════════════════════════════════════════════════════════════════════╗
        ║                      PRE-RICING BACKUP RECOMMENDATION                     ║
        ╠══════════════════════════════════════════════════════════════════════╣
        ║  Before applying themes, ensure you have a backup of your configs:       ║
        ║                                                                      ║
        ║  OPTION A — GitHub (recommended):                                       ║
        ║    • Push to your dotfiles repo (if set up):                            ║
        ║      git -C ~/.dotfiles add -u && git -C ~/.dotfiles commit -m "pre-ricer snapshot"  ║
        ║                                                                      ║
        ║  OPTION B — Full system backup:                                         ║
        ║    • Timeshift, rsync, or your preferred backup solution             ║
        ║                                                                      ║
        ║  OPTION C — Skip (not recommended):                                     ║
        ║    • ricer has its own pre-flight backup system                         ║
        ║    • But GitHub gives you longer-term protection                       ║
        ╚══════════════════════════════════════════════════════════════════════╝
    """))
    response = input("\nHave you backed up your configs? [y/n/skip]: ").strip().lower()
    if response in ("y", "yes"):
        print("Proceeding with backup confirmed.")
        return True
    elif response in ("s", "skip"):
        print("Skipping external backup. Proceeding with ricer's internal backup system.")
        return True
    else:
        print("Please back up first, then run this script again.")
        return False


# Phases 0-6 are imported from session_helpers / session_phases above.


# =============================================================================
# MAIN
# =============================================================================

# NOTE: phases 4-6 were previously defined here; they are now imported from
# session_phases.py. Do not define them here to avoid a shadowing conflict.

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
    session_log = str(SESSION_LOG_DIR / f"session_{log_ts}.log")
    set_session_log(session_log)

    log("=" * 70)
    log("DETERMINISTIC RICING SESSION STARTED")
    log(f"Args: preset={args.preset}, design={args.design}, wallpaper={args.wallpaper}, dry_run={args.dry_run}, rollback={args.rollback}")
    log("=" * 70)

    if not ensure_deps():
        sys.exit(1)

    if args.status:
        run([sys.executable, str(RICER_PY), "status"])
        baselines_dir = HOME / ".cache" / "linux-ricing" / "baselines"
        manifests = sorted(baselines_dir.glob("*_baseline.json"))
        if manifests:
            print(f"\nLast baseline: {manifests[-1]}")
        else:
            print("\nNo baselines found.")
        sys.exit(0)

    if args.rollback:
        ok = phase6_rollback()
        sys.exit(0 if ok else 5)

    # Phase -1: Backup prompt
    if not phase_minus1_backup_prompt():
        sys.exit(1)

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
    log(f"Log file: {session_log}")
    log("=" * 70)


if __name__ == "__main__":
    main()
