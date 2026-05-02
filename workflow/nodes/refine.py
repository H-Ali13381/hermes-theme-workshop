"""Step 3 — Converge on a single theme. Writes design.json. Uses interrupt() for confirmation."""
from __future__ import annotations

import json
import re
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
    judge_design_creativity,
    MAX_LOOP_ITERATIONS,
    PALETTE_SLOTS,
    RECIPE_PROMPT_FIELDS,
    RECIPE_REQUIRED_KEYS,
    SUPPORTED_DESKTOP_RECIPES,
)
from ..log_setup import get_logger, truncate_for_log
from ..state import RiceSessionState
from ..validators import design_complete

DESIGN_SENTINEL = "<<DESIGN_READY>>"

# Internal self-healing retries inside one refine_node invocation. Bounds the
# upper latency cost (each retry is another LLM round-trip) while removing the
# common case where the agent panics and bypasses the workflow because the
# first response failed to emit valid JSON.
MAX_REFINE_RETRIES = 1


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

## Creativity Rules — especially for KDE Plasma
- A valid KDE rice is NOT a palette swap. Follow the user's vision and make at least 3 specific non-default moves.
- Widgets are powerful but optional: use EWW/widgets only when they serve the brief. Do not add generic clocks/meters just to satisfy a checklist.
- If you preview rounded windows, custom titlebars, terminal frames, ornamental borders, or panel chrome, chrome_strategy must say exactly how those visuals will be implemented.
- Favor original, theme-specific composition over generic docks, average bars, and stock defaults.

## Output
Output ONLY the design_system JSON. Do not narrate the design, do not preview the
palette in prose, do not show tables, do not ask the user to confirm. The next
workflow step renders a visual HTML mockup that the user will actually judge —
your job here is to produce structured data, not commentary.

End your response with the sentinel on its own line, followed immediately by a
fenced ```json block containing the complete design_system object:

{DESIGN_SENTINEL}
```json
{{...complete design_system object...}}
```
"""


# Backward-compatible default prompt for modules/tests importing SYSTEM_PROMPT.
SYSTEM_PROMPT = build_system_prompt("kde")


def refine_node(state: RiceSessionState) -> dict:
    """Converge on design.json. Loops via graph routing until confirmed."""
    log = get_logger("refine", state)
    llm = get_llm(0.3)
    messages = list(state.get("messages", []))
    direction = state.get("design", {})
    profile = state.get("device_profile", {})
    # Fail closed: refusing to generate a design at all is safer than silently
    # producing a KDE design on a non-KDE machine (likely on resume from a
    # checkpoint that lost its device_profile, or a state-loading bug).
    recipe = profile.get("desktop_recipe")
    if not recipe:
        raise ValueError(
            "refine_node: device_profile is missing 'desktop_recipe'. "
            "This usually means setup_node didn't run or the checkpoint was "
            "loaded without a device profile. Re-run setup before refining."
        )
    system_prompt = build_system_prompt(recipe)

    # Track invocations so routing.after_refine can abort if the loop diverges.
    loop_counts = dict(state.get("loop_counts") or {})
    prior_refine_count = loop_counts.get("refine", 0)
    loop_counts["refine"] = prior_refine_count + 1
    log.info("refine invocation #%d (recipe=%s)", prior_refine_count + 1, recipe)

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
        log.debug("seeded conversation with system + direction prompt")

    # Self-healing retry loop: try to extract a valid design up to
    # MAX_REFINE_RETRIES extra times before falling through to a user interrupt.
    # Failed retry exchanges stay local — only the final response (success or
    # the one shown via interrupt) is committed to the message history.
    working_messages = list(messages)
    response = llm.invoke(working_messages)
    log.debug("attempt 1 raw response:\n%s", truncate_for_log(response.content or ""))
    design, reason = _extract_design_json(response.content or "", recipe)
    if design:
        design, reason = _judge_or_reject(design, direction, recipe, log)

    for attempt in range(MAX_REFINE_RETRIES):
        if design:
            break
        log.warning("attempt %d failed (%s) — retrying", attempt + 1, reason)
        retry_msg = HumanMessage(content=_build_retry_prompt(reason))
        working_messages = working_messages + [response, retry_msg]
        response = llm.invoke(working_messages)
        log.debug(
            "attempt %d raw response:\n%s",
            attempt + 2, truncate_for_log(response.content or ""),
        )
        design, reason = _extract_design_json(response.content or "", recipe)
        if design:
            design, reason = _judge_or_reject(design, direction, recipe, log)

    if design:
        queue = _queue_design_elements(
            state.get("element_queue", []), design, state.get("device_profile", {}),
        )
        session_dir = state.get("session_dir", "")
        if session_dir:
            _write_design_json(session_dir, design)
        log.info("design.json written: %s", design.get("name"))
        return {
            "messages": new_messages + [AIMessage(content=response.content.split(DESIGN_SENTINEL)[0].strip())],
            "design": design,
            "element_queue": queue,
            "current_step": 3,
            "loop_counts": loop_counts,
        }

    log.warning(
        "all %d attempts failed (%s) — asking user",
        MAX_REFINE_RETRIES + 1, reason,
    )
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


def _judge_or_reject(
    design: dict, direction: dict, recipe: str, log,
) -> tuple[dict | None, str]:
    """Run the LLM creativity judge on a structurally-valid design.

    Returns ``(design, "")`` on pass / fail-open, or ``(None, reason)`` on a
    confident reject so the outer retry loop can prompt the model again.
    Only KDE currently has semantic creativity rules; other recipes pass.
    """
    if recipe != "kde":
        return design, ""
    ok, reasons = judge_design_creativity(design, direction or {})
    if ok:
        return design, ""
    joined = "; ".join(reasons)
    log.warning("creativity judge rejected design: %s", joined)
    return None, f"creativity judge rejected: {joined}"


def _extract_design_json(content: str, recipe: str = "kde") -> tuple[dict | None, str]:
    """Pull the JSON block after the sentinel.

    Returns ``(design, "")`` on success or ``(None, reason)`` describing why the
    extraction failed so the caller can craft a targeted self-healing retry.
    """
    if not content:
        return None, "empty response"
    parts = content.split(DESIGN_SENTINEL, 1)
    if len(parts) < 2:
        return None, "missing sentinel"
    after = parts[1].strip()
    # Extract JSON from markdown fences using a block-extraction pattern so any
    # preamble text before the opening fence is handled correctly (matches plan.py).
    fence_m = re.search(r"```(?:json)?\s*([\s\S]*?)```", after)
    if fence_m:
        after = fence_m.group(1).strip()
    decoder = json.JSONDecoder()
    idx = after.find("{")
    if idx < 0:
        return None, "no JSON object after sentinel"
    try:
        obj, _ = decoder.raw_decode(after, idx)
    except Exception as e:
        return None, f"JSON parse error: {e}"
    if recipe not in SUPPORTED_DESKTOP_RECIPES:
        return None, f"unsupported desktop recipe '{recipe}'"
    ok, reason = design_complete(obj, {"desktop_recipe": recipe})
    if not ok:
        return None, f"design validation failed: {reason}"
    return obj, ""


def _validate_design(d: dict, recipe: str = "kde") -> bool:
    if recipe not in SUPPORTED_DESKTOP_RECIPES:
        return False
    ok, _ = design_complete(d, {"desktop_recipe": recipe})
    return ok


def _build_retry_prompt(reason: str) -> str:
    """Concise corrective instruction for a self-healing retry."""
    return (
        f"Your previous response failed: {reason}.\n\n"
        "Re-emit your final answer with NO prose, NO commentary, NO confirmation step. "
        "End with the sentinel on its own line, immediately followed by a fenced "
        "```json block containing the complete design_system object:\n\n"
        f"{DESIGN_SENTINEL}\n"
        "```json\n"
        "{...complete design_system object...}\n"
        "```"
    )


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


