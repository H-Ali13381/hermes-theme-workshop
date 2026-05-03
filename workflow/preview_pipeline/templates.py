from __future__ import annotations

from .types import PreviewEdge, PreviewNode, PreviewNodeType, PreviewWorkflow


def build_default_desktop_preview_workflow() -> PreviewWorkflow:
    return PreviewWorkflow(
        id="desktop-preview-default",
        name="Desktop Preview Default",
        nodes=[
            PreviewNode("prompt", PreviewNodeType.DESKTOP_PROMPT, {}),
            PreviewNode("image", PreviewNodeType.FAL_DESKTOP_CONCEPT, {"prompt": "{{prompt.prompt}}"}),
            PreviewNode("analysis", PreviewNodeType.MULTIMODAL_ANALYSIS, {"image_url": "{{image.image_url}}"}),
            PreviewNode("validate", PreviewNodeType.CONTRACT_VALIDATE, {"visual_context": "{{analysis.visual_context}}"}),
            PreviewNode("html", PreviewNodeType.STYLE_HTML_RENDER, {"visual_context": "{{analysis.visual_context}}"}),
            PreviewNode("cache", PreviewNodeType.CACHE_ARTIFACTS, {"image_url": "{{image.image_url}}"}),
        ],
        edges=[
            PreviewEdge("prompt", "image"),
            PreviewEdge("image", "analysis"),
            PreviewEdge("analysis", "validate"),
            PreviewEdge("validate", "html"),
            PreviewEdge("html", "cache"),
        ],
    )


def build_variant_desktop_preview_workflow(variant_count: int = 3) -> PreviewWorkflow:
    count = max(1, min(variant_count, 4))
    nodes = [PreviewNode("prompt", PreviewNodeType.DESKTOP_PROMPT, {})]
    edges: list[PreviewEdge] = []
    for idx in range(1, count + 1):
        image_id = f"image_{idx}"
        nodes.append(PreviewNode(image_id, PreviewNodeType.FAL_DESKTOP_CONCEPT, {
            "prompt": f"{{{{prompt.prompt}}}}\nVariant {idx}: preserve the same theme, vary composition and UI emphasis.",
        }))
        edges.append(PreviewEdge("prompt", image_id))
    return PreviewWorkflow(
        id="desktop-preview-variants",
        name="Desktop Preview Variants",
        nodes=nodes,
        edges=edges,
    )
