"""Step 1 — Silent machine audit. No LLM. Returns device_profile."""
from __future__ import annotations

import os

from ...state import RiceSessionState
from .detectors import (
    detect_wm, detect_chassis, detect_screens, detect_gpu,
    detect_apps, detect_touchpad, get_current_wallpaper, build_element_queue,
)


def audit_node(state: RiceSessionState) -> dict:
    """Gather device profile silently. No user interaction."""
    print("[Step 1] Auditing your machine...", flush=True)

    wm       = detect_wm()
    chassis  = detect_chassis()
    screens  = detect_screens()
    gpu      = detect_gpu()
    apps     = detect_apps()
    touchpad = detect_touchpad()
    wallpaper = get_current_wallpaper()
    fal_available = bool(os.environ.get("FAL_KEY", "").strip())

    profile = {
        "wm": wm,
        "chassis": chassis,
        "screens": screens,
        "gpu": gpu,
        "has_touchpad": touchpad,
        "apps": apps,
        "fal_available": fal_available,
        "current_wallpaper": wallpaper,
    }

    queue = build_element_queue(wm, apps)

    print(f"  WM: {wm} | Chassis: {chassis} | Screens: {screens} | GPU: {gpu['name'][:40]}")
    print(f"  Installed: {', '.join(k for k, v in apps.items() if v)}")
    print(f"  Element queue ({len(queue)}): {', '.join(queue)}\n")

    return {
        "device_profile": profile,
        "element_queue": queue,
        "current_step": 1,
    }
