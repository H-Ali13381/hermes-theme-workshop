"""install/resolver.py — Maps design choices to package names and installs them."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

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

    if profile.get("desktop_recipe") == "kde" and _design_needs_widgets(design):
        framework = _widget_framework_for(design, profile)
        if framework == "quickshell" and not (shutil.which("quickshell") or shutil.which("qs")):
            pkgs.add("quickshell")
        elif framework == "eww" and not shutil.which("eww"):
            pkgs.add("eww")

    return sorted(pkgs)


def detect_distro() -> str:
    """Return a normalised distro family string from /etc/os-release.

    Returns one of: 'arch', 'debian', 'fedora', 'suse', 'unknown'.
    """
    try:
        text = Path("/etc/os-release").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unknown"
    ids: list[str] = []
    for line in text.splitlines():
        if line.startswith("ID=") or line.startswith("ID_LIKE="):
            val = line.split("=", 1)[1].strip().strip('"').lower()
            ids.extend(val.split())
    for d in ids:
        if d in {"arch", "manjaro", "endeavouros", "garuda"}:
            return "arch"
        if d in {"debian", "ubuntu", "linuxmint", "pop", "elementary"}:
            return "debian"
        if d in {"fedora", "rhel", "centos", "rocky", "alma"}:
            return "fedora"
        if d in {"opensuse", "suse", "opensuse-leap", "opensuse-tumbleweed"}:
            return "suse"
    return "unknown"


def install_packages(packages: list[str], errors: list[str], sudo_password: str = "") -> None:
    """Install packages. Dispatches to the appropriate package manager for the running distro."""
    distro = detect_distro()
    for pkg in packages:
        if not _try_install_pkg(pkg, sudo_password, distro):
            errors.append(pkg)


def can_sudo_noninteractive() -> bool:
    """Return True if sudo -n true succeeds (cached credentials in this session)."""
    try:
        return subprocess.run(
            ["sudo", "-n", "true"], capture_output=True, timeout=5
        ).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def _try_install_pkg(pkg: str, sudo_password: str, distro: str) -> bool:
    """Try to install *pkg* using the distro-appropriate package manager."""
    if distro == "arch":
        return _try_arch(pkg, sudo_password)
    if distro == "debian":
        return _try_apt(pkg, sudo_password)
    if distro == "fedora":
        return _try_dnf(pkg, sudo_password)
    if distro == "suse":
        return _try_zypper(pkg, sudo_password)
    # Unknown distro — log and bail
    print(f"[install] Unknown distro; cannot install '{pkg}'. "
          "Only Arch, Debian/Ubuntu, Fedora, and openSUSE are supported.")
    return False


def _sudo_run(cmd: list[str], sudo_password: str) -> bool:
    """Run a sudo command, injecting password via stdin when provided."""
    if sudo_password:
        try:
            r = subprocess.run(
                ["sudo", "-S", "-p", "", "-k"] + cmd,
                input=sudo_password + "\n",
                capture_output=True, text=True, encoding="utf-8", timeout=300,
            )
            return r.returncode == 0
        except subprocess.TimeoutExpired:
            return False
    try:
        r = subprocess.run(
            ["sudo", "-n"] + cmd,
            capture_output=True, text=True, encoding="utf-8", timeout=300,
        )
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def _try_arch(pkg: str, sudo_password: str) -> bool:
    if _sudo_run(["pacman", "-S", "--noconfirm", "--needed", pkg], sudo_password):
        return True
    if shutil.which("yay"):
        try:
            return subprocess.run(
                ["yay", "-S", "--noconfirm", "--needed", pkg],
                capture_output=True, text=True, encoding="utf-8", timeout=300,
            ).returncode == 0
        except subprocess.TimeoutExpired:
            pass
    return False


def _try_apt(pkg: str, sudo_password: str) -> bool:
    return _sudo_run(["apt-get", "install", "-y", pkg], sudo_password)


def _try_dnf(pkg: str, sudo_password: str) -> bool:
    mgr = "dnf" if shutil.which("dnf") else "yum"
    return _sudo_run([mgr, "install", "-y", pkg], sudo_password)


def _try_zypper(pkg: str, sudo_password: str) -> bool:
    return _sudo_run(["zypper", "--non-interactive", "install", pkg], sudo_password)


def verify_installed(packages: list[str]) -> list[str]:
    """Return packages not yet installed (distro-aware check)."""
    distro = detect_distro()
    missing = []
    for p in packages:
        if distro == "arch":
            ok = subprocess.run(["pacman", "-Q", p], capture_output=True, timeout=30).returncode == 0
        elif distro == "debian":
            ok = subprocess.run(["dpkg", "-s", p], capture_output=True, timeout=30).returncode == 0
        elif distro == "fedora":
            ok = subprocess.run(["rpm", "-q", p], capture_output=True, timeout=30).returncode == 0
        elif distro == "suse":
            ok = subprocess.run(["rpm", "-q", p], capture_output=True, timeout=30).returncode == 0
        else:
            ok = bool(shutil.which(p))
        if not ok:
            missing.append(p)
    return missing


def _match(value: str, table: dict[str, str], pkgs: set[str]) -> None:
    for key, pkg in table.items():
        if key in value.lower():
            pkgs.add(pkg)
            return


def _design_needs_widgets(design: dict) -> bool:
    """True when the design implies a custom widget framework (eww/quickshell)."""
    if design.get("widget_layout"):
        return True
    chrome = design.get("chrome_strategy", {})
    if not isinstance(chrome, dict):
        return False
    method = str(chrome.get("method", "")).lower()
    targets = " ".join(str(t).lower() for t in chrome.get("implementation_targets", []))
    return any(
        term in method or term in targets
        for term in ("eww", "quickshell", "overlay", "frame", "border")
    )


def _widget_framework_for(design: dict, profile: dict) -> str:
    """Mirror of refine._default_widget_element, returning the framework name only.

    Honors explicit eww/quickshell mentions in the design's implementation_targets;
    otherwise picks Quickshell on Hyprland and KDE Wayland, EWW elsewhere.
    """
    chrome = design.get("chrome_strategy", {}) if isinstance(design, dict) else {}
    targets = " ".join(str(t).lower() for t in chrome.get("implementation_targets", [])) if isinstance(chrome, dict) else ""
    if "widgets:quickshell" in targets:
        return "quickshell"
    if "widgets:eww" in targets:
        return "eww"
    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "").lower()
    session = str(profile.get("session_type") or "").lower()
    if "hypr" in wm:
        return "quickshell"
    if ("kde" in wm or "plasma" in wm) and session == "wayland":
        return "quickshell"
    return "eww"
