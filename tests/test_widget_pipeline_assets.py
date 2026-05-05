from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from workflow.widget_pipeline.asset_compiler import compile_assets_for_contracts  # noqa: E402
from workflow.widget_pipeline.contract_normalizer import normalize_regions  # noqa: E402
from workflow.widget_pipeline.models import StageStatus, WidgetElementContract  # noqa: E402
from workflow.widget_pipeline.sample_fixtures import sample_regions_for_image  # noqa: E402


def test_sample_fixture_contracts_compile_ornate_assets(tmp_path: Path) -> None:
    pytest.importorskip("PIL.Image")
    contracts = normalize_regions(sample_regions_for_image(1376, 768))

    bundle, stage = compile_assets_for_contracts(contracts, tmp_path)

    assert bundle is not None
    assert bundle.theme_slug == "sample-widget-hud"
    assert stage.name == "assets"
    assert stage.status is StageStatus.PASS
    assert "generated 3 deterministic ornate texture assets" in stage.reason

    bundle_json = tmp_path / "assets" / "sample-widget-hud" / "texture_bundle.json"
    contact_sheet = tmp_path / "assets" / "sample-widget-hud" / "asset_contact_sheet.png"
    assert bundle_json.is_file()
    assert contact_sheet.is_file()

    metadata = json.loads(bundle_json.read_text(encoding="utf-8"))
    assert [asset["variant"] for asset in metadata["assets"]] == ["panel", "button", "slot"]
    assert {Path(asset["path"]).name for asset in metadata["assets"]} == {
        "panel_ornate_9slice.png",
        "button_ornate_9slice.png",
        "slot_ornate_9slice.png",
    }
    for asset in metadata["assets"]:
        assert (tmp_path / asset["path"]).is_file()

    assert str(bundle_json) in stage.artifacts
    assert str(contact_sheet) in stage.artifacts
    for asset in bundle.assets:
        assert str(tmp_path / asset.path) in stage.artifacts


def test_plain_non_ornate_contract_skips_assets(tmp_path: Path) -> None:
    contract = WidgetElementContract(
        id="plain_label",
        role="label",
        bbox=(0, 0, 100, 20),
        crop_path="",
        visual_traits=("flat text label", "minimal monochrome typography"),
        hard_requirements=("render readable text", "avoid decorative imagery"),
    )

    bundle, stage = compile_assets_for_contracts([contract], tmp_path)

    assert bundle is None
    assert stage.name == "assets"
    assert stage.status is StageStatus.SKIP
    assert stage.reason == "no ornate/textured assets required"
    assert stage.artifacts == ()
    assert not (tmp_path / "assets" / "sample-widget-hud" / "texture_bundle.json").exists()
