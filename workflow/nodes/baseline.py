"""Step 4.5 — Capture immutable rollback baseline before any writes."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone

from ..config import SCRIPTS_DIR
from ..log_setup import get_logger
from ..state import RiceSessionState


def baseline_node(state: RiceSessionState) -> dict:
    """Run desktop_state_audit.py to snapshot current desktop state."""
    log = get_logger("baseline", state)
    log.info("capturing rollback baseline")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    audit_script = SCRIPTS_DIR / "desktop_state_audit.py"

    if not audit_script.exists():
        log.warning("desktop_state_audit.py not found — skipping baseline capture")
        return {"baseline_ts": ts}

    session_dir = state.get("session_dir", "")
    cmd = [sys.executable, str(audit_script)]
    if session_dir:
        cmd += ["--output", f"{session_dir}/baseline_{ts}.json"]

    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=30)

    if result.returncode != 0:
        log.warning("baseline capture exited %s: %s", result.returncode, result.stderr[:200])
        return {"baseline_ts": ts, "errors": [f"baseline_warn: {result.stderr[:200]}"]}

    log.info("baseline captured (ts=%s); rollback with: ricer undo", ts)
    return {"baseline_ts": ts}
