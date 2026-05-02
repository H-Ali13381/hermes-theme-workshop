"""implement/apply.py — Applies one element by calling ricer.py materializers directly."""
from __future__ import annotations

import sys

from ...config import SCRIPTS_DIR
from ...log_setup import get_logger

# Ensure scripts/ is importable regardless of cwd — same bootstrap ricer.py uses.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ricer import materialize              # noqa: E402
from core.discovery import discover_apps   # noqa: E402
from materializers import APP_MATERIALIZERS  # noqa: E402


def apply_element(element: str, design: dict, session_dir: str) -> dict:
    """Map element name → ricer.py materializer and call it directly as a Python API."""
    materializer = _element_to_materializer(element)
    if materializer is None:
        return {"success": False, "error": f"unsupported element: {element}"}

    if materializer not in APP_MATERIALIZERS:
        return {"success": False, "error": f"unknown materializer: {materializer}"}

    apps = discover_apps()
    if materializer not in apps:
        return {"success": False, "error": f"materializer not detected on this system: {materializer}"}

    try:
        manifest = materialize(design, apps={materializer: apps[materializer]})
        return {"success": True, "manifest": manifest}
    except Exception as e:  # noqa: BLE001
        get_logger("implement.apply").exception("materializer error: %s", e)
        return {"success": False, "error": str(e)}


# Elements where category:provider doesn't map directly to the materializer key.
_PROVIDER_REMAPS: dict[str, str] = {
    "look_and_feel:kde":      "lnf",
    "lock_screen:kde":        "kde_lockscreen",
    "window_decorations:gnome": "gnome_shell",
    "lock_screen:gnome":      "gnome_lockscreen",
}


def _element_to_materializer(element: str) -> str | None:
    """Translate workflow element names to ricer.py APP_MATERIALIZERS keys."""
    if element in _PROVIDER_REMAPS:
        return _PROVIDER_REMAPS[element]

    if ":" in element:
        category, provider = element.split(":", 1)
        if category in {
            "terminal", "bar", "launcher", "notifications", "shell_prompt", "widgets",
            "window_decorations", "lock_screen",
        }:
            return provider
        return None

    aliases = {
        "gtk_theme":     "gtk",
        "fastfetch":     "fastfetch",
        "plasma_theme":  "plasma_theme",
        "cursor_theme":  "cursor",
        "icon_theme":    "icon_theme",
        "kvantum_theme": "kvantum",
    }
    return aliases.get(element)
