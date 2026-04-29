"""Step 2 — Creative direction dialogue. LLM-driven. Uses interrupt() each turn."""
from __future__ import annotations

import json
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from ..config import get_llm, SKILL_DIR, MAX_LOOP_ITERATIONS
from ..state import RiceSessionState

DIRECTION_SENTINEL = "<<DIRECTION_CONFIRMED>>"

SYSTEM_PROMPT = """\
You are a creative director for Linux desktop theming. Your role is Agent = Designer; \
the user is Art/UX Director. Guide a creative exploration, not a configuration menu.

## The Design Stance Model
Seven named stances on two axes:
- Axis 1: Curated (OS knows best) ↔ Liberated (machine is yours)
- Axis 2: Warm/Cold × Meditative/Confrontational

| Stance  | Position  | Flavor                    | Roots                        |
|---------|-----------|---------------------------|------------------------------|
| Zen     | Curated   | Warm / Meditative         | Apple HIG, wabi-sabi         |
| Signal  | Curated   | Cold / Meditative         | Material Design, GNOME       |
| Garden  | Liberated | Warm / Meditative         | Hippie, doujin, lo-fi        |
| Ghost   | Liberated | Cold / Meditative         | Cypherpunk, GNU, tiling WM   |
| Riot    | Liberated | Cold / Confrontational    | Punk, anarchist zines        |
| Blade   | Liberated | Cold / Confrontational    | Cyberpunk, precision-sharp   |
| Drift   | Floating  | Eclectic                  | Situationist dérive          |

Blends are valid: Ghost+Blade = "Hardened workstation", Garden+Blade = "Spaceship but cozy".

## Rules
- Ask about aesthetics and vibes, NEVER about config files or technical tools.
- Use the device profile to suggest a hypothesis ("Your playtime data suggests...").
- After 2-4 exchanges, when you sense a clear direction, write your final message ending
  with the exact sentinel on its own line: {sentinel}
- After the sentinel, on a new line, write a JSON object:
  {{"stance": "<name>", "mood": ["word1","word2","word3"], "reference_anchor": "<concise>",
    "name_hypothesis": "<theme-slug>"}}

Speak in vibes, not taxonomy. Reference films, music, games, spaces — not software.
""".format(sentinel=DIRECTION_SENTINEL)


def explore_node(state: RiceSessionState) -> dict:
    """Multi-turn creative direction dialogue. Loops via graph routing until confirmed."""
    llm = get_llm(0.7)
    messages = list(state.get("messages", []))

    # Track invocations so routing.after_explore can abort if the LLM loops without
    # converging (e.g. sentinel emitted but JSON parsing consistently fails).
    loop_counts = dict(state.get("loop_counts") or {})
    loop_counts["explore"] = loop_counts.get("explore", 0) + 1

    new_messages: list = []
    if not messages:
        # First turn — inject system + device context
        profile = state.get("device_profile", {})
        device_ctx = _format_device_context(profile)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Let's start a ricing session.\n\nMachine profile:\n{device_ctx}"),
        ]
        new_messages = list(messages)  # seed messages are new on first turn

    # Generate response (re-executes on interrupt resume — idempotent for same messages)
    response = llm.invoke(messages)

    # Check for confirmed direction
    if response.content and DIRECTION_SENTINEL in response.content:
        direction = _parse_direction(response.content)
        clean_content = response.content.split(DIRECTION_SENTINEL)[0].strip()
        print(f"\n[Explore] Direction confirmed: {direction}\n")
        return {
            "messages": new_messages + [AIMessage(content=clean_content)],
            "design": direction,
            "current_step": 2,
            "loop_counts": loop_counts,
        }

    # Pause and collect user reply
    user_reply = interrupt({
        "step": 2,
        "type": "conversation",
        "message": response.content or "",
    })

    return {
        "messages": new_messages + [response, HumanMessage(content=str(user_reply))],
        "loop_counts": loop_counts,
    }


def _format_device_context(profile: dict) -> str:
    apps = profile.get("apps", {})
    installed = [k for k, v in apps.items() if v]
    lines = [
        f"WM: {profile.get('wm', 'unknown')}",
        f"Chassis: {profile.get('chassis', 'unknown')} | Screens: {profile.get('screens', 1)}",
        f"GPU: {profile.get('gpu', {}).get('name', 'unknown')}",
        f"Installed apps: {', '.join(installed) if installed else 'standard set'}",
        f"FAL (animated wallpaper): {'available' if profile.get('fal_available') else 'not configured'}",
    ]
    current_wallpaper = profile.get("current_wallpaper", "")
    if current_wallpaper:
        lines.append(f"Current wallpaper: {current_wallpaper}")
    return "\n".join(lines)


def _parse_direction(content: str) -> dict:
    """Extract direction JSON after the sentinel."""
    parts = content.split(DIRECTION_SENTINEL, 1)
    if len(parts) < 2:
        return {}
    after = parts[1].strip()
    decoder = json.JSONDecoder()
    idx = after.find("{")
    if idx >= 0:
        try:
            obj, _ = decoder.raw_decode(after, idx)
            return obj
        except Exception as e:
            print(f"[Explore][WARN] JSON parse error: {e}", file=sys.stderr, flush=True)
    print("[Explore][WARN] Could not parse direction JSON from LLM response — returning empty direction", file=sys.stderr, flush=True)
    return {}
