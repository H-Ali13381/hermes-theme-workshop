"""Deterministic ornate asset compilation for widget contracts.

This MVP stays sandboxed under the caller-provided output root and reuses the
existing craft texture generator for deterministic 9-slice PNG bundles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from workflow.nodes.craft.texture_assets import (
    TextureBundle,
    extract_texture_intent,
    generate_texture_bundle,
    validate_texture_bundle,
)

from .models import StageResult, StageStatus, WidgetElementContract

_ASSET_TERMS = (
    "ornate",
    "fantasy",
    "hud",
    "frame",
    "trim",
    "button",
    "slot",
    "plaque",
    "meter",
    "panel",
)

_DEFAULT_PALETTE = {
    "background": "#111513",
    "soot": "#252623",
    "iron": "#6b4b2f",
    "bone": "#d6c8aa",
    "ember": "#d06f22",
    "amber": "#f0a33a",
}


def compile_assets_for_contracts(
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    output_root: str | Path,
    theme_slug: str = "sample-widget-hud",
) -> tuple[TextureBundle | None, StageResult]:
    """Generate ornate texture assets needed by widget contracts.

    Returns ``(None, SKIP)`` when no visual trait or hard requirement asks for
    ornate/textured chrome. On generation, artifacts are absolute paths under
    ``output_root/assets/<theme_slug>/`` only.
    """

    normalized_contracts = tuple(_coerce_contract(contract) for contract in contracts)
    output_root = Path(output_root).expanduser().resolve()

    if not _contracts_need_assets(normalized_contracts):
        return None, StageResult("assets", StageStatus.SKIP, "no ornate/textured assets required")

    try:
        _load_pillow_for_contact_sheet()
    except RuntimeError as exc:
        return None, StageResult("assets", StageStatus.FAIL, str(exc))

    design = _design_for_contracts(normalized_contracts, theme_slug)
    intent = extract_texture_intent(design)

    try:
        bundle = generate_texture_bundle(intent, output_root)
    except RuntimeError as exc:
        return None, StageResult("assets", StageStatus.FAIL, str(exc))

    reasons = validate_texture_bundle(bundle)
    contact_sheet_path: Path | None = None
    try:
        contact_sheet_path = _write_contact_sheet(bundle, output_root)
    except RuntimeError as exc:
        reasons.append(str(exc))

    artifacts = _artifact_paths(bundle, output_root, contact_sheet_path)
    if reasons:
        return bundle, StageResult(
            "assets",
            StageStatus.FAIL,
            "texture asset validation failed: " + "; ".join(reasons),
            artifacts=artifacts,
        )

    return bundle, StageResult(
        "assets",
        StageStatus.PASS,
        f"generated {len(bundle.assets)} deterministic ornate texture assets",
        artifacts=artifacts,
    )


def _contracts_need_assets(contracts: Iterable[WidgetElementContract]) -> bool:
    return any(_contract_needs_assets(contract) for contract in contracts)


def _contract_needs_assets(contract: WidgetElementContract) -> bool:
    haystack = " ".join((*contract.visual_traits, *contract.hard_requirements)).lower()
    return any(term in haystack for term in _ASSET_TERMS)


def _coerce_contract(contract: WidgetElementContract | dict[str, Any]) -> WidgetElementContract:
    if isinstance(contract, WidgetElementContract):
        return contract
    return WidgetElementContract.from_dict(contract)


def _design_for_contracts(contracts: tuple[WidgetElementContract, ...], theme_slug: str) -> dict[str, Any]:
    traits: list[str] = []
    requirements: list[str] = []
    for contract in contracts:
        traits.extend(contract.visual_traits)
        requirements.extend(contract.hard_requirements)
    return {
        "name": theme_slug,
        "palette": dict(_DEFAULT_PALETTE),
        "description": "deterministic fantasy HUD ornate panel frame trim button slot meter chrome",
        "visual_traits": traits,
        "hard_requirements": requirements,
        "variants": ["panel", "button", "slot"],
    }


def _load_pillow_for_contact_sheet() -> tuple[Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - exercised only without Pillow installed
        raise RuntimeError(
            "Pillow is required to generate asset contact sheets; install the 'pillow' package."
        ) from exc
    return Image, ImageDraw, ImageFont


def _write_contact_sheet(bundle: TextureBundle, output_root: Path) -> Path:
    Image, ImageDraw, ImageFont = _load_pillow_for_contact_sheet()
    root = Path(output_root)
    asset_paths = [root / asset.path for asset in bundle.assets]
    missing = [str(path) for path in asset_paths if not path.exists()]
    if missing:
        raise RuntimeError("cannot generate asset contact sheet; missing assets: " + ", ".join(missing))

    cell_w = 224
    cell_h = 244
    padding = 16
    label_h = 28
    sheet_w = padding + len(bundle.assets) * cell_w + padding
    sheet_h = padding + label_h + 192 + padding
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (12, 13, 12, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, asset in enumerate(bundle.assets):
        x = padding + index * cell_w
        y = padding
        draw.text((x, y), f"{asset.variant} / slice {asset.slice_px}px", fill=(230, 214, 176, 255), font=font)
        with Image.open(root / asset.path) as img:
            preview = img.convert("RGBA")
            preview.thumbnail((192, 192))
            px = x + (192 - preview.width) // 2
            py = y + label_h + (192 - preview.height) // 2
            draw.rectangle((x - 4, y + label_h - 4, x + 196, y + label_h + 196), outline=(107, 75, 47, 255))
            sheet.alpha_composite(preview, (px, py))

    contact_sheet = root / "assets" / bundle.theme_slug / "asset_contact_sheet.png"
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet)
    return contact_sheet


def _artifact_paths(bundle: TextureBundle, output_root: Path, contact_sheet_path: Path | None) -> tuple[str, ...]:
    root = Path(output_root)
    artifacts = [str(root / bundle.metadata_path)]
    if contact_sheet_path is not None:
        artifacts.append(str(contact_sheet_path))
    artifacts.extend(str(root / asset.path) for asset in bundle.assets)
    return tuple(artifacts)
