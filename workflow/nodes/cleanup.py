"""Step 7 — Sweep configs for syntax errors, verify services reloaded."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ..config import SCRIPTS_DIR
from ..state import RiceSessionState


def cleanup_node(state: RiceSessionState) -> dict:
    """Validate written configs and reload services."""
    print("[Step 7] Running cleanup...", flush=True)
    errors = []
    reloaded = []

    impl_log = state.get("impl_log", [])
    profile = state.get("device_profile", {})
    wm = profile.get("wm", "")

    # Collect all target files from impl_log
    written_files: list[str] = []
    for record in impl_log:
        spec = record.get("spec", {})
        written_files.extend(spec.get("targets", []))

    # Validate each written file
    for fpath in written_files:
        p = Path(fpath).expanduser()
        if not p.exists():
            continue
        ok, err = _validate_file(p)
        if not ok:
            errors.append(f"syntax error in {p.name}: {err}")
            print(f"  [WARN] {err}")

    # Reload services based on what was implemented
    elements = {r.get("element", "").split(":")[0] for r in impl_log}

    if "bar" in elements:
        _reload_waybar(reloaded, errors)

    if "notifications" in elements:
        _reload_dunst(reloaded, errors)

    if "window_decorations" in elements and "hypr" in wm:
        _reload_hyprland(reloaded, errors)

    if "gtk_theme" in elements:
        print("  GTK: changes apply to newly opened apps (no live reload)")
        reloaded.append("gtk_notice")

    print(f"  Reloaded: {', '.join(reloaded) if reloaded else 'none'}")
    print(f"  Errors: {len(errors)}\n")

    return {"current_step": 7, "errors": errors}


def _validate_file(path: Path) -> tuple[bool, str]:
    if path.suffix in (".json", ".jsonc"):
        try:
            import re
            content = path.read_text()
            content = re.sub(r"//.*", "", content)
            json.loads(content)
        except Exception as e:
            return False, f"{path.name}: {e}"
    return True, ""


def _reload_waybar(reloaded: list, errors: list) -> None:
    r = subprocess.run(["pkill", "-SIGUSR2", "waybar"], capture_output=True)
    if r.returncode == 0:
        reloaded.append("waybar")
    else:
        subprocess.run(["pkill", "waybar"], capture_output=True)
        subprocess.Popen(["waybar"])
        reloaded.append("waybar(restart)")


def _reload_dunst(reloaded: list, errors: list) -> None:
    subprocess.run(["pkill", "dunst"], capture_output=True)
    subprocess.Popen(["dunst"])
    reloaded.append("dunst")


def _reload_hyprland(reloaded: list, errors: list) -> None:
    r = subprocess.run(
        ["hyprctl", "reload"], capture_output=True, text=True, timeout=10
    )
    if r.returncode == 0:
        reloaded.append("hyprland")
    else:
        errors.append(f"hyprctl reload failed: {r.stderr[:100]}")
