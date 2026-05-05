from __future__ import annotations

from pathlib import Path

import pytest

from workflow.widget_pipeline.contract_normalizer import normalize_regions
from workflow.widget_pipeline.sample_fixtures import sample_regions_for_image
from workflow.widget_pipeline.segmentation import crop_regions

EXPECTED_IDS = {"full_hud", "workspace_group", "clock", "status_bars", "power_button"}


def test_sample_regions_scale_inside_tiny_image_and_crop_all_ids(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "tiny.png"
    crops_dir = tmp_path / "crops"
    Image.new("RGBA", (23, 11), (10, 20, 30, 255)).save(image_path)

    regions = sample_regions_for_image(23, 11)

    assert {region["id"] for region in regions} == EXPECTED_IDS
    for region in regions:
        x, y, w, h = region["bbox"]
        assert x >= 0
        assert y >= 0
        assert w > 0
        assert h > 0
        assert x + w <= 23
        assert y + h <= 11

    cropped = crop_regions(image_path, regions, crops_dir)

    assert {region["id"] for region in cropped} == EXPECTED_IDS
    for region in cropped:
        crop_path = Path(region["crop_path"])
        assert crop_path.is_file()
        assert crop_path.name == f"{region['id']}.png"
        assert tuple(region["dimensions"]) == tuple(region["bbox"][2:4])
        with Image.open(crop_path) as crop:
            assert crop.size == tuple(region["dimensions"])

    contracts = normalize_regions(cropped)
    assert {contract.id for contract in contracts} == EXPECTED_IDS
    assert all(contract.crop_path for contract in contracts)
    assert all(contract.dimensions[0] > 0 and contract.dimensions[1] > 0 for contract in contracts)

    workspace = next(contract for contract in contracts if contract.id == "workspace_group")
    assert [action.id for action in workspace.actions] == [
        "workspace-1",
        "workspace-2",
        "workspace-3",
        "workspace-4",
        "workspace-5",
    ]
    assert all(action.command for action in workspace.actions)
    assert all("org.kde.KWin.setCurrentDesktop" in str(action.command) for action in workspace.actions)
    assert not any(action.decorative for action in workspace.actions)

    power = next(contract for contract in contracts if contract.id == "power_button")
    assert len(power.actions) == 1
    assert power.actions[0].command != "qdbus6 org.kde.krunner /App org.kde.krunner.App.query power"
    assert "krunner" not in str(power.actions[0].command).lower()
    assert "hover" in power.actions[0].visual_states
    assert "pressed" in power.actions[0].visual_states
    assert power.actions[0].decorative is False


def test_crop_regions_rejects_invalid_bbox(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "source.png"
    Image.new("RGBA", (10, 10), (0, 0, 0, 255)).save(image_path)

    with pytest.raises(ValueError, match="width and height must be positive"):
        crop_regions(image_path, [{"id": "bad", "bbox": (1, 1, 0, 5)}], tmp_path / "crops")

    with pytest.raises(ValueError, match="exceeds image bounds"):
        crop_regions(image_path, [{"id": "bad", "bbox": (8, 8, 5, 5)}], tmp_path / "crops")


def test_crop_regions_rejects_path_traversal_ids(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "source.png"
    Image.new("RGBA", (10, 10), (0, 0, 0, 255)).save(image_path)

    with pytest.raises(ValueError, match="unsafe widget artifact id"):
        crop_regions(image_path, [{"id": "../../escape", "bbox": (1, 1, 5, 5)}], tmp_path / "crops")

    assert not (tmp_path / "escape.png").exists()
