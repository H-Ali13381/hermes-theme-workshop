"""Step 5 — Show package list and install after user confirmation."""
from __future__ import annotations

import os

try:
    from langgraph.types import interrupt
except ImportError:  # LangGraph not installed (e.g. during unit tests)
    interrupt = None  # type: ignore[assignment]

from ...state import RiceSessionState
from .resolver import resolve_packages, install_packages, can_sudo_noninteractive


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

    if decision_str != "install":
        print(f"[Step 5] Unrecognised response '{decision_str}' — skipping installation.\n")
        return {"packages": packages, "current_step": 5}

    # Acquire sudo password — 3-tier escalation
    sudo_password = os.environ.get("SUDO_PASSWORD", "")          # Tier 1: env var

    if not sudo_password and not can_sudo_noninteractive():       # Tier 2: cached creds
        # Tier 3: escalate — workflow pauses, run.py prompts via getpass (masked)
        sudo_password = interrupt({
            "step": 5,
            "type": "sudo_password",
            "message": (
                "Package installation requires sudo.\n\n"
                "Enter your sudo password (or press Enter to attempt without):"
            ),
        })

    print(f"[Step 5] Installing {len(packages)} package(s)...", flush=True)
    errors: list[str] = []
    install_packages(packages, errors, sudo_password=str(sudo_password) if sudo_password else "")

    if errors:
        print(f"  [WARN] Some packages failed: {errors}")

    print("[Step 5] Installation complete.\n")
    result: dict = {"packages": packages, "current_step": 5}
    if errors:
        result["errors"] = errors
    return result
