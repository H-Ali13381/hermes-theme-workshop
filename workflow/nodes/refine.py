"""Step 3 — Converge on a single theme. Writes design.json. Uses interrupt() for confirmation."""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langgraph.types import interrupt
except ImportError:  # LangGraph not installed (e.g. during unit tests)
    AIMessage = HumanMessage = SystemMessage = None  # type: ignore[assignment,misc]
    interrupt = None  # type: ignore[assignment]

from ..config import (
    BASE_REQUIRED_KEYS,
    get_llm,
    MAX_LOOP_ITERATIONS,
    PALETTE_SLOTS,
    RECIPE_PROMPT_FIELDS,
    RECIPE_REQUIRED_KEYS,
    SUPPORTED_DESKTOP_RECIPES,
)
from ..state import RiceSessionState

DESIGN_SENTINEL = "<<DESIGN_READY>>"


def build_system_prompt(recipe: str) -> str:
    """Build the design-system prompt for the detected desktop recipe.

    Raises ValueError for unrecognised recipes so callers get an explicit
    error rather than silently generating a KDE-flavoured prompt for a
    non-KDE environment.
    """
    if recipe not in SUPPORTED_DESKTOP_RECIPES:
        raise ValueError(
            f"Unsupported desktop recipe '{recipe}'. "
            f"Supported: {sorted(SUPPORTED_DESKTOP_RECIPES)}"
        )
    recipe_fields = "\n".join(RECIPE_PROMPT_FIELDS[recipe])
    return f"""\
You are a Linux desktop theme designer. Your task is to produce a complete design_system JSON \
for a {recipe} desktop rice. Build on the creative direction already established.

## The 10-Key Palette Schema
Produce a JSON object with exactly these top-level keys:
- name (kebab-case slug, e.g. "ghost-blade")
- description (1-2 sentences)
- palette: object with exactly 10 semantic keys:
  background, foreground, primary, secondary, accent, surface, muted, danger, success, warning
  All values must be valid #rrggbb hex.
{recipe_fields}
- mood_tags: list of 2-3 lowercase strings

## Color Rules
- background should be dark (YIQ < 128) for dark themes
- foreground must contrast with background (YIQ delta ≥ 128)
- primary is the main accent — most visible interactive element color
- No two palette slots may share the same hex value
- danger should be in red-hue family (hue 330-30°), success green (90-150°), warning amber (30-70°)

## Workflow
1. Show the refined design in a code block
2. Briefly explain 2-3 key color choices (reference the design stance)
3. Ask the user to confirm or request changes
4. When confirmed, output {DESIGN_SENTINEL} followed by the final JSON on the next line

## Output format when confirmed:
{DESIGN_SENTINEL}
```json
{{...complete design_system object...}}
```
"""


# Backward-compatible default prompt for modules/tests importing SYSTEM_PROMPT.
SYSTEM_PROMPT = build_system_prompt("kde")


def refine_node(state: RiceSessionState) -> dict:
    """Converge on design.json. Loops via graph routing until confirmed."""
    llm = get_llm(0.3)
    messages = list(state.get("messages", []))
    direction = state.get("design", {})
    profile = state.get("device_profile", {})
    recipe = profile.get("desktop_recipe", "kde")
    system_prompt = build_system_prompt(recipe)

    # Track invocations so routing.after_refine can abort if the loop diverges.
    loop_counts = dict(state.get("loop_counts") or {})
    prior_refine_count = loop_counts.get("refine", 0)
    loop_counts["refine"] = prior_refine_count + 1

    new_messages: list = []
    if prior_refine_count == 0 or not messages:
        # Seed with system + direction context
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=(
                f"Creative direction established:\n{json.dumps(direction, indent=2)}\n\n"
                "Please produce the design_system.json for this theme."
            )),
        ]
        new_messages = list(messages)  # seed messages are new on first turn

    response = llm.invoke(messages)

    if response.content and DESIGN_SENTINEL in response.content:
        design = _extract_design_json(response.content, recipe)
        if design:
            session_dir = state.get("session_dir", "")
            if session_dir:
                _write_design_json(session_dir, design)
            print(f"[Refine] design.json written: {design.get('name')}\n")
            return {
                "messages": new_messages + [AIMessage(content=response.content.split(DESIGN_SENTINEL)[0].strip())],
                "design": design,
                "current_step": 3,
                "loop_counts": loop_counts,
            }
        print("[Refine][WARN] Sentinel found but design JSON could not be parsed — asking for retry.")

    # Present to user for feedback
    user_reply = interrupt({
        "step": 3,
        "type": "conversation",
        "message": response.content or "",
    })

    return {
        "messages": new_messages + [response, HumanMessage(content=str(user_reply))],
        "loop_counts": loop_counts,
    }


def _extract_design_json(content: str, recipe: str = "kde") -> dict | None:
    """Pull the JSON block after the sentinel."""
    parts = content.split(DESIGN_SENTINEL, 1)
    if len(parts) < 2:
        return None
    after = parts[1].strip()
    # Extract JSON from markdown fences using a block-extraction pattern so any
    # preamble text before the opening fence is handled correctly (matches plan.py).
    fence_m = re.search(r"```(?:json)?\s*([\s\S]*?)```", after)
    if fence_m:
        after = fence_m.group(1).strip()
    decoder = json.JSONDecoder()
    idx = after.find("{")
    if idx >= 0:
        try:
            obj, _ = decoder.raw_decode(after, idx)
            return obj if _validate_design(obj, recipe) else None
        except Exception as e:
            print(f"[Refine][WARN] JSON parse error: {e}", file=sys.stderr, flush=True)
    return None


def _validate_design(d: dict, recipe: str = "kde") -> bool:
    if recipe not in SUPPORTED_DESKTOP_RECIPES:
        return False
    required_keys = BASE_REQUIRED_KEYS + RECIPE_REQUIRED_KEYS[recipe]
    if not all(k in d for k in required_keys):
        return False
    if not all(k in d.get("palette", {}) for k in PALETTE_SLOTS):
        return False
    return True


def _write_design_json(session_dir: str, design: dict) -> None:
    path = Path(session_dir) / "design.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    json_content = json.dumps(design, indent=2)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, encoding="utf-8", delete=False, suffix=".tmp"
        ) as tmp:
            tmp.write(json_content)
            tmp_path = tmp.name
        Path(tmp_path).replace(path)
    except Exception:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        raise
