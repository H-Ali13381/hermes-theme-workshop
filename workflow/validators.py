"""workflow/validators.py — Workflow stage validation.

A single WorkflowValidator class encapsulates every gate condition in the
pipeline. graph.py imports one object and calls one method per routing
decision — no domain knowledge leaks into the graph wiring.
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


class WorkflowValidator:
    MIN_PLAN_HTML_BYTES = 500

    # ── Step 2 — Explore ────────────────────────────────────────────────────

    def direction_confirmed(self, design: dict) -> bool:
        """True when the LLM has committed to a creative direction."""
        return bool(design.get("stance") or design.get("name_hypothesis"))

    # ── Step 3 — Refine ─────────────────────────────────────────────────────

    def design_complete(self, design: dict, profile: dict | None = None) -> tuple[bool, str]:
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

        return True, ""

    # ── Step 4 — Plan ───────────────────────────────────────────────────────

    def plan_ready(self, path_str: str) -> tuple[bool, str]:
        """True when the plan HTML file exists and has real content."""
        if not path_str:
            return False, "no path set"

        p = Path(path_str)
        if not p.exists():
            return False, f"file not found: {p}"

        size = p.stat().st_size
        if size < self.MIN_PLAN_HTML_BYTES:
            return False, f"file too small ({size}B < {self.MIN_PLAN_HTML_BYTES}B)"

        return True, ""

    # ── Step 6 — Implement ──────────────────────────────────────────────────

    def implement_done(self, element_queue: list) -> bool:
        """True when all elements have been processed."""
        return not element_queue


validator = WorkflowValidator()
