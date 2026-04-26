"""Verify design.json completeness after refine_node."""
from __future__ import annotations

from ..config import DESIGN_REQUIRED_KEYS, PALETTE_SLOTS
from ..state import RiceSessionState


def route_after_refine(state: RiceSessionState) -> str:
    """Return 'plan' if design is complete and valid, else 'refine' to retry."""
    d = state.get("design", {})

    if not d:
        return "refine"

    # All required top-level keys present
    if not all(k in d for k in DESIGN_REQUIRED_KEYS):
        missing = [k for k in DESIGN_REQUIRED_KEYS if k not in d]
        print(f"  [Verifier] design missing keys: {missing} → retrying refine")
        return "refine"

    # All 10 palette slots present and valid hex
    palette = d.get("palette", {})
    if not all(k in palette for k in PALETTE_SLOTS):
        missing = [k for k in PALETTE_SLOTS if k not in palette]
        print(f"  [Verifier] palette missing slots: {missing} → retrying refine")
        return "refine"

    for slot, val in palette.items():
        if not (isinstance(val, str) and val.startswith("#") and len(val) == 7):
            print(f"  [Verifier] invalid hex for {slot}: {val!r} → retrying refine")
            return "refine"

    return "plan"
