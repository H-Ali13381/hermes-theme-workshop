"""Step 4.5 — Capture immutable rollback baseline before any writes."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime

from ..config import SCRIPTS_DIR
from ..state import RiceSessionState


def baseline_node(state: RiceSessionState) -> dict:
    """Run desktop_state_audit.py to snapshot current desktop state."""
    print("[Step 4.5] Capturing rollback baseline...", flush=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    audit_script = SCRIPTS_DIR / "desktop_state_audit.py"

    if not audit_script.exists():
        print("  [WARN] desktop_state_audit.py not found — skipping baseline capture")
        return {"baseline_ts": ts, "current_step": 5}

    session_dir = state.get("session_dir", "")
    cmd = [sys.executable, str(audit_script)]
    if session_dir:
        cmd += ["--output", f"{session_dir}/baseline_{ts}.json"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        print(f"  [WARN] Baseline capture exited {result.returncode}: {result.stderr[:200]}")
        return {"baseline_ts": ts, "current_step": 5, "errors": [f"baseline_warn: {result.stderr[:200]}"]}

    print(f"  Baseline captured (ts={ts}). Rollback with: ricer undo\n")
    return {"baseline_ts": ts, "current_step": 5}
