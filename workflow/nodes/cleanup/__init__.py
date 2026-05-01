"""Step 7 — Sweep configs for syntax errors and reload services."""
from __future__ import annotations

from pathlib import Path

from ...state import RiceSessionState
from .capabilities import probe_capabilities
from .effective_state import audit_effective_state
from .kde_finalize import finalize_kde
from .visual_artifacts import capture_visual_artifacts
from .reloader import validate_file, reload_waybar, reload_polybar, reload_dunst, reload_mako, reload_swaync, reload_hyprland


def cleanup_node(state: RiceSessionState) -> dict:
    """Validate written configs and reload affected services."""
    print("[Step 7] Running cleanup...", flush=True)
    errors:   list[str] = []
    reloaded: list[str] = []
    cleanup_actions: list[dict] = []

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

    if "bar" in elements:
        bar_element = next(
            (r.get("element", "") for r in impl_log
             if r.get("element", "").split(":")[0] == "bar"),
            "bar:waybar",
        )
        bar_provider = bar_element.split(":")[-1] if ":" in bar_element else "waybar"
        if bar_provider == "polybar":
            reload_polybar(reloaded, errors)
        else:
            reload_waybar(reloaded, errors)
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

    cleanup_actions.extend(finalize_kde(state, reloaded, errors))
    effective_state = audit_effective_state(state)
    capability_report = probe_capabilities(state)
    visual_artifacts = capture_visual_artifacts(state)

    print(f"  Reloaded: {', '.join(reloaded) if reloaded else 'none'}")
    print(f"  Errors: {len(errors)}\n")

    result: dict = {"current_step": 7, "cleanup_actions": cleanup_actions}
    if effective_state:
        result["effective_state"] = effective_state
    if capability_report:
        result["capability_report"] = capability_report
    if visual_artifacts:
        result["visual_artifacts"] = visual_artifacts
    if errors:
        result["errors"] = errors
    return result
