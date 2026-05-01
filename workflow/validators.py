"""workflow/validators.py — Workflow stage gate conditions.

Pure functions — no state.  ``routing.py`` calls one function per routing
decision so no domain knowledge leaks into the graph wiring.
"""
from __future__ import annotations

from pathlib import Path

from .config import (
    BASE_REQUIRED_KEYS,
    PALETTE_SLOTS,
    RECIPE_REQUIRED_KEYS,
    SUPPORTED_DESKTOP_RECIPES,
    UNSUPPORTED_DESKTOP_MESSAGE,
)

MIN_PLAN_HTML_BYTES = 500


# ── Step 2 — Explore ────────────────────────────────────────────────────

def direction_confirmed(design: dict) -> bool:
    """True when the LLM has committed to a creative direction."""
    return bool(design.get("stance") or design.get("name_hypothesis"))


# ── Step 3 — Refine ─────────────────────────────────────────────────────

def design_complete(design: dict, profile: dict | None = None) -> tuple[bool, str]:
    """True when design has base keys, recipe keys, palette slots, and valid hex values."""
    if not design:
        return False, "design is empty"

    recipe = (profile or {}).get("desktop_recipe", "kde")
    if recipe not in SUPPORTED_DESKTOP_RECIPES:
        return False, UNSUPPORTED_DESKTOP_MESSAGE

    required_keys = BASE_REQUIRED_KEYS + RECIPE_REQUIRED_KEYS[recipe]
    missing_keys = [k for k in required_keys if k not in design]
    if missing_keys:
        return False, f"missing keys for {recipe} recipe: {missing_keys}"

    palette = design.get("palette", {})
    missing_slots = [k for k in PALETTE_SLOTS if k not in palette]
    if missing_slots:
        return False, f"missing palette slots: {missing_slots}"

    bad_hex = [
        slot for slot, val in palette.items()
        if not (isinstance(val, str) and val.startswith("#") and len(val) == 7)
    ]
    if bad_hex:
        return False, f"invalid hex values for: {bad_hex}"

    if recipe == "kde":
        ok, reason = _kde_creativity_complete(design)
        if not ok:
            return False, reason

    return True, ""


def _kde_creativity_complete(design: dict) -> tuple[bool, str]:
    """KDE must follow the user's vision with non-boilerplate, implementable chrome."""
    banned = {"default", "stock", "breeze", "standard", "unchanged", "normal", "generic"}

    originality = design.get("originality_strategy")
    if not isinstance(originality, dict):
        return False, "kde originality_strategy must describe user-specific non-default moves"
    moves = originality.get("non_default_moves")
    if not isinstance(moves, list) or len(moves) < 3:
        return False, "kde originality_strategy needs at least 3 non_default_moves"
    if not originality.get("vision_alignment"):
        return False, "kde originality_strategy must explain vision_alignment"
    moves_text = " ".join(str(v).lower() for v in moves)
    if any(word in moves_text for word in banned):
        return False, "kde originality_strategy contains boilerplate/default moves"

    chrome = design.get("chrome_strategy")
    if not isinstance(chrome, dict):
        return False, "kde chrome_strategy must declare implementable window/terminal/panel chrome"
    if not chrome.get("method") or not chrome.get("implementation_targets"):
        return False, "kde chrome_strategy needs method and implementation_targets"

    panel = design.get("panel_layout")
    if panel is not None:
        if not isinstance(panel, dict):
            return False, "kde panel_layout must be an object when present"
        panel_text = " ".join(str(v).lower() for v in panel.values())
        if any(word in panel_text for word in banned):
            return False, "kde panel_layout may not preserve stock/default Plasma toolbar aesthetics"

    widgets = design.get("widget_layout", [])
    if widgets:
        if not isinstance(widgets, list):
            return False, "kde widget_layout must be a list when present"
        for i, widget in enumerate(widgets, start=1):
            if not isinstance(widget, dict):
                return False, f"kde widget_layout[{i}] must be an object"
            missing = [k for k in ("name", "position", "data", "visual") if not widget.get(k)]
            if missing:
                return False, f"kde widget_layout[{i}] missing fields: {missing}"
    return True, ""


# ── Step 4 — Plan ───────────────────────────────────────────────────────

def plan_ready(path_str: str) -> tuple[bool, str]:
    """True when the plan HTML file exists and has real content."""
    if not path_str:
        return False, "no path set"

    p = Path(path_str)
    if not p.exists():
        return False, f"file not found: {p}"

    size = p.stat().st_size
    if size < MIN_PLAN_HTML_BYTES:
        return False, f"file too small ({size}B < {MIN_PLAN_HTML_BYTES}B)"

    return True, ""


# ── Step 6 — Implement / Craft ──────────────────────────────────────────

def implement_done(element_queue: list) -> bool:
    """True when all elements have been processed."""
    return not element_queue


def is_craft_element(element: str) -> bool:
    """True when *element* should be routed to craft_node instead of implement_node.

    Imported lazily to avoid a circular-import chain — craft.frameworks does
    not import from workflow.validators.
    """
    from .nodes.craft.frameworks import is_craft_element as _is_craft  # noqa: PLC0415
    return _is_craft(element)


# Backward-compatible class wrapper — tests import WorkflowValidator directly.
class WorkflowValidator:
    """Thin wrapper delegating to module-level functions."""
    MIN_PLAN_HTML_BYTES = MIN_PLAN_HTML_BYTES
    direction_confirmed = staticmethod(direction_confirmed)
    design_complete     = staticmethod(design_complete)
    plan_ready          = staticmethod(plan_ready)
    implement_done      = staticmethod(implement_done)
    is_craft_element    = staticmethod(is_craft_element)


# Legacy singleton kept for backward compatibility.
validator = WorkflowValidator()
