"""Step 2 — Fast creative intake. One visible chat, hidden orchestration."""
from __future__ import annotations

import json
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from ..config import get_llm
from ..state import RiceSessionState

DIRECTION_SENTINEL = "<<DIRECTION_CONFIRMED>>"

SYSTEM_PROMPT = """\
You are a creative director for Linux desktop theming. You are hidden behind a single
chat interface: never mention agents, workflows, orchestration, or handoffs.

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
- Be concise. No monologues.
- Ask no questions during proposal/finalization except "Pick one, combine, or tweak."
- For proposals, return exactly 3 numbered visual directions.
- For finalization, write a short confirmation ending with the exact sentinel on its own line:
  {sentinel}
- After the sentinel, on a new line, write a JSON object:
  {{"stance": "<name>", "mood": ["word1","word2","word3"], "reference_anchor": "<concise>",
    "name_hypothesis": "<theme-slug>"}}

Speak in vibes, not taxonomy. Reference films, music, games, spaces — not software.
""".format(sentinel=DIRECTION_SENTINEL)

BRIEF_STAGE = "brief"
PROPOSE_STAGE = "propose"
FINALIZE_STAGE = "finalize"
# Re-entry stage triggered when plan_node routes feedback back to explore.
# Skips the brief; LLM sees prior direction + rejection feedback and proposes
# revised directions before flowing into FINALIZE_STAGE.
REVISE_STAGE = "revise"


def explore_node(state: RiceSessionState) -> dict:
    """Collect a compact brief, propose directions once, then finalize."""
    profile = state.get("device_profile", {})
    intake = dict(state.get("explore_intake") or {})
    stage = intake.get("stage", BRIEF_STAGE)

    # Track invocations so routing.after_explore can abort if the LLM loops without
    # converging (e.g. sentinel emitted but JSON parsing consistently fails).
    loop_counts = dict(state.get("loop_counts") or {})
    loop_counts["explore"] = loop_counts.get("explore", 0) + 1

    if stage == BRIEF_STAGE:
        prompt = _brief_prompt()
        user_reply = interrupt({
            "step": 2,
            "type": "conversation",
            "message": prompt,
        })
        intake.update({"stage": PROPOSE_STAGE, "brief": str(user_reply)})
        return {
            "messages": [AIMessage(content=prompt), HumanMessage(content=str(user_reply))],
            "explore_intake": intake,
            "current_step": 2,
            "loop_counts": loop_counts,
        }

    if stage == PROPOSE_STAGE:
        llm = get_llm(0.7)
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_proposal_prompt(intake, profile)),
        ])
        proposal = (response.content or "").strip() or _fallback_proposal(intake)
        user_reply = interrupt({
            "step": 2,
            "type": "conversation",
            "message": proposal,
        })
        intake.update({
            "stage": FINALIZE_STAGE,
            "proposal": proposal,
            "choice": str(user_reply),
        })
        return {
            "messages": [AIMessage(content=proposal), HumanMessage(content=str(user_reply))],
            "explore_intake": intake,
            "current_step": 2,
            "loop_counts": loop_counts,
        }

    if stage == REVISE_STAGE:
        llm = get_llm(0.7)
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_revise_prompt(intake, profile)),
        ])
        proposal = (response.content or "").strip() or _fallback_revise_proposal(intake)
        user_reply = interrupt({
            "step": 2,
            "type": "conversation",
            "message": proposal,
        })
        intake.update({
            "stage": FINALIZE_STAGE,
            "proposal": proposal,
            "choice": str(user_reply),
        })
        return {
            "messages": [AIMessage(content=proposal), HumanMessage(content=str(user_reply))],
            "explore_intake": intake,
            "current_step": 2,
            "loop_counts": loop_counts,
        }

    llm = get_llm(0.7)
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_final_prompt(intake, profile)),
    ])

    # Check for confirmed direction
    if response.content and DIRECTION_SENTINEL in response.content:
        direction = _parse_direction(response.content)
        clean_content = response.content.split(DIRECTION_SENTINEL)[0].strip()
        if not direction:
            direction = _fallback_direction(intake)
        print(f"\n[Explore] Direction confirmed: {direction}\n")
        return {
            "messages": [AIMessage(content=clean_content)],
            "design": direction,
            "current_step": 2,
            "explore_intake": intake,
            "loop_counts": loop_counts,
        }

    direction = _fallback_direction(intake)
    print(f"\n[Explore] Direction confirmed: {direction}\n")
    return {
        "messages": [AIMessage(content=_confirmation(direction))],
        "design": direction,
        "current_step": 2,
        "explore_intake": intake,
        "loop_counts": loop_counts,
    }


