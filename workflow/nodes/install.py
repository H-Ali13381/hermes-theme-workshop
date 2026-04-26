"""Step 5 — Show package list and install after user confirmation."""
from __future__ import annotations

import subprocess
import sys

from langgraph.types import interrupt

from ..state import RiceSessionState


# Packages that ship the kvantum themes
_KVANTUM_THEME_PACKAGES = {
    "catppuccin": "kvantum-theme-catppuccin",
    "nordic": "nordic-kvantum",
}
_CURSOR_PACKAGES = {
    "catppuccin": "catppuccin-cursors-git",
    "breeze": "breeze",
}
_ICON_PACKAGES = {
    "papirus": "papirus-icon-theme",
    "tela": "tela-icon-theme-git",
}


def install_node(state: RiceSessionState) -> dict:
    """Derive required packages, show list, install after confirmation."""
    design = state.get("design", {})
    packages = _resolve_packages(design, state.get("device_profile", {}))

    if not packages:
        print("[Step 5] No extra packages needed.\n")
        return {"packages": [], "current_step": 5}

    pkg_list_text = "\n".join(f"  - {p}" for p in sorted(packages))
    decision = interrupt({
        "step": 5,
        "type": "approval",
        "message": (
            f"The following packages will be installed:\n{pkg_list_text}\n\n"
            "Type 'install' to proceed, 'skip' to skip installation, "
            "or 'cancel' to abort the session."
        ),
    })

    decision_str = str(decision).lower().strip()

    if decision_str == "cancel":
        raise RuntimeError("Session cancelled by user at package installation step.")

    if decision_str == "skip":
        print("[Step 5] Package installation skipped.\n")
        return {"packages": packages, "current_step": 5}

    # Install
    print(f"[Step 5] Installing {len(packages)} package(s)...", flush=True)
    errors = []
    _install_packages(packages, errors)

    if errors:
        print(f"  [WARN] Some packages failed: {errors}")

    print("[Step 5] Installation complete.\n")
    return {"packages": packages, "current_step": 5, "errors": errors}


def _resolve_packages(design: dict, profile: dict) -> list[str]:
    pkgs = set()

    kvantum = design.get("kvantum_theme", "")
    for key, pkg in _KVANTUM_THEME_PACKAGES.items():
        if key in kvantum.lower():
            pkgs.add(pkg)
            break

    cursor = design.get("cursor_theme", "")
    for key, pkg in _CURSOR_PACKAGES.items():
        if key in cursor.lower():
            pkgs.add(pkg)
            break

    icons = design.get("icon_theme", "")
    for key, pkg in _ICON_PACKAGES.items():
        if key in icons.lower():
            pkgs.add(pkg)
            break

    return sorted(pkgs)


def _install_packages(packages: list[str], errors: list[str]) -> None:
    # Try pacman first, then yay for AUR packages
    for pkg in packages:
        rc = subprocess.run(
            ["sudo", "pacman", "-S", "--noconfirm", "--needed", pkg],
            capture_output=True, text=True,
        ).returncode
        if rc != 0:
            rc2 = subprocess.run(
                ["yay", "-S", "--noconfirm", "--needed", pkg],
                capture_output=True, text=True,
            ).returncode
            if rc2 != 0:
                errors.append(pkg)
