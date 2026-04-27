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


def install_packages(packages: list[str], errors: list[str], sudo_password: str = "") -> None:
    """Install packages. Uses sudo_password if provided, else sudo -n (cached), then yay."""
    for pkg in packages:
        if not _try_install_pkg(pkg, sudo_password):
            errors.append(pkg)


def can_sudo_noninteractive() -> bool:
    """Return True if sudo -n true succeeds (cached credentials in this session)."""
    return subprocess.run(
        ["sudo", "-n", "true"], capture_output=True, timeout=5
    ).returncode == 0


def _try_install_pkg(pkg: str, sudo_password: str) -> bool:
    """Try pacman (with password or -n), then yay. Returns True if installed."""
    if sudo_password:
        try:
            r = subprocess.run(
                ["sudo", "-S", "-p", "", "-k", "pacman", "-S", "--noconfirm", "--needed", pkg],
                input=sudo_password + "\n",
                capture_output=True, text=True, timeout=300,
            )
            if r.returncode == 0:
                return True
        except subprocess.TimeoutExpired:
            return False

    try:
        r = subprocess.run(
            ["sudo", "-n", "pacman", "-S", "--noconfirm", "--needed", pkg],
            capture_output=True, text=True, timeout=300,
        )
        if r.returncode == 0:
            return True
    except subprocess.TimeoutExpired:
        return False

    try:
        r = subprocess.run(
            ["yay", "-S", "--noconfirm", "--needed", pkg],
            capture_output=True, text=True, timeout=300,
        )
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def verify_installed(packages: list[str]) -> list[str]:
    """Return packages not yet in the local pacman database (no sudo needed)."""
    return [
        p for p in packages
        if subprocess.run(["pacman", "-Q", p], capture_output=True).returncode != 0
    ]


def _match(value: str, table: dict[str, str], pkgs: set[str]) -> None:
    for key, pkg in table.items():
        if key in value.lower():
            pkgs.add(pkg)
            return
