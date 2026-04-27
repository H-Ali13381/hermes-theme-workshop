"""Step 7 — Sweep configs for syntax errors and reload services."""
from __future__ import annotations

from pathlib import Path

from ...state import RiceSessionState
from .reloader import validate_file, reload_waybar, reload_dunst, reload_mako, reload_swaync, reload_hyprland


def cleanup_node(state: RiceSessionState) -> dict:
    """Validate written configs and reload affected services."""
    print("[Step 7] Running cleanup...", flush=True)
    errors:   list[str] = []
    reloaded: list[str] = []

    impl_log = state.get("impl_log", [])
    wm       = state.get("device_profile", {}).get("wm", "")

    # Validate every config file that was written during Step 6
    written_files = [
        target
        for record in impl_log
        for target in record.get("spec", {}).get("targets", [])
    ]
    for fpath in written_files:
        p = Path(fpath).expanduser()
        if not p.exists():
            continue
        ok, err = validate_file(p)
        if not ok:
            errors.append(f"syntax error in {p.name}: {err}")
            print(f"  [WARN] {err}")

    # Reload only the services that were actually changed
    elements = {r.get("element", "").split(":")[0] for r in impl_log}

    if "bar" in elements: reload_waybar(reloaded, errors)
    if "notifications" in elements:
        # Determine which notifier was actually implemented; default to dunst.
        notif_element = next(
            (r.get("element", "") for r in impl_log
             if r.get("element", "").split(":")[0] == "notifications"),
            "notifications:dunst",
        )
        notifier = notif_element.split(":")[-1] if ":" in notif_element else "dunst"
        if notifier == "mako":
            reload_mako(reloaded, errors)
        elif notifier == "swaync":
            reload_swaync(reloaded, errors)
        else:
            reload_dunst(reloaded, errors)
    if "window_decorations" in elements and "hypr" in wm:
        reload_hyprland(reloaded, errors)
    if "gtk_theme"          in elements:
        print("  GTK: changes apply to newly opened apps (no live reload)")
        reloaded.append("gtk")

    print(f"  Reloaded: {', '.join(reloaded) if reloaded else 'none'}")
    print(f"  Errors: {len(errors)}\n")

    return {"current_step": 7, "errors": errors}
