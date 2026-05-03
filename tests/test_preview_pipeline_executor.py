from workflow.preview_pipeline.executor import execute_preview_workflow, topological_preview_nodes
from workflow.preview_pipeline.templates import (
    build_default_desktop_preview_workflow,
    build_variant_desktop_preview_workflow,
)
from workflow.preview_pipeline.types import (
    PreviewEdge,
    PreviewNode,
    PreviewNodeType,
    PreviewRunOptions,
    PreviewWorkflow,
)


def test_preview_workflow_accepts_desktop_nodes():
    wf = PreviewWorkflow(
        id="preview-1",
        name="desktop-overview",
        nodes=[
            PreviewNode(id="prompt", type=PreviewNodeType.DESKTOP_PROMPT, config={"direction": {}}),
            PreviewNode(id="image", type=PreviewNodeType.FAL_DESKTOP_CONCEPT, config={"prompt": "{{prompt.prompt}}"}),
        ],
        edges=[PreviewEdge(source="prompt", target="image")],
    )

    assert wf.id == "preview-1"
    assert wf.nodes[0].type is PreviewNodeType.DESKTOP_PROMPT
    assert wf.edges[0].source == "prompt"


def test_default_template_has_expected_node_order():
    wf = build_default_desktop_preview_workflow()
    assert [node.id for node in wf.nodes] == [
        "prompt",
        "image",
        "analysis",
        "validate",
        "html",
        "cache",
    ]
    assert [node.id for node in topological_preview_nodes(wf)] == [
        "prompt",
        "image",
        "analysis",
        "validate",
        "html",
        "cache",
    ]


def test_executor_reuses_cached_preview_without_paid_generation(tmp_path):
    from workflow.preview_pipeline.cache import save_pending_preview

    html_path = tmp_path / "visualize.html"
    html_path.write_text("<html>cached</html>")
    save_pending_preview(
        str(tmp_path),
        "https://example.com/cached.png",
        html_path,
        {"reference_image_url": "https://example.com/cached.png"},
    )

    result = execute_preview_workflow(
        direction={"name": "cached"},
        profile={},
        html_path=html_path,
        options=PreviewRunOptions(session_dir=str(tmp_path), fal_key="", use_cache=True),
        log=None,
        analyze_image=lambda image_url, direction, log: {"reference_image_url": image_url},
        render_html=lambda path, image_url, visual_context, direction, log: path.write_text("<html>new</html>"),
        generate_image=lambda prompt, aspect_ratio, fal_key, log: (_ for _ in ()).throw(AssertionError("should not generate")),
    )

    assert result.image_url == "https://example.com/cached.png"
    assert result.visual_context["reference_image_url"] == "https://example.com/cached.png"
    assert result.budget["num_calls"] == 0


def test_variant_template_is_opt_in_and_has_three_paid_image_nodes():
    wf = build_variant_desktop_preview_workflow(variant_count=3)
    image_nodes = [node for node in wf.nodes if node.type.value == "fal_desktop_concept"]

    assert len(image_nodes) == 3
    assert [node.id for node in image_nodes] == ["image_1", "image_2", "image_3"]


def test_executor_blocks_cumulative_session_budget_across_runs(tmp_path):
    html_path = tmp_path / "visualize.html"

    def analyze(image_url, direction, log):
        return {
            "reference_image_url": image_url,
            "extracted_palette": {},
            "style_description": "dark",
            "visual_element_plan": [],
            "validation_checklist": [],
        }

    def render(path, image_url, visual_context, direction, log):
        path.write_text("<html>" + ("x" * 250) + "</html>")

    first = execute_preview_workflow(
        direction={"name": "budget"},
        profile={},
        html_path=html_path,
        options=PreviewRunOptions(session_dir=str(tmp_path), fal_key="key", use_cache=False, budget_limit=0.05),
        log=None,
        analyze_image=analyze,
        render_html=render,
        generate_image=lambda prompt, aspect_ratio, fal_key, log: "https://example.com/first.png",
    )
    assert first.status == "success"
    assert first.budget["spent"] == 0.04

    second = execute_preview_workflow(
        direction={"name": "budget"},
        profile={},
        html_path=html_path,
        options=PreviewRunOptions(session_dir=str(tmp_path), fal_key="key", use_cache=False, regenerate=True, budget_limit=0.05),
        log=None,
        analyze_image=analyze,
        render_html=render,
        generate_image=lambda prompt, aspect_ratio, fal_key, log: (_ for _ in ()).throw(AssertionError("should not generate over budget")),
    )
    assert second.status == "error"
    assert "Preview budget exceeded" in second.error


def test_executor_converts_analysis_exception_to_error(tmp_path):
    result = execute_preview_workflow(
        direction={"name": "analysis-fails"},
        profile={},
        html_path=tmp_path / "visualize.html",
        options=PreviewRunOptions(session_dir=str(tmp_path), fal_key="key", use_cache=False),
        log=None,
        analyze_image=lambda image_url, direction, log: (_ for _ in ()).throw(ValueError("vision down")),
        render_html=lambda path, image_url, visual_context, direction, log: path.write_text("<html></html>"),
        generate_image=lambda prompt, aspect_ratio, fal_key, log: "https://example.com/paid.png",
    )

    assert result.status == "error"
    assert result.image_url == ""
    assert "image analysis failed" in result.error
