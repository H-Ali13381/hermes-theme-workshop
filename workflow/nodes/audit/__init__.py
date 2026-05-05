"""Step 1 — Silent machine audit. No LLM. Returns device_profile."""
from __future__ import annotations

from ...config import UNSUPPORTED_DESKTOP_MESSAGE, resolve_env_secret
from ...log_setup import get_logger
from ...state import RiceSessionState
from .detectors import (
    detect_wm, detect_session_type, detect_chassis, detect_screens, detect_screen_geometries, detect_gpu,
    detect_apps, detect_touchpad, get_current_wallpaper, build_element_queue,
    desktop_recipe_for_wm,
)


def audit_node(state: RiceSessionState) -> dict:
    """Gather device profile silently. No user interaction."""
    log = get_logger("audit", state)
    log.info("auditing machine")

    wm           = detect_wm()
    session_type = detect_session_type()
    recipe       = desktop_recipe_for_wm(wm)
    chassis      = detect_chassis()
    screen_geometries = detect_screen_geometries()
    screens      = len(screen_geometries) if screen_geometries else detect_screens()
    gpu          = detect_gpu()
    apps         = detect_apps()
    touchpad     = detect_touchpad()
    wallpaper    = get_current_wallpaper()
    fal_available = bool(resolve_env_secret("FAL_KEY"))

    profile = {
        "wm": wm,
        "session_type": session_type,
        "desktop_recipe": recipe,
        "chassis": chassis,
        "screens": screens,
        "screen_geometries": screen_geometries,
        "gpu": gpu,
        "has_touchpad": touchpad,
        "apps": apps,
        "fal_available": fal_available,
        "current_wallpaper": wallpaper,
    }

    existing_queue = state.get("element_queue", [])
    queue = existing_queue or ([] if recipe == "other" else build_element_queue(wm, apps))

    if recipe == "other":
        profile["unsupported_message"] = UNSUPPORTED_DESKTOP_MESSAGE

    log.info(
        "WM=%s recipe=%s chassis=%s screens=%s gpu=%s",
        wm, recipe, chassis, screens, gpu["name"][:40],
    )
    log.info("installed: %s", ", ".join(k for k, v in apps.items() if v))
    if recipe == "other":
        log.warning(UNSUPPORTED_DESKTOP_MESSAGE)
    else:
        log.info("element queue (%d): %s", len(queue), ", ".join(queue))

    result = {
        "device_profile": profile,
        "current_step": 1,
    }
    if not existing_queue and recipe != "other":
        result["element_queue"] = queue
    return result
