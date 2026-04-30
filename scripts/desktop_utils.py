#!/usr/bin/env python3
"""Shared desktop detection utilities.

Single source of truth for discover_desktop(), imported by ricer.py and
desktop_state_audit.py. Keeping it here prevents the two scripts from
drifting apart on which WMs they recognise.
"""
from __future__ import annotations

import os
import subprocess
from typing import Any


def discover_desktop() -> dict[str, Any]:
    """Detect what DE/WM/compositor is running.

    Returns a dict with keys:
        wm           — one of: kde, gnome, hyprland, sway, i3, bspwm, awesome,
                       qtile, unknown
        session_type — wayland | x11 | unknown
        desktop_env  — XDG_CURRENT_DESKTOP (or DESKTOP_SESSION) value, lowercased

    This is the single source of truth used by both the scripts layer
    (ricer.py, desktop_state_audit.py) and the workflow layer
    (workflow/nodes/audit/detectors.py:detect_wm).
    """
    # Primary env var; fall back to DESKTOP_SESSION when XDG_CURRENT_DESKTOP is unset.
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if not desktop:
        desktop = os.environ.get("DESKTOP_SESSION", "").lower()

    wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
    display = os.environ.get("DISPLAY", "")

    session_type = "x11" if display else "unknown"
    if wayland_display:
        session_type = "wayland"

    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, encoding="utf-8", timeout=3
        )
        proc_lower = result.stdout.lower()
    except (OSError, subprocess.SubprocessError, TimeoutError):
        proc_lower = ""

    wm = "unknown"
    if "plasmashell" in proc_lower or "kwin" in proc_lower:
        wm = "kde"
    elif "gnome-shell" in proc_lower:
        wm = "gnome"
    elif "hyprland" in proc_lower:
        wm = "hyprland"
    elif "sway" in proc_lower:
        wm = "sway"
    elif "i3" in proc_lower:
        wm = "i3"
    elif "bspwm" in proc_lower:
        wm = "bspwm"
    elif "awesome" in proc_lower:
        wm = "awesome"
    elif "qtile" in proc_lower:
        wm = "qtile"

    # XDG/session fallback when ps scan found nothing (e.g. nested session, CI).
    if wm == "unknown":
        if "kde" in desktop or "plasma" in desktop:
            wm = "kde"
        elif "gnome" in desktop:
            wm = "gnome"
        elif "hypr" in desktop:
            wm = "hyprland"

    return {
        "wm": wm,
        "session_type": session_type,
        "desktop_env": desktop,
    }
