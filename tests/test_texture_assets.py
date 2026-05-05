from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from workflow.nodes.craft.texture_assets import (  # noqa: E402
    TextureIntent,
    declared_asset_paths,
    extract_texture_intent,
    generate_texture_bundle,
    needs_texture_assets,
    referenced_borderimage_sources,
    seam_distance,
    validate_texture_bundle,
)


BONFIRE_DESIGN = {
    "name": "bonfire-blackiron",
    "description": "Diablo RPG menu, ornate thorn carved borderimage blackiron shell chrome",
    "palette": {
        "bg": "#111513",
        "soot": "#252623",
        "iron": "#6b4b2f",
        "bone": "#d6c8aa",
        "ember": "#d06f22",
        "amber": "#f0a33a",
    },
}


def test_needs_texture_assets_only_for_ornate_quickshell():
    assert needs_texture_assets("widgets:quickshell", BONFIRE_DESIGN)
    assert not needs_texture_assets("widgets:eww", BONFIRE_DESIGN)
    assert not needs_texture_assets("widgets:quickshell", {"name": "plain", "palette": {"bg": "#000000"}})


def test_extract_texture_intent_is_deterministic_and_slugged():
    one = extract_texture_intent(BONFIRE_DESIGN)
    two = extract_texture_intent(json.loads(json.dumps(BONFIRE_DESIGN)))
    assert one == two
    assert one.theme_slug == "bonfire-blackiron"
    assert one.variants == ("panel", "button", "slot")


def test_generate_texture_bundle_writes_pngs_and_metadata():
    with tempfile.TemporaryDirectory() as tmp:
        bundle = generate_texture_bundle(extract_texture_intent(BONFIRE_DESIGN), Path(tmp))
        reasons = validate_texture_bundle(bundle)
        assert reasons == []
        assert len(bundle.assets) == 3
        assert (Path(tmp) / bundle.metadata_path).exists()
        for asset in bundle.assets:
            path = Path(tmp) / asset.path
            assert path.exists()
            assert path.suffix == ".png"
            assert asset.width >= 96
            assert asset.height >= 96
            assert asset.slice_px > 0
            assert asset.seam_score <= 16.0
            assert len(asset.sha256) == 64


def test_generated_assets_are_tileable_by_seam_metric():
    with tempfile.TemporaryDirectory() as tmp:
        bundle = generate_texture_bundle(TextureIntent(theme_slug="bonfire"), Path(tmp))
        # Re-open each image and independently recompute the seam metric.
        from PIL import Image
        for asset in bundle.assets:
            image = Image.open(Path(tmp) / asset.path)
            assert seam_distance(image) <= 16.0


def test_validate_texture_bundle_flags_missing_asset():
    with tempfile.TemporaryDirectory() as tmp:
        bundle = generate_texture_bundle(extract_texture_intent(BONFIRE_DESIGN), Path(tmp))
        (Path(tmp) / bundle.assets[0].path).unlink()
        reasons = validate_texture_bundle(bundle)
        assert any("missing on disk" in reason for reason in reasons)


def test_declared_and_referenced_asset_path_helpers():
    texture_assets = {"assets": [{"path": "assets/bonfire/panel_ornate_9slice.png"}]}
    qml = "BorderImage { source: 'assets/bonfire/panel_ornate_9slice.png' } Image { source: 'https://example.com/x.png' }"
    assert declared_asset_paths(texture_assets) == {"assets/bonfire/panel_ornate_9slice.png"}
    assert referenced_borderimage_sources(qml) == {"assets/bonfire/panel_ornate_9slice.png"}


def test_texture_and_codegen_import_without_pillow():
    code = """
import builtins
from pathlib import Path

real_import = builtins.__import__

def blocked_import(name, *args, **kwargs):
    if name == "PIL" or name.startswith("PIL."):
        raise ImportError("blocked Pillow import")
    return real_import(name, *args, **kwargs)

builtins.__import__ = blocked_import

from workflow.nodes.craft import codegen
from workflow.nodes.craft import texture_assets

assert texture_assets.needs_texture_assets("widgets:quickshell", {"description": "ornate RPG menu"})
assert codegen._format_texture_assets({"assets": [{"path": "assets/t/panel.png"}]})

try:
    texture_assets.generate_texture_bundle(texture_assets.TextureIntent(theme_slug="missing-pillow"), Path("/tmp/missing-pillow"))
except RuntimeError as exc:
    assert "Pillow is required for texture asset generation" in str(exc)
else:
    raise AssertionError("expected texture generation to fail without Pillow")
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
