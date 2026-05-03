from __future__ import annotations

from pathlib import Path
from typing import Callable

from .budget import PreviewBudgetGate
from .cache import append_preview_history, load_pending_preview, load_preview_history, save_pending_preview
from .prompts import build_desktop_preview_prompt, select_overview_aspect_ratio
from .types import PreviewEvent, PreviewNode, PreviewRunOptions, PreviewRunResult, PreviewWorkflow
from .validators import validate_desktop_prompt_contract, validate_visual_context_contract


def _null_log():
    class Log:
        def info(self, *args, **kwargs):
            pass
        def warning(self, *args, **kwargs):
            pass
    return Log()


def _prior_session_spend(session_dir: str) -> tuple[float, list[dict]]:
    """Recover the best cumulative estimated spend from preview_pipeline.history.jsonl."""
    best_spent = 0.0
    best_history: list[dict] = []
    for entry in load_preview_history(session_dir):
        budget = entry.get("budget") if isinstance(entry, dict) else None
        if not isinstance(budget, dict):
            continue
        try:
            spent = float(budget.get("spent") or 0.0)
        except (TypeError, ValueError):
            spent = 0.0
        if spent < best_spent:
            continue
        calls = budget.get("history")
        history_items: list[dict] = []
        if isinstance(calls, list):
            for call in calls:
                if not isinstance(call, dict):
                    continue
                amount = float(call.get("amount") or 0.0)
                if amount <= 0:
                    continue
                history_items.append({
                    "model": call.get("model", "unknown"),
                    "amount": amount,
                    "detail": call.get("detail", "previous-session-preview"),
                    "total": call.get("total", 0.0),
                })
        best_spent = spent
        best_history = history_items
    return round(best_spent, 6), best_history


def topological_preview_nodes(workflow: PreviewWorkflow) -> list[PreviewNode]:
    """Return workflow nodes in dependency order and reject cycles/unknown edges."""
    nodes_by_id = {node.id: node for node in workflow.nodes}
    incoming = {node.id: 0 for node in workflow.nodes}
    outgoing: dict[str, list[str]] = {node.id: [] for node in workflow.nodes}
    for edge in workflow.edges:
        if edge.source not in nodes_by_id or edge.target not in nodes_by_id:
            raise ValueError(f"workflow edge references unknown node: {edge.source}->{edge.target}")
        outgoing[edge.source].append(edge.target)
        incoming[edge.target] += 1

    ready = [node.id for node in workflow.nodes if incoming[node.id] == 0]
    ordered: list[PreviewNode] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(nodes_by_id[node_id])
        for target in outgoing[node_id]:
            incoming[target] -= 1
            if incoming[target] == 0:
                ready.append(target)

    if len(ordered) != len(workflow.nodes):
        raise ValueError(f"workflow contains a cycle: {workflow.id}")
    return ordered


