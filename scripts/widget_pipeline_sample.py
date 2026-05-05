#!/usr/bin/env python3
"""Dry-run sample harness skeleton for the widget pipeline.

This CLI only writes to the requested --out directory. It does not touch live
window-manager, shell, KDE, Quickshell, Eww, AGS, Fabric, or desktop config
paths.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from workflow.widget_pipeline.asset_compiler import compile_assets_for_contracts
from workflow.widget_pipeline.contract_normalizer import normalize_regions
from workflow.widget_pipeline.adapters.quickshell import scaffold_quickshell_sandbox
from workflow.widget_pipeline.fake_renderer import render_fake_widgets
from workflow.widget_pipeline.function_validate import validate_contract_actions, validate_rendered_artifact_contracts
from workflow.widget_pipeline.models import StageResult, StageStatus, VisualScorecard, WidgetElementContract, WidgetSampleReport
from workflow.widget_pipeline.sample_fixtures import preview_regions_for_image
from workflow.widget_pipeline.safe_paths import safe_artifact_path
from workflow.widget_pipeline.segmentation import crop_regions
from workflow.widget_pipeline.runtime_visual import crop_screenshot_for_contracts, render_visual_review_html
from workflow.widget_pipeline.visual_score import score_rendered_widgets

_OUTPUT_SUBDIRS = (
    "crops",
    "contracts",
    "assets",
    "rendered",
    "rendered-real",
    "comparisons",
    "sandbox",
    "screenshots",
    "reports",
)

_SKIP_STAGES = (
    ("runtime-launch", "dry-run"),
    ("desktop-promotion", "dry-run"),
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a dry widget-pipeline sample harness.")
    parser.add_argument("--image", required=True, help="Path to a source widget/dashboard image.")
    parser.add_argument("--out", required=True, help="Output directory for isolated dry-run artifacts.")
    parser.add_argument("--framework", default="quickshell", help="Target framework label (default: quickshell).")
    parser.add_argument("--renderer", choices=("fake", "quickshell"), default="fake", help="Renderer path: fake PNGs or Quickshell sandbox codegen.")
    parser.add_argument("--no-launch", action="store_true", help="For Quickshell renderer, generate sandbox files without attempting runtime launch.")
    parser.add_argument(
        "--preview-texture",
        action="store_true",
        help="For Quickshell renderer, use target crops as sandbox Image textures to test the visual-scoring upper bound.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Keep live-only stages disabled.")
    parser.add_argument("--strict", action="store_true", help="Reserved for future strict validation gates.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.dry_run:
        print("error: Milestone 1 widget sample harness is dry-run only; pass --dry-run", file=sys.stderr)
        return 5

    image_path = Path(args.image).expanduser()
    output_dir = Path(args.out).expanduser()

    if not image_path.exists() or not image_path.is_file():
        print(f"error: image does not exist: {image_path}", file=sys.stderr)
        return 2

    try:
        from PIL import Image
    except ImportError:
        print("error: Pillow is required to load the source image; install the 'pillow' package.", file=sys.stderr)
        return 3

    try:
        with Image.open(image_path) as image:
            image_dimensions = tuple(int(value) for value in image.size)
    except Exception as exc:  # pragma: no cover - defensive clarity for corrupt fixtures
        print(f"error: failed to load image with Pillow: {image_path}: {exc}", file=sys.stderr)
        return 4

    paths = create_output_dirs(output_dir)
    regions = preview_regions_for_image(image_path)
    segmentation_reason = _segmentation_reason(regions)
    cropped_regions = crop_regions(image_path, regions, paths["crops"])
    contracts = normalize_regions(cropped_regions)
    contract_artifacts = write_contracts(contracts, paths["contracts"])
    asset_bundle, asset_stage = compile_assets_for_contracts(contracts, output_dir)
    rendered_results: list[dict[str, str]] = []
    visual_scores: list[VisualScorecard] = []
    quickshell_stage: StageResult | None = None
    runtime_stage: StageResult | None = None
    screenshot_stage: StageResult | None = None
    runtime_crop_stage: StageResult | None = None
    artifact_function_stage: StageResult | None = None
    if args.renderer == "fake":
        rendered_results, rendering_stage = render_fake_widgets(contracts, paths["rendered"], asset_bundle=asset_bundle)
        visual_scores, visual_stage = score_rendered_widgets(contracts, rendered_results, paths["comparisons"])
    else:
        sandbox = scaffold_quickshell_sandbox(
            contracts,
            output_dir,
            asset_bundle=asset_bundle,
            desktop_recipe="kde",
            no_launch=bool(args.no_launch),
            render_mode="preview_texture" if args.preview_texture else "components",
        )
        quickshell_stage = sandbox.stage
        rendering_stage = StageResult(
            "rendering",
            sandbox.stage.status,
            sandbox.stage.reason,
            artifacts=sandbox.stage.artifacts,
        )
        runtime_stage = sandbox.runtime_stage
        screenshot_stage = sandbox.screenshot_stage
        artifact_function_stage = validate_rendered_artifact_contracts(contracts, sandbox.qml_path, framework="quickshell")
        if screenshot_stage.status is StageStatus.PASS and sandbox.screenshot_path:
            sandbox_manifest = json.loads(Path(sandbox.manifest_path).read_text(encoding="utf-8"))
            rendered_results, runtime_crop_stage = crop_screenshot_for_contracts(
                sandbox.screenshot_path,
                contracts,
                paths["rendered-real"],
                render_geometry=sandbox_manifest.get("render_geometry"),
                surface_bbox=sandbox_manifest.get("runtime_surface_bbox"),
            )
            visual_scores, visual_stage = score_rendered_widgets(contracts, rendered_results, paths["comparisons"])
            review_path = render_visual_review_html(
                contracts=contracts,
                rendered_results=rendered_results,
                visual_scores=visual_scores,
                output_path=paths["reports"] / "visual-review.html",
            )
            if visual_scores and not all(score.passed for score in visual_scores):
                visual_stage = StageResult(
                    "visual-score",
                    StageStatus.FAIL,
                    "real Quickshell visual score below threshold for one or more contracts",
                    artifacts=tuple(visual_stage.artifacts) + (str(review_path),),
                )
            else:
                visual_stage = StageResult(
                    "visual-score",
                    visual_stage.status,
                    "real Quickshell screenshot visual comparisons produced",
                    artifacts=tuple(visual_stage.artifacts) + (str(review_path),),
                )
        else:
            visual_stage = StageResult(
                "visual-score",
                StageStatus.SKIP,
                "real visual score requires screenshot capture from sandbox runtime",
            )
    function_stage = validate_contract_actions(contracts, desktop_recipe="kde")

    report = build_report(
        framework=args.framework,
        dry_run=bool(args.dry_run),
        image_path=image_path,
        output_dir=output_dir,
        crop_artifacts=tuple(str(region["crop_path"]) for region in cropped_regions),
        contract_artifacts=contract_artifacts,
        asset_stage=asset_stage,
        quickshell_stage=quickshell_stage,
        rendering_stage=rendering_stage,
        visual_stage=visual_stage,
        function_stage=function_stage,
        artifact_function_stage=artifact_function_stage,
        runtime_stage=runtime_stage,
        screenshot_stage=screenshot_stage,
        runtime_crop_stage=runtime_crop_stage,
        contracts=tuple(contracts),
        visual_scores=tuple(visual_scores),
        segmentation_reason=segmentation_reason,
    )
    report_data = report.to_dict()
    report_data["image_dimensions"] = list(image_dimensions)
    report_data["strict"] = bool(args.strict)
    report_data["renderer"] = str(args.renderer)
    report_data["no_launch"] = bool(args.no_launch)
    report_data["preview_texture"] = bool(args.preview_texture)

    report_json = paths["reports"] / "report.json"
    report_md = paths["reports"] / "report.md"
    report_json.write_text(json.dumps(report_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md.write_text(render_markdown_report(report_data), encoding="utf-8")

    print(f"wrote widget pipeline dry-run reports to {paths['reports']}")
    return 0


def create_output_dirs(output_dir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    if output_dir.is_symlink():
        raise ValueError(f"output directory must not be a symlink: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_root = output_dir.resolve()
    for name in _OUTPUT_SUBDIRS:
        path = output_dir / name
        if path.is_symlink():
            raise ValueError(f"managed output subdirectory must not be a symlink: {path}")
        path.mkdir(parents=True, exist_ok=True)
        if not path.resolve().is_relative_to(output_root):
            raise ValueError(f"managed output subdirectory escapes output root: {path}")
        paths[name] = path
    return paths


def _segmentation_reason(regions: Sequence[dict[str, object]]) -> str:
    method = str(regions[0].get("segmentation_method", "") if regions else "")
    if method == "detected_preview_ui_cluster":
        return f"detected preview UI cluster and cropped {len(regions)} fixture-aligned regions"
    if method == "fixed_fixture_fallback":
        return f"cropped {len(regions)} deterministic fixture regions (no preview UI cluster detected)"
    return f"cropped {len(regions)} widget regions"


def write_contracts(contracts: Sequence[WidgetElementContract], contracts_dir: Path) -> tuple[str, ...]:
    artifacts: list[str] = []
    contract_dicts = [contract.to_dict() for contract in contracts]
    for contract, payload in zip(contracts, contract_dicts, strict=True):
        path = safe_artifact_path(contracts_dir, contract.id, ".json")
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts.append(str(path))

    aggregate_path = contracts_dir / "contracts.json"
    aggregate_path.write_text(json.dumps(contract_dicts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifacts.append(str(aggregate_path))
    return tuple(artifacts)


def build_report(
    *,
    framework: str,
    dry_run: bool,
    image_path: Path,
    output_dir: Path,
    crop_artifacts: Sequence[str] = (),
    contract_artifacts: Sequence[str] = (),
    asset_stage: StageResult | None = None,
    quickshell_stage: StageResult | None = None,
    rendering_stage: StageResult | None = None,
    visual_stage: StageResult | None = None,
    function_stage: StageResult | None = None,
    artifact_function_stage: StageResult | None = None,
    runtime_stage: StageResult | None = None,
    screenshot_stage: StageResult | None = None,
    runtime_crop_stage: StageResult | None = None,
    contracts: Sequence[WidgetElementContract] = (),
    visual_scores: Sequence[VisualScorecard] = (),
    segmentation_reason: str = "",
) -> WidgetSampleReport:
    stages = [
        StageResult(
            name="preview-source",
            status=StageStatus.PASS,
            reason="source image loaded",
            artifacts=(str(image_path),),
        ),
        StageResult(
            name="segmentation",
            status=StageStatus.PASS,
            reason=segmentation_reason or f"cropped {len(crop_artifacts)} deterministic fixture regions",
            artifacts=tuple(crop_artifacts),
        ),
        StageResult(
            name="contracts",
            status=StageStatus.PASS,
            reason=f"normalized {len(contracts)} widget contracts",
            artifacts=tuple(contract_artifacts),
        ),
    ]
    stages.append(asset_stage or StageResult("assets", StageStatus.SKIP, "no ornate/textured assets required"))
    if quickshell_stage is not None:
        stages.append(quickshell_stage)
    stages.append(rendering_stage or StageResult("rendering", StageStatus.SKIP, "not run"))
    if screenshot_stage is not None:
        stages.append(screenshot_stage)
    if runtime_crop_stage is not None:
        stages.append(runtime_crop_stage)
    stages.append(visual_stage or StageResult("visual-score", StageStatus.SKIP, "not run"))
    stages.append(function_stage or StageResult("function-validation", StageStatus.SKIP, "not run"))
    stages.append(artifact_function_stage or StageResult("artifact-function-validation", StageStatus.SKIP, "no generated framework artifact"))
    stages.append(runtime_stage or StageResult("runtime-launch", StageStatus.SKIP, "dry-run"))
    stages.append(StageResult(name="desktop-promotion", status=StageStatus.SKIP, reason="dry-run"))
    return WidgetSampleReport(
        framework=framework,
        dry_run=dry_run,
        image_path=str(image_path),
        output_dir=str(output_dir),
        stages=tuple(stages),
        contracts=tuple(contracts),
        visual_scores=tuple(visual_scores),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def render_markdown_report(report: dict[str, object]) -> str:
    lines = [
        "# Widget Pipeline Sample Report",
        "",
        f"- Framework: {report['framework']}",
        f"- Renderer: {report.get('renderer', 'fake')}",
        f"- Dry run: {report['dry_run']}",
        f"- No launch: {report.get('no_launch', False)}",
        f"- Strict: {report['strict']}",
        f"- Image: {report['image_path']}",
        f"- Image dimensions: {report['image_dimensions']}",
        f"- Output directory: {report['output_dir']}",
        f"- Generated at: {report['generated_at']}",
        "",
        "## Stages",
        "",
        "| Stage | Status | Reason |",
        "| --- | --- | --- |",
    ]
    for stage in report["stages"]:  # type: ignore[index]
        lines.append(f"| {stage['name']} | {stage['status']} | {stage['reason']} |")
    lines.append("")
    lines.extend([
        "## Visual Scores",
        "",
        "| Contract | Total | Loss | Passed | Comparison |",
        "| --- | ---: | ---: | --- | --- |",
    ])
    visual_scores = report.get("visual_scores", [])  # type: ignore[assignment]
    if visual_scores:
        for score in visual_scores:  # type: ignore[union-attr]
            lines.append(
                f"| {score['contract_id']} | {score['total']} | {score['loss']} | {score['passed']} | {score['comparison_path']} |"
            )
    else:
        lines.append("| none | 0 | 0 | False |  |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
