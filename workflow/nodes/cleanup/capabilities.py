"""Capability probes for platform-sensitive desktop features."""
from __future__ import annotations

import os
import re
import shutil
import subprocess


def probe_capabilities(state: dict) -> dict:
    """Return a capability report used by cleanup and handoff."""
    profile = state.get("device_profile", {})
    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "").lower()
    if "kde" not in wm and "plasma" not in wm:
        return {}
    report = {
        "desktop": "kde",
        "session_type": os.environ.get("XDG_SESSION_TYPE", ""),
        "plasma_version": _plasma_version(),
        "kwin_compositing_active": _qdbus_bool(["qdbus6", "org.kde.KWin", "/Compositor", "org.kde.kwin.Compositing.active"]),
        "kwin_blur_loaded": _qdbus_bool(["qdbus6", "org.kde.KWin", "/Effects", "org.kde.kwin.Effects.isEffectLoaded", "blur"]),
        "terminals": {name: shutil.which(name) is not None for name in ("kitty", "konsole", "alacritty", "wezterm", "foot")},
    }
    report["features"] = {
        "konsole_transparency": _konsole_transparency_status(report),
        "kitty_transparency": _kitty_transparency_status(report),
    }
    return report


def _run(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def _plasma_version() -> str | None:
    rc, out = _run(["plasmashell", "--version"])
    if rc != 0 or not out:
        return None
    m = re.search(r"([0-9]+(?:\.[0-9]+)+)", out)
    return m.group(1) if m else out


def _qdbus_bool(cmd: list[str]) -> bool | None:
    rc, out = _run(cmd)
    if rc != 0 or not out:
        return None
    val = out.strip().lower()
    if val in {"true", "1", "yes"}:
        return True
    if val in {"false", "0", "no"}:
        return False
    return None


def _version_tuple(version: str | None) -> tuple[int, ...]:
    if not version:
        return ()
    return tuple(int(part) for part in re.findall(r"[0-9]+", version)[:3])


def _konsole_transparency_status(report: dict) -> dict:
    if not report["terminals"].get("konsole"):
        return {"status": "unavailable", "reason": "konsole not installed"}
    if report.get("session_type", "").lower() != "wayland":
        return {"status": "unknown", "reason": "not a native Wayland session; test before claiming support"}
    version = _version_tuple(report.get("plasma_version"))
    if version and version <= (6, 6, 4):
        return {
            "status": "unsupported",
            "reason": "Konsole profile Opacity is known to be ignored on native Plasma Wayland here",
            "workaround": "Use Kitty for transparent terminal designs",
        }
    return {
        "status": "requires-test",
        "reason": "Plasma Wayland Konsole opacity is platform-sensitive; verify visibly in a fresh session",
        "workaround": "Use Kitty if opacity does not apply",
    }


def _kitty_transparency_status(report: dict) -> dict:
    if not report["terminals"].get("kitty"):
        return {"status": "unavailable", "reason": "kitty not installed"}
    return {"status": "supported", "reason": "kitty background_opacity works on Wayland/X11"}