def execute_preview_workflow(
    *,
    direction: dict,
    profile: dict,
    html_path: Path,
    options: PreviewRunOptions,
    log,
    analyze_image: Callable,
    render_html: Callable,
    generate_image: Callable,
) -> PreviewRunResult:
    """Run the default desktop-preview flow with explicit cache and budget gates."""
    log = log or _null_log()
    from .templates import build_default_desktop_preview_workflow

    workflow = build_default_desktop_preview_workflow()
    ordered_node_ids = [node.id for node in topological_preview_nodes(workflow)]
    events: list[PreviewEvent] = [PreviewEvent("workflow", "topology_ready", {"node_order": ordered_node_ids})]
    prior_spend, prior_history = _prior_session_spend(options.session_dir)
    gate = PreviewBudgetGate(
        max_budget=options.budget_limit if options.budget_limit is not None else 0.08,
        spent=prior_spend,
        history=prior_history,
    )

    def finish(result: PreviewRunResult) -> PreviewRunResult:
        if not result.budget:
            result.budget = gate.summary()
        append_preview_history(options.session_dir, {
            "status": result.status,
            "image_url": result.image_url,
            "html_path": result.html_path,
            "budget": result.budget,
            "error": result.error,
        })
        return result

    cached = load_pending_preview(options.session_dir) if options.use_cache and not options.regenerate else {}
    if cached.get("image_url"):
        visual_context = dict(cached.get("visual_context") or {})
        cached_html_path = Path(cached.get("html_path") or html_path)
        try:
            if not cached_html_path.exists() or cached_html_path.stat().st_size < 200:
                render_html(cached_html_path, cached["image_url"], visual_context, direction, log)
        except Exception as e:
            events.append(PreviewEvent("html", "node_error", {"error": str(e)}))
            return finish(PreviewRunResult(status="error", error=f"cached preview render failed: {e}", events=events, budget=gate.summary()))
        return finish(PreviewRunResult(
            image_url=cached["image_url"],
            html_path=str(cached_html_path),
            visual_context=visual_context,
            events=[PreviewEvent("cache", "cache_hit", {"image_url": cached["image_url"]})],
            budget=gate.summary(),
        ))

    aspect_ratio = select_overview_aspect_ratio(profile or {})
    prompt = build_desktop_preview_prompt(direction or {}, aspect_ratio=aspect_ratio)
    prompt_errors = validate_desktop_prompt_contract(prompt)
    if prompt_errors:
        log.warning("desktop preview prompt contract warnings: %s", prompt_errors)
    events.append(PreviewEvent("prompt", "node_complete", {"aspect_ratio": aspect_ratio, "errors": prompt_errors}))

    if not options.allow_paid_generation:
        return finish(PreviewRunResult(status="error", error="paid generation disabled", events=events, budget=gate.summary()))

    estimated_cost = gate.estimate("fal-ai/nano-banana")
    if not gate.can_spend(estimated_cost):
        return finish(PreviewRunResult(
            status="error",
            error=(
                f"Preview budget exceeded: ${gate.remaining():.4f} remaining, "
                f"${estimated_cost:.4f} needed for fal-ai/nano-banana"
            ),
            events=events,
            budget=gate.summary(),
        ))

    image_url = generate_image(prompt, aspect_ratio, options.fal_key, log)
    events.append(PreviewEvent("image", "node_complete" if image_url else "node_error", {"image_url": image_url}))
    if not image_url:
        return finish(PreviewRunResult(status="error", error="image generation failed", events=events, budget=gate.summary()))
    gate.record_model("fal-ai/nano-banana", detail="desktop-preview")

    try:
        visual_context = analyze_image(image_url, direction, log)
    except Exception as e:
        events.append(PreviewEvent("analysis", "node_error", {"error": str(e)}))
        return finish(PreviewRunResult(status="error", error=f"image analysis failed: {e}", events=events, budget=gate.summary()))
    if not isinstance(visual_context, dict):
        visual_context = {}
    visual_context["reference_image_url"] = image_url
    context_errors = validate_visual_context_contract(visual_context)
    if context_errors:
        log.warning("visual context contract warnings: %s", context_errors)
    events.append(PreviewEvent("analysis", "node_complete", {"errors": context_errors}))

    try:
        if not html_path.exists() or html_path.stat().st_size < 200:
            render_html(html_path, image_url, visual_context, direction, log)
    except Exception as e:
        events.append(PreviewEvent("html", "node_error", {"error": str(e)}))
        return finish(PreviewRunResult(status="error", error=f"preview HTML render failed: {e}", events=events, budget=gate.summary()))
    events.append(PreviewEvent("html", "node_complete", {"html_path": str(html_path)}))

    save_pending_preview(options.session_dir, image_url, html_path, visual_context)
    events.append(PreviewEvent("cache", "node_complete", {"session_dir": options.session_dir}))

    return finish(PreviewRunResult(
        image_url=image_url,
        html_path=str(html_path),
        visual_context=visual_context,
        events=events,
        budget=gate.summary(),
    ))


run_desktop_preview_pipeline = execute_preview_workflow
