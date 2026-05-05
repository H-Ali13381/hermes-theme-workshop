from __future__ import annotations

from pathlib import Path

import pytest

from workflow.widget_pipeline.models import WidgetElementContract
from workflow.widget_pipeline.runtime_visual import crop_screenshot_for_contracts, render_visual_review_html
from workflow.widget_pipeline.visual_score import score_rendered_widgets


def test_crop_screenshot_for_contracts_scores_and_writes_review_html(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    target = tmp_path / "target.png"
    screenshot = tmp_path / "screenshot.png"
    Image.new("RGBA", (40, 20), (120, 40, 30, 255)).save(target)
    Image.new("RGBA", (100, 60), (20, 20, 20, 255)).save(screenshot)
    with Image.open(screenshot) as image:
        image.paste((120, 40, 30, 255), (5, 6, 45, 26))
        image.save(screenshot)
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(5, 6, 40, 20),
        crop_path=str(target),
        dimensions=(40, 20),
    )

    rendered_results, crop_stage = crop_screenshot_for_contracts(
        screenshot, (contract,), tmp_path / "rendered-real"
    )
    scores, score_stage = score_rendered_widgets((contract,), rendered_results, tmp_path / "comparisons")
    review_path = render_visual_review_html(
        contracts=(contract,),
        rendered_results=rendered_results,
        visual_scores=scores,
        output_path=tmp_path / "reports" / "visual-review.html",
    )

    assert crop_stage.status.value == "PASS"
    assert Path(rendered_results[0]["rendered_path"]).is_file()
    assert score_stage.status.value == "PASS"
    assert scores[0].passed is True
    assert review_path.is_file()
    html = review_path.read_text(encoding="utf-8")
    assert "target crop" in html
    assert "real Quickshell render" in html
    assert "diff" in html
    assert "clock" in html
    for artifact in (rendered_results[0]["rendered_path"], scores[0].comparison_path, str(review_path)):
        assert Path(artifact).resolve().is_relative_to(tmp_path.resolve())


def test_crop_screenshot_for_contracts_localizes_quickshell_surface(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    target = tmp_path / "target.png"
    screenshot = tmp_path / "screenshot.png"
    Image.new("RGBA", (16, 10), (231, 196, 116, 255)).save(target)
    image = Image.new("RGBA", (120, 80), (20, 20, 20, 255))
    surface_x, surface_y, surface_w, surface_h = 50, 23, 42, 30
    image.paste((19, 14, 16, 255), (surface_x, surface_y, surface_x + surface_w, surface_y + surface_h))
    # Quickshell sandbox signature: gold border around the actual rendered surface.
    image.paste((196, 145, 55, 255), (surface_x, surface_y, surface_x + surface_w, surface_y + 1))
    image.paste((196, 145, 55, 255), (surface_x, surface_y + surface_h - 1, surface_x + surface_w, surface_y + surface_h))
    image.paste((196, 145, 55, 255), (surface_x, surface_y, surface_x + 1, surface_y + surface_h))
    image.paste((196, 145, 55, 255), (surface_x + surface_w - 1, surface_y, surface_x + surface_w, surface_y + surface_h))
    image.paste((231, 196, 116, 255), (surface_x + 7, surface_y + 9, surface_x + 23, surface_y + 19))
    image.save(screenshot)
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 16, 10),
        crop_path=str(target),
        dimensions=(16, 10),
    )
    render_geometry = {
        "surface": {"width": surface_w, "height": surface_h, "margin": 0, "spacing": 0},
        "contracts": {"clock": [7, 9, 16, 10]},
    }

    rendered_results, crop_stage = crop_screenshot_for_contracts(
        screenshot, (contract,), tmp_path / "rendered-real", render_geometry=render_geometry
    )

    assert crop_stage.status.value == "PASS"
    assert "localized surface" in crop_stage.reason
    rendered = Path(rendered_results[0]["rendered_path"])
    with Image.open(rendered) as rendered_image:
        assert rendered_image.convert("RGBA").getpixel((0, 0)) == (231, 196, 116, 255)


def test_crop_screenshot_for_contracts_maps_scaled_surface_bbox(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    target = tmp_path / "target.png"
    screenshot = tmp_path / "screenshot.png"
    Image.new("RGBA", (32, 20), (231, 196, 116, 255)).save(target)
    image = Image.new("RGBA", (180, 120), (20, 20, 20, 255))
    surface_x, surface_y = 50, 24
    # Logical surface is 42x30, but compositor screenshot is 2x physical pixels.
    image.paste((19, 14, 16, 255), (surface_x, surface_y, surface_x + 84, surface_y + 60))
    image.paste((231, 196, 116, 255), (surface_x + 14, surface_y + 18, surface_x + 46, surface_y + 38))
    image.save(screenshot)
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 16, 10),
        crop_path=str(target),
        dimensions=(16, 10),
    )

    rendered_results, crop_stage = crop_screenshot_for_contracts(
        screenshot,
        (contract,),
        tmp_path / "rendered-real",
        render_geometry={"surface": {"width": 42, "height": 30}, "contracts": {"clock": [7, 9, 16, 10]}},
        surface_bbox=[surface_x, surface_y, 84, 60],
    )

    assert crop_stage.status.value == "PASS"
    with Image.open(rendered_results[0]["rendered_path"]) as rendered_image:
        assert rendered_image.size == (32, 20)
        assert rendered_image.convert("RGBA").getpixel((0, 0)) == (231, 196, 116, 255)


def test_crop_screenshot_for_contracts_fails_when_geometry_surface_missing(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    target = tmp_path / "target.png"
    screenshot = tmp_path / "screenshot.png"
    Image.new("RGBA", (16, 10), (231, 196, 116, 255)).save(target)
    Image.new("RGBA", (120, 80), (20, 20, 20, 255)).save(screenshot)
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 16, 10),
        crop_path=str(target),
        dimensions=(16, 10),
    )

    rendered_results, crop_stage = crop_screenshot_for_contracts(
        screenshot,
        (contract,),
        tmp_path / "rendered-real",
        render_geometry={"surface": {"width": 42, "height": 30}, "contracts": {"clock": [7, 9, 16, 10]}},
    )

    assert rendered_results == []
    assert crop_stage.status.value == "FAIL"
    assert "could not localize" in crop_stage.reason