def _brief_prompt() -> str:
    return (
        "Fast brief — reply in bullets or one sentence:\n"
        "1. A place — real or fictional — you'd want to live inside?\n"
        "2. Mood words?\n"
        "3. Subtle reference or obvious homage?\n"
        "4. Anything to avoid? (or skip)"
    )


def _proposal_prompt(intake: dict, profile: dict) -> str:
    return (
        "Create exactly 3 concise visual directions from this brief.\n"
        "Each option: number, 2-4 word name, one vivid sentence, stance/blend.\n"
        "End with: Pick 1, 2, 3, combine, or tweak.\n\n"
        f"Brief:\n{intake.get('brief', '')}\n\n"
        f"Machine profile:\n{_format_device_context(profile)}"
    )


def _final_prompt(intake: dict, profile: dict) -> str:
    return (
        "Finalize the chosen creative direction. Do not ask another question.\n"
        f"End with {DIRECTION_SENTINEL} and the required JSON.\n\n"
        f"Brief:\n{intake.get('brief', '')}\n\n"
        f"Proposed directions:\n{intake.get('proposal', '')}\n\n"
        f"User choice:\n{intake.get('choice', '')}\n\n"
        f"Machine profile:\n{_format_device_context(profile)}"
    )


def _fallback_proposal(intake: dict) -> str:
    brief = intake.get("brief", "your references")
    return (
        "1. Shadow Signal — dark, readable, restrained; Ghost+Signal.\n"
        "2. Neon Relic — game-world glow with ancient texture; Blade+Drift.\n"
        "3. Soft Ruin — worn-in, atmospheric, calm; Garden+Ghost.\n\n"
        f"Based on: {brief}\n"
        "Pick 1, 2, 3, combine, or tweak."
    )


def _revise_prompt(intake: dict, profile: dict) -> str:
    """Prompt for REVISE_STAGE — preserve brief + prior direction, layer rejection feedback on top."""
    prior = intake.get("prior_direction") or {}
    rejection = intake.get("rejection_feedback", "")
    return (
        "The user previously confirmed a creative direction, then rejected the "
        "rendered preview because the overall vibe was off. Keep the original brief "
        "intact; revise the direction to address the rejection.\n\n"
        "Output 1 to 3 revised directions (use 1 if the fix is small, 3 if the vibe "
        "needs to shift). Same format as the proposal stage: number, 2-4 word name, "
        "one vivid sentence, stance/blend.\n"
        "End with: Pick 1 (or 2/3 if multiple), combine, or tweak.\n\n"
        f"Original brief:\n{intake.get('brief', '')}\n\n"
        f"Previously confirmed direction:\n{json.dumps(prior, indent=2) if prior else '(none recorded)'}\n\n"
        f"User rejection feedback on the preview:\n{rejection}\n\n"
        f"Machine profile:\n{_format_device_context(profile)}"
    )


def _fallback_revise_proposal(intake: dict) -> str:
    rejection = intake.get("rejection_feedback", "their previous feedback")
    return (
        "1. Same direction, dialed back — softer accents, less saturation.\n\n"
        f"Adjusting based on: {rejection}\n"
        "Pick 1, combine, or tweak."
    )


def _fallback_direction(intake: dict) -> dict:
    brief = str(intake.get("brief", "custom references")).strip() or "custom references"
    choice = str(intake.get("choice", "selected direction")).strip() or "selected direction"
    return {
        "stance": "Ghost+Blade",
        "mood": ["dark", "readable", "atmospheric"],
        "reference_anchor": f"{brief}; {choice}"[:120],
        "name_hypothesis": "fast-shadow-signal",
    }


def _confirmation(direction: dict) -> str:
    anchor = direction.get("reference_anchor", "your chosen direction")
    return f"Got it — building around {anchor}."


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