def _queue_design_elements(queue: list[str], design: dict, profile: dict | None = None) -> list[str]:
    """Add optional design-driven implementers without making widgets mandatory.

    Picks the widget framework based on the running compositor:
      - Hyprland or KDE Wayland → widgets:quickshell (default)
      - Everything else (KDE X11, GNOME, X11) → widgets:eww (fallback)
    An explicit element name in implementation_targets overrides the default.
    """
    updated = list(queue or [])
    chrome = design.get("chrome_strategy", {}) if isinstance(design, dict) else {}
    method = str(chrome.get("method", "")).lower() if isinstance(chrome, dict) else ""
    targets = " ".join(str(x).lower() for x in chrome.get("implementation_targets", [])) if isinstance(chrome, dict) else ""

    explicit = None
    if "widgets:quickshell" in targets:
        explicit = "widgets:quickshell"
    elif "widgets:eww" in targets:
        explicit = "widgets:eww"

    needs_widget = bool(design.get("widget_layout")) or any(
        term in method or term in targets
        for term in ("eww", "quickshell", "overlay", "frame", "border")
    )
    if not needs_widget:
        return updated

    provider = explicit or _default_widget_element(profile or {})
    if provider not in updated:
        insert_at = 1 if updated else 0
        updated.insert(insert_at, provider)
    return updated


def _default_widget_element(profile: dict) -> str:
    """Return the default widgets:* element name for this profile.

    Quickshell is preferred wherever wlr-layer-shell is available
    (Hyprland, KDE Wayland). EWW is the fallback for X11 / unknown.
    """
    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "").lower()
    session = str(profile.get("session_type") or "").lower()
    if "hypr" in wm:
        return "widgets:quickshell"
    if ("kde" in wm or "plasma" in wm) and session == "wayland":
        return "widgets:quickshell"
    return "widgets:eww"
