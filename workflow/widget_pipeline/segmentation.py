"""Image crop helpers for deterministic widget segmentation fixtures."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .safe_paths import safe_artifact_path


def crop_regions(image_path: str | Path, regions: Iterable[dict[str, Any]], crops_dir: str | Path) -> list[dict[str, Any]]:
    """Crop region bboxes from an image and return enriched region dictionaries.

    Each input region must contain an ``id`` and ``bbox`` in ``(x, y, w, h)``
    form. Crop files are written as ``<id>.png`` inside ``crops_dir``. Returned
    region dicts preserve the input metadata and add ``crop_path`` plus
    ``dimensions``.
    """

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError("Pillow is required to crop widget regions") from exc

    image_path = Path(image_path)
    crops_dir = Path(crops_dir)
    crops_dir.mkdir(parents=True, exist_ok=True)

    enriched: list[dict[str, Any]] = []
    with Image.open(image_path) as image:
        image_width, image_height = image.size
        for region in regions:
            region_id = str(region.get("id", "")).strip()
            if not region_id:
                raise ValueError("region id is required")
            x, y, w, h = _bbox(region.get("bbox"), region_id)
            _validate_bbox(region_id, x, y, w, h, image_width, image_height)

            crop_path = safe_artifact_path(crops_dir, region_id, ".png")
            crop = image.crop((x, y, x + w, y + h))
            crop.save(crop_path)

            item = dict(region)
            item["bbox"] = (x, y, w, h)
            item["crop_path"] = str(crop_path)
            item["dimensions"] = (w, h)
            enriched.append(item)

    return enriched


def _bbox(value: Any, region_id: str) -> tuple[int, int, int, int]:
    try:
        items = tuple(int(item) for item in value)
    except TypeError as exc:
        raise ValueError(f"region {region_id!r} bbox must be an iterable of four integers") from exc
    if len(items) != 4:
        raise ValueError(f"region {region_id!r} bbox must contain four integers")
    return items  # type: ignore[return-value]


def _validate_bbox(region_id: str, x: int, y: int, w: int, h: int, image_width: int, image_height: int) -> None:
    if w <= 0 or h <= 0:
        raise ValueError(f"region {region_id!r} bbox width and height must be positive")
    if x < 0 or y < 0:
        raise ValueError(f"region {region_id!r} bbox origin must be non-negative")
    if x + w > image_width or y + h > image_height:
        raise ValueError(
            f"region {region_id!r} bbox {(x, y, w, h)!r} exceeds image bounds {(image_width, image_height)!r}"
        )
