"""Widget pipeline contracts and dry-run harness helpers."""

from __future__ import annotations

from .adapters.quickshell import scaffold_quickshell_sandbox
from .asset_compiler import compile_assets_for_contracts
from .contract_normalizer import normalize_regions
from .fake_renderer import render_fake_widgets
from .function_validate import validate_contract_actions, validate_rendered_artifact_contracts
from .models import (
    StageResult,
    StageStatus,
    VisualScorecard,
    WidgetAction,
    WidgetElementContract,
    WidgetSampleReport,
)
from .safe_paths import safe_artifact_path
from .sample_fixtures import preview_regions_for_image, sample_regions_for_image
from .segmentation import crop_regions
from .visual_score import score_rendered_widgets

__all__ = [
    "compile_assets_for_contracts",
    "render_fake_widgets",
    "score_rendered_widgets",
    "StageResult",
    "StageStatus",
    "VisualScorecard",
    "WidgetAction",
    "WidgetElementContract",
    "WidgetSampleReport",
    "crop_regions",
    "normalize_regions",
    "preview_regions_for_image",
    "sample_regions_for_image",
    "safe_artifact_path",
    "scaffold_quickshell_sandbox",
    "validate_contract_actions",
    "validate_rendered_artifact_contracts",
]
