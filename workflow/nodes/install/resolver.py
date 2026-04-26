"""install/resolver.py — Maps design choices to package names and installs them."""
from __future__ import annotations

import subprocess

_KVANTUM_PACKAGES = {
    "catppuccin": "kvantum-theme-catppuccin",
    "nordic":     "nordic-kvantum",
}
_CURSOR_PACKAGES = {
    "catppuccin": "catppuccin-cursors-git",
    "breeze":     "breeze",
}
_ICON_PACKAGES = {
    "papirus": "papirus-icon-theme",
    "tela":    "tela-icon-theme-git",
}


def resolve_packages(design: dict, profile: dict) -> list[str]:
    """Return sorted list of packages required by this design."""
    pkgs: set[str] = set()

    _match(design.get("kvantum_theme", ""), _KVANTUM_PACKAGES, pkgs)
    _match(design.get("cursor_theme",   ""), _CURSOR_PACKAGES,  pkgs)
    _match(design.get("icon_theme",     ""), _ICON_PACKAGES,    pkgs)

    return sorted(pkgs)


def install_packages(packages: list[str], errors: list[str]) -> None:
    """Try pacman first, fall back to yay for AUR packages."""
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


def _match(value: str, table: dict[str, str], pkgs: set[str]) -> None:
    for key, pkg in table.items():
        if key in value.lower():
            pkgs.add(pkg)
            return
