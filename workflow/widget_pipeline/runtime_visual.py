"""Runtime screenshot crop and review helpers for widget visual validation."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import StageResult, StageStatus, VisualScorecard, WidgetElementContract
from .safe_paths import safe_artifact_path


def crop_screenshot_for_contracts(
    screenshot_path: str | Path,
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    rendered_dir: str | Path,
    *,
    render_geometry: Mapping[str, Any] | None = None,
    surface_bbox: tuple[int, int, int, int] | list[int] | None = None,
) -> tuple[list[dict[str, str]], StageResult]:
    """Crop a runtime screenshot into per-contract rendered artifacts.

    When Quickshell render geometry is available, locate the sandbox surface in
    the full desktop screenshot and translate framework-local boxes to screen
    coordinates. Without geometry, fall back to the original contract bboxes.
    """

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("Pillow is required to crop runtime screenshots") from exc

    screenshot = Path(screenshot_path).expanduser().resolve()
    rendered_root = Path(rendered_dir)
    rendered_root.mkdir(parents=True, exist_ok=True)
    rendered_results: list[dict[str, str]] = []
    artifacts: list[str] = []

    try:
        with Image.open(screenshot) as image:
            rgba = image.convert("RGBA")
            image_width, image_height = rgba.size
            contracts_tuple = tuple(_coerce_contract(item) for item in contracts)
            localized_surface_bbox = _coerce_bbox(surface_bbox) if surface_bbox is not None else None
            if localized_surface_bbox is None and render_geometry:
                localized_surface_bbox = _locate_surface_bbox(rgba, render_geometry)
            if render_geometry and localized_surface_bbox is None:
                return rendered_results, StageResult(
                    "runtime-rendered-crops",
                    StageStatus.FAIL,
                    "could not localize Quickshell sandbox surface in screenshot",
                    artifacts=tuple(artifacts),
                )
            for contract in contracts_tuple:
                x, y, width, height = _crop_box_for_contract(contract, render_geometry, localized_surface_bbox)
                left = max(0, min(image_width, x))
                top = max(0, min(image_height, y))
                right = max(left, min(image_width, x + max(1, width)))
                bottom = max(top, min(image_height, y + max(1, height)))
                if right <= left or bottom <= top:
                    return rendered_results, StageResult(
                        "runtime-rendered-crops",
                        StageStatus.FAIL,
                        f"contract {contract.id} bbox does not intersect screenshot",
                        artifacts=tuple(artifacts),
                    )
                rendered_path = safe_artifact_path(rendered_root, contract.id, ".png")
                rgba.crop((left, top, right, bottom)).save(rendered_path)
                rendered_results.append({"contract_id": contract.id, "rendered_path": str(rendered_path)})
                artifacts.append(str(rendered_path))
    except OSError as exc:
        return rendered_results, StageResult("runtime-rendered-crops", StageStatus.FAIL, f"failed to crop runtime screenshot: {exc}")

    if not rendered_results:
        return rendered_results, StageResult("runtime-rendered-crops", StageStatus.SKIP, "no contracts available for runtime crop extraction")
    return rendered_results, StageResult(
        "runtime-rendered-crops",
        StageStatus.PASS,
        (
            f"cropped {len(rendered_results)} real screenshot widget regions using localized surface"
            if render_geometry
            else f"cropped {len(rendered_results)} real screenshot widget regions"
        ),
        artifacts=tuple(artifacts),
    )


def render_visual_review_html(
    *,
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    rendered_results: Iterable[Mapping[str, Any]],
    visual_scores: Iterable[VisualScorecard | dict[str, Any]],
    output_path: str | Path,
) -> Path:
    """Write a target/render/diff review page for human visual inspection."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered_by_id = {str(item.get("contract_id", "")): str(item.get("rendered_path", "")) for item in rendered_results}
    scores_by_id = {_score_id(score): _score_dict(score) for score in visual_scores}

    lines = [
        "<!doctype html>",
        '<html><head><meta charset="utf-8"><title>Widget Runtime Visual Review</title>',
        "<style>body{background:#15110d;color:#ead8b1;font:15px system-ui;margin:24px}h1,h2{color:#f0c36a}.row{margin:24px 0;padding:16px;border:1px solid #5b3a1f;background:#221810}.grid{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap}.card{background:#0f0c09;border:1px solid #4a3324;padding:10px}.card img{max-width:360px;border:1px solid #704d2f}.meta{color:#b9a17d;font-size:13px}code{color:#f0c36a}</style>",
        "</head><body>",
        "<h1>Widget Runtime Visual Review</h1>",
        "<p>Each row shows target crop, real Quickshell render, diff/comparison, and score.</p>",
    ]
    for contract in (_coerce_contract(item) for item in contracts):
        rendered = rendered_by_id.get(contract.id, "")
        score = scores_by_id.get(contract.id, {})
        comparison = str(score.get("comparison_path", ""))
        lines.append(f'<div class="row"><h2>{escape(contract.id)}</h2><div class="grid">')
        lines.append(_image_card("target crop", contract.crop_path))
        lines.append(_image_card("real Quickshell render", rendered))
        lines.append(_image_card("diff", comparison))
        lines.append(
            '<div class="card"><strong>score</strong>'
            f'<div class="meta">total={escape(str(score.get("total", "")))}<br>'
            f'loss={escape(str(score.get("loss", "")))}<br>'
            f'passed={escape(str(score.get("passed", "")))}</div></div>'
        )
        lines.append("</div></div>")
    lines.append("</body></html>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def _coerce_bbox(value: tuple[int, int, int, int] | list[int] | None) -> tuple[int, int, int, int] | None:
    if value is None or len(value) != 4:
        return None
    try:
        x, y, width, height = (int(item) for item in value)
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    return x, y, width, height


def _crop_box_for_contract(
    contract: WidgetElementContract,
    render_geometry: Mapping[str, Any] | None,
    surface_bbox: tuple[int, int, int, int] | None,
) -> tuple[int, int, int, int]:
    if render_geometry and surface_bbox:
        contract_boxes = render_geometry.get("contracts") if isinstance(render_geometry, Mapping) else None
        local_box = contract_boxes.get(contract.id) if isinstance(contract_boxes, Mapping) else None
        if isinstance(local_box, (list, tuple)) and len(local_box) == 4:
            sx, sy, surface_width, surface_height = surface_bbox
            surface = render_geometry.get("surface") if isinstance(render_geometry, Mapping) else None
            expected_width = int(surface.get("width") or surface_width) if isinstance(surface, Mapping) else surface_width
            expected_height = int(surface.get("height") or surface_height) if isinstance(surface, Mapping) else surface_height
            scale_x = surface_width / max(1, expected_width)
            scale_y = surface_height / max(1, expected_height)
            lx, ly, width, height = (int(value) for value in local_box)
            return (
                sx + int(round(lx * scale_x)),
                sy + int(round(ly * scale_y)),
                max(1, int(round(width * scale_x))),
                max(1, int(round(height * scale_y))),
            )
    return tuple(int(value) for value in contract.bbox)  # type: ignore[return-value]


def _locate_surface_bbox(image: Any, render_geometry: Mapping[str, Any] | None) -> tuple[int, int, int, int] | None:
    if not render_geometry:
        return None
    surface = render_geometry.get("surface") if isinstance(render_geometry, Mapping) else None
    if not isinstance(surface, Mapping):
        return None
    expected_width = int(surface.get("width") or 0)
    expected_height = int(surface.get("height") or 0)
    if expected_width <= 0 or expected_height <= 0:
        return None

    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        for x in range(width):
            if _is_widget_signature_pixel(pixels[x, y]):
                xs.append(x)
                ys.append(y)

    if len(xs) < 16:
        return None

    xs.sort()
    ys.sort()
    lo = max(0, int(len(xs) * 0.02))
    hi = min(len(xs) - 1, int(len(xs) * 0.98))
    min_x, max_x = xs[lo], xs[hi]
    min_y, max_y = ys[lo], ys[hi]
    observed_width = max(1, max_x - min_x + 1)
    observed_height = max(1, max_y - min_y + 1)

    if abs(observed_width - expected_width) <= 2 and abs(observed_height - expected_height) <= 2:
        origin_x, origin_y = min_x, min_y
    elif observed_width <= expected_width * 1.4 and observed_height <= expected_height * 1.4:
        origin_x = int(round((min_x + max_x - expected_width) / 2))
        origin_y = int(round((min_y + max_y - expected_height) / 2))
    else:
        origin_x, origin_y = min_x, min_y
    origin_x = max(0, min(width - 1, origin_x))
    origin_y = max(0, min(height - 1, origin_y))
    return origin_x, origin_y, min(expected_width, width - origin_x), min(expected_height, height - origin_y)


def _is_widget_signature_pixel(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    palette = (
        (196, 145, 55),  # gold border
        (231, 196, 116), # gold text
        (242, 193, 91),  # power accent
        (132, 45, 34),   # power red
        (103, 28, 32),   # health red
        (37, 79, 94),    # mana blue
        (74, 43, 34),    # active slot brown
    )
    for pr, pg, pb in palette:
        if abs(r - pr) <= 26 and abs(g - pg) <= 26 and abs(b - pb) <= 26:
            return True
    return False


def _image_card(label: str, path: str) -> str:
    if not path:
        return f'<div class="card"><strong>{escape(label)}</strong><div class="meta">missing</div></div>'
    p = Path(path)
    src = p.resolve().as_uri() if p.exists() else ""
    image = f'<img src="{escape(src)}">' if src else ""
    return f'<div class="card"><strong>{escape(label)}</strong><br>{image}<div class="meta"><code>{escape(path)}</code></div></div>'


def _coerce_contract(value: WidgetElementContract | dict[str, Any]) -> WidgetElementContract:
    if isinstance(value, WidgetElementContract):
        return value
    return WidgetElementContract.from_dict(value)


def _score_id(score: VisualScorecard | dict[str, Any]) -> str:
    return score.contract_id if isinstance(score, VisualScorecard) else str(score.get("contract_id", ""))


def _score_dict(score: VisualScorecard | dict[str, Any]) -> dict[str, Any]:
    return score.to_dict() if isinstance(score, VisualScorecard) else dict(score)
