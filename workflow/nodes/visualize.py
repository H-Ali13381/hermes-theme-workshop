"""Step 2.5 — AI desktop concept preview: FAL image generation + multimodal style analysis.

Requires:
  - FAL_KEY environment variable (fal.ai account)
  - A multimodal-capable LLM (vision input support)

If either is unavailable the node warns the user via an interrupt and routes
straight to Step 3 (refine) with an empty visual_context so the rest of the
pipeline is unaffected.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

try:
    import fal_client  # type: ignore[import]
except ImportError:  # pragma: no cover - exercised through runtime availability checks
    fal_client = None  # type: ignore[assignment]

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt

from ..config import get_llm, resolve_env_secret
from ..log_setup import get_logger
from ..preview_pipeline.cache import (
    clear_pending_preview as _clear_pending_preview,
    load_pending_preview as _load_pending_preview,
    pending_preview_path as _pending_preview_path,
    save_pending_preview as _save_pending_preview,
)
from ..preview_pipeline.executor import execute_preview_workflow
from ..preview_pipeline.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    PREVIEW_SYSTEM_PROMPT,
    aspect_prompt_phrase as _aspect_prompt_phrase,
    build_desktop_preview_prompt as _build_desktop_preview_prompt,
    overview_target_geometry as _overview_target_geometry,
    select_overview_aspect_ratio as _select_overview_aspect_ratio,
)
from ..preview_pipeline.providers import generate_desktop_concept
from ..preview_pipeline.types import PreviewRunOptions
from ..preview_pipeline.validators import validate_desktop_prompt_contract
from ..state import RiceSessionState


# ── Node ─────────────────────────────────────────────────────────────────────

def visualize_node(state: RiceSessionState) -> dict:
    """Generate AI full-desktop theme concept + multimodal preview. Interrupts for approval."""
    log = get_logger("visualize", state)
    direction = state.get("design", {})
    session_dir = state.get("session_dir", "")

    loop_counts = dict(state.get("loop_counts") or {})
    loop_counts["visualize"] = loop_counts.get("visualize", 0) + 1
    log.info("visualize invocation #%d", loop_counts["visualize"])

    fal_key = resolve_env_secret("FAL_KEY")
    cached_preview = _load_pending_preview(session_dir)
    if not fal_key and not cached_preview.get("image_url"):
        log.warning("FAL_KEY not set — skipping AI desktop preview generation")
        msg = (
            "⚠  FAL_KEY not configured — skipping AI image generation.\n\n"
            "Set `export FAL_KEY=<your-key>` in ~/.bashrc and restart to enable "
            "this step. Proceeding to design phase without an AI desktop preview."
        )
        user_reply = interrupt({"step": "2.5", "type": "conversation", "message": msg})
        return {
            "messages": [AIMessage(content=msg), HumanMessage(content=str(user_reply))],
            "visual_context": {},
            "visualize_route": "skip",
            "current_step": 3,
            "loop_counts": loop_counts,
        }

    # ── 1–3. Generate/analyze/render through the DesktopPreviewPipeline ───────
    # LangGraph checkpoints the interrupt, not this node's eventual return value.
    # If a stale bridge mistakenly calls graph.stream(None) while the approval
    # interrupt is already pending, state may not yet contain visualize_image_url.
    # The pipeline's cache fast-path preserves the approved target and prevents a
    # second paid FAL generation on accidental no-answer re-entry.
    html_path = _get_html_path(session_dir)
    result = execute_preview_workflow(
        direction=direction,
        profile=state.get("device_profile", {}),
        html_path=html_path,
        options=PreviewRunOptions(
            session_dir=session_dir,
            fal_key=fal_key,
            use_cache=True,
            budget_limit=0.08,
            allow_paid_generation=True,
            regenerate=False,
        ),
        log=log,
        analyze_image=_analyze_image_multimodal,
        render_html=_render_style_html,
        generate_image=generate_desktop_concept,
    )

    image_url = result.image_url
    visual_context = result.visual_context
    html_path = Path(result.html_path) if result.html_path else html_path

    if not image_url:
        log.warning("FAL image generation failed — skipping AI desktop preview")
        msg = "⚠  Image generation failed. Proceeding without AI desktop preview.\nCheck your FAL_KEY and account credits."
        user_reply = interrupt({"step": "2.5", "type": "conversation", "message": msg})
        return {
            "messages": [AIMessage(content=msg), HumanMessage(content=str(user_reply))],
            "visual_context": {},
            "visualize_route": "skip",
            "current_step": 3,
            "loop_counts": loop_counts,
            "preview_pipeline_status": {"status": result.status, "error": result.error},
            "preview_budget": result.budget,
        }

    # ── 4. Interrupt for user approval ────────────────────────────────────────
    decision = interrupt({
        "step": "2.5",
        "type": "approval",
        "message": (
            f"AI desktop theme preview generated:\n  Image: {image_url}\n  Preview: {html_path}\n\n"
            "Open the preview, then:\n"
            "  'approve'     — lock this desktop direction, proceed to design\n"
            "  'regenerate'  — generate a fresh desktop preview image\n"
            "  'back'        — revise the creative direction\n"
            "  or describe what feels off"
        ),
    })

    decision_str = str(decision).strip()
    decision_lower = decision_str.lower()

    if decision_lower in ("approve", "yes", "ok", "looks good", "good"):
        log.info("AI desktop preview approved")
        return {
            "messages": [AIMessage(content=f"AI desktop preview locked in. Reference: {image_url}")],
            "visualize_image_url": image_url,
            "visualize_html_path": str(html_path),
            "visual_context": visual_context,
            "visualize_route": "approve",
            "current_step": 3,
            "loop_counts": loop_counts,
            "preview_pipeline_status": {"status": result.status, "events": [e.__dict__ for e in result.events]},
            "preview_budget": result.budget,
        }

    if decision_lower in ("back", "revise", "direction", "explore"):
        log.info("routing back to explore for direction revision")
        html_path.unlink(missing_ok=True)
        _clear_pending_preview(session_dir)
        return {
            "visualize_image_url": "", "visual_context": {},
            "visualize_route": "explore", "loop_counts": loop_counts,
        }

    # regenerate or freeform feedback
    log.info("regenerating AI desktop preview (feedback: %r)", decision_str[:60])
    html_path.unlink(missing_ok=True)
    _clear_pending_preview(session_dir)
    return {
        "messages": [HumanMessage(content=f"[VISUAL_FEEDBACK] {decision_str}")],
        "visualize_image_url": "", "visual_context": {},
        "visualize_route": "regenerate", "loop_counts": loop_counts,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_style_image(direction: dict, fal_key: str, log, profile: dict | None = None) -> str:
    """Compatibility wrapper for tests and older callers."""
    aspect_ratio = _select_overview_aspect_ratio(profile or {})
    prompt = _build_desktop_preview_prompt(direction, aspect_ratio=aspect_ratio)
    prompt_errors = validate_desktop_prompt_contract(prompt)
    if prompt_errors:
        log.warning("desktop preview prompt contract warnings: %s", prompt_errors)
    log.info("generating FAL nano-banana image — aspect=%s prompt: %s", aspect_ratio, prompt[:120])
    return generate_desktop_concept(prompt, aspect_ratio, fal_key, log)


def _analyze_image_multimodal(image_url: str, direction: dict, log) -> dict:
    """Use a multimodal LLM to extract palette and style notes from the desktop preview image.

    Raises on any LLM or parse error — the caller surfaces the exception to the
    user rather than silently continuing with an empty context.
    """
    llm = get_llm(0.3)
    response = llm.invoke([
        SystemMessage(content=ANALYSIS_SYSTEM_PROMPT),
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": (
                f"Creative direction:\n{json.dumps(direction, indent=2)}\n\n"
                "Analyze this image and extract design guidance for the Linux desktop theme."
            )},
        ]),
    ])
    raw = (response.content or "").strip()
    log.debug("multimodal analysis raw:\n%s", raw[:400])
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    idx = raw.find("{")
    if idx < 0:
        raise ValueError(f"multimodal LLM returned no JSON object:\n{raw[:300]}")
    obj, _ = json.JSONDecoder().raw_decode(raw, idx)
    if not isinstance(obj, dict):
        raise ValueError(f"multimodal LLM returned non-dict JSON: {type(obj)}")
    log.info("multimodal analysis successful")
    return obj


def _render_style_html(
    html_path: Path, image_url: str, visual_context: dict, direction: dict, log,
) -> None:
    """Generate the style preview HTML via LLM and write it atomically.

    Raises if the LLM call fails or returns something that doesn't look like HTML.
    """
    log.info("generating style preview HTML")
    llm = get_llm(0.85)
    payload = json.dumps({"direction": direction, "visual_analysis": visual_context}, indent=2)
    system = PREVIEW_SYSTEM_PROMPT + f"\n\nReference image URL: {image_url}"
    response = llm.invoke([
        SystemMessage(content=system),
        HumanMessage(content=f"Style data:\n```json\n{payload}\n```"),
    ])
    html_content = _extract_html(response.content or "")
    if not html_content:
        raise ValueError("LLM returned a response with no HTML content for style preview")

    html_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=html_path.parent, encoding="utf-8", delete=False, suffix=".tmp"
        ) as f:
            f.write(html_content)
            tmp = f.name
        Path(tmp).replace(html_path)
    except Exception:
        if tmp:
            Path(tmp).unlink(missing_ok=True)
        raise
    log.info("style preview written: %s", html_path)


def _extract_html(content: str) -> str:
    content = content.strip()
    fence = re.search(r"```(?:html)?\s*([\s\S]*?)```", content)
    if fence:
        inner = fence.group(1).strip()
        if inner.startswith("<!DOCTYPE") or inner.startswith("<html"):
            return inner
    for marker in ("<!DOCTYPE", "<html"):
        start = content.find(marker)
        if start != -1:
            return content[start:]
    return ""


def _get_html_path(session_dir: str) -> Path:
    if session_dir:
        return Path(session_dir) / "visualize.html"
    return Path(tempfile.gettempdir()) / f"linux-ricing-visualize-{os.getpid()}.html"
