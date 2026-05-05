"""Step 5 — Show package list and install after user confirmation."""
from __future__ import annotations

import os

try:
    from langgraph.types import interrupt
except ImportError:  # LangGraph not installed (e.g. during unit tests)
    interrupt = None  # type: ignore[assignment]

from ...log_setup import get_logger
from ...session import append_step, append_item
from ...state import RiceSessionState
from .resolver import resolve_packages, install_packages, can_sudo_noninteractive


def install_node(state: RiceSessionState) -> dict:
    """Derive required packages, show list, install after confirmation."""
    log = get_logger("install", state)
    design      = state.get("design", {})
    profile     = state.get("device_profile", {})
    session_dir = state.get("session_dir", "")
    packages = resolve_packages(design, profile)

    if not packages:
        log.info("no extra packages needed")
        append_step(session_dir, 5, "no extra packages needed")
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
        log.info("package installation skipped")
        append_step(session_dir, 5, f"skipped ({len(packages)} package(s) not installed)")
        return {"packages": packages, "current_step": 5}

    if decision_str != "install":
        log.warning("unrecognised response '%s' — skipping installation", decision_str)
        append_step(session_dir, 5, f"unrecognised response {decision_str!r} — skipped")
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

    log.info("installing %d package(s)", len(packages))
    errors: list[str] = []
    install_packages(packages, errors, sudo_password=str(sudo_password) if sudo_password else "")

    if errors:
        log.warning("some packages failed: %s", errors)

    log.info("installation complete")
    note = f"installed {len(packages)} package(s)"
    if errors:
        note += f"; {len(errors)} failed"
        for err in errors:
            append_item(session_dir, f"install error: {err}")
    append_step(session_dir, 5, note)
    result: dict = {"packages": packages, "current_step": 5}
    if errors:
        result["errors"] = errors
    return result
