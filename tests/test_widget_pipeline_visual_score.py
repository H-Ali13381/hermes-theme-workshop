from __future__ import annotations

from pathlib import Path

import pytest

from workflow.widget_pipeline.fake_renderer import render_fake_widgets
from workflow.widget_pipeline.models import StageStatus, VisualScorecard, WidgetElementContract
from workflow.widget_pipeline.visual_score import score_rendered_widgets


def test_fake_renderer_and_visual_scorer_write_png_artifacts(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    crop_path = tmp_path / "target.png"
    Image.new("RGBA", (32, 18), (24, 18, 20, 255)).save(crop_path)
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 32, 18),
        crop_path=str(crop_path),
        dimensions=(32, 18),
        expected_text=("12:00",),
    )

    rendered_results, rendering_stage = render_fake_widgets([contract], tmp_path / "rendered")

    assert rendering_stage.name == "rendering"
    assert rendering_stage.status == StageStatus.PASS
    assert len(rendered_results) == 1
    rendered_path = Path(rendered_results[0]["rendered_path"])
    assert rendered_results[0]["contract_id"] == "clock"
    assert rendered_path.is_file()
    with Image.open(rendered_path) as rendered:
        assert rendered.size == (32, 18)

    scorecards, visual_stage = score_rendered_widgets([contract], rendered_results, tmp_path / "comparisons")

    assert visual_stage.name == "visual-score"
    assert visual_stage.status == StageStatus.PASS
    assert len(scorecards) == 1
    assert isinstance(scorecards[0], VisualScorecard)
    assert scorecards[0].contract_id == "clock"
    assert 0.0 <= scorecards[0].loss <= 1.0
    assert 0.0 <= scorecards[0].total <= 10.0
    comparison_path = Path(scorecards[0].comparison_path)
    assert comparison_path.is_file()
    with Image.open(comparison_path) as comparison:
        assert comparison.size == (66, 18)


def test_visual_scorer_returns_fail_stage_for_missing_crop(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    rendered_path = tmp_path / "rendered.png"
    Image.new("RGBA", (32, 18), (24, 18, 20, 255)).save(rendered_path)
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 32, 18),
        crop_path=str(tmp_path / "missing-target.png"),
        dimensions=(32, 18),
    )

    scores, stage = score_rendered_widgets(
        [contract],
        [{"contract_id": "clock", "rendered_path": str(rendered_path)}],
        tmp_path / "comparisons",
    )

    assert scores == []
    assert stage.status is StageStatus.FAIL
    assert "failed to compare clock" in stage.reason
