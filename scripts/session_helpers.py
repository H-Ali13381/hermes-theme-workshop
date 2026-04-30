"""session_helpers.py — Shared utilities and early phases for deterministic_ricing_session.

Extracted from scripts/deterministic_ricing_session.py to keep that file
within the 300-line budget.  Contains the logger, subprocess wrapper, and
Phases 0-3 of the deterministic ricing protocol.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.session_io import load_design_file  # noqa: E402

RICER_PY = SKILL_DIR / "scripts" / "ricer.py"
AUDIT_PY = SKILL_DIR / "scripts" / "desktop_state_audit.py"
SESSION_LOG_DIR = HOME / ".cache" / "linux-ricing" / "session_logs"

# Module-level session log path; set via set_session_log() before first use.
_session_log_path: str | None = None


def set_session_log(path: str) -> None:
    """Set the active session log file path (called once by main())."""
    global _session_log_path
    _session_log_path = path


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    if _session_log_path:
        with open(_session_log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    log(f"RUN: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
        if result.stdout:
            log(f"STDOUT: {result.stdout.strip()[:200]}")
        if result.stderr:
            log(f"STDERR: {result.stderr.strip()[:200]}")
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (OSError, subprocess.SubprocessError, TimeoutError) as e:
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
    from presets import PRESETS
    if name not in PRESETS:
        log(f"FATAL: preset '{name}' not found. Available: {list(PRESETS.keys())}")
        return None
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

    baselines_dir = HOME / ".cache" / "linux-ricing" / "baselines"
    manifests = sorted(baselines_dir.glob("*_baseline.json"))
    if not manifests:
        log("FATAL: Audit completed but no baseline manifest found.")
        return None

    latest = manifests[-1]
    log(f"BASELINE CAPTURED: {latest}")
    return json.loads(latest.read_text(encoding="utf-8"))


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
        design = load_design_file(path)
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

    rc, out, err = run(cmd)
    if rc != 0:
        log(f"FATAL: Dry-run failed (exit {rc}): {err}")
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        log(f"FATAL: Dry-run output is not valid JSON:\n{out[:500]}")
        return None



# =============================================================================
# PHASE 3: VERIFICATION
# =============================================================================

def phase3_verify(manifest: dict, baseline: dict) -> bool:
    log("=== PHASE 3: VERIFICATION ===")
    changes = manifest.get("changes", [])
    if not changes:
        log("WARNING: Dry-run produced zero changes. Nothing to apply.")
        return False

    print("\n" + "=" * 70 + "\nPROPOSED CHANGES\n" + "=" * 70)
    for change in changes:
        app    = change.get("app", "?")
        action = change.get("action", "?")
        if action == "error":
            print(f"  [{app}] ERROR: {change.get('error')}")
            continue
        if action == "dry-run":
            path = change.get("path") or change.get("config_path") or change.get("profile_path")
            print(f"  [{app}] Would write: {path}")
            for key in ["previous_colorscheme", "previous_kvantum_theme",
                        "previous_theme", "previous_cursor", "previous_profile"]:
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
