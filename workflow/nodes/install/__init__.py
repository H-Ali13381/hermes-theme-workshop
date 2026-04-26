"""Step 5 — Show package list and install after user confirmation."""
from __future__ import annotations

from langgraph.types import interrupt

from ...state import RiceSessionState
from .resolver import resolve_packages, install_packages


def install_node(state: RiceSessionState) -> dict:
    """Derive required packages, show list, install after confirmation."""
    design   = state.get("design", {})
    profile  = state.get("device_profile", {})
    packages = resolve_packages(design, profile)

    if not packages:
        print("[Step 5] No extra packages needed.\n")
        return {"packages": [], "current_step": 5}

    pkg_list_text = "\n".join(f"  - {p}" for p in packages)
    decision = interrupt({
        "step": 5,
        "type": "approval",
        "message": (
            f"The following packages will be installed:\n{pkg_list_text}\n\n"
            "Type 'install' to proceed, 'skip' to skip, or 'cancel' to abort."
        ),
    })

    decision_str = str(decision).lower().strip()

    if decision_str == "cancel":
        raise RuntimeError("Session cancelled by user at package installation step.")

    if decision_str == "skip":
        print("[Step 5] Package installation skipped.\n")
        return {"packages": packages, "current_step": 5}

    print(f"[Step 5] Installing {len(packages)} package(s)...", flush=True)
    errors: list[str] = []
    install_packages(packages, errors)

    if errors:
        print(f"  [WARN] Some packages failed: {errors}")

    print("[Step 5] Installation complete.\n")
    result: dict = {"packages": packages, "current_step": 5}
    if errors:
        result["errors"] = errors
    return result
