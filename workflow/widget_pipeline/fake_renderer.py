"""Deterministic fake widget rendering for the Milestone 1 dry-run harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .models import StageResult, StageStatus, WidgetElementContract
from .safe_paths import safe_artifact_path


def render_fake_widgets(
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    rendered_dir: str | Path,
    asset_bundle: Any | None = None,
) -> tuple[list[dict[str, str]], StageResult]:
    """Render deterministic placeholder crops for widget contracts.

    The renderer is intentionally fake: it validates that the pipeline can write
    per-contract output images without launching a shell or touching live desktop
    configuration. ``asset_bundle`` is accepted for API compatibility with later
    real renderers but is not required for this MVP.
    """

    del asset_bundle
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("Pillow is required to render fake widget crops") from exc

    rendered_dir = Path(rendered_dir)
    rendered_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[dict[str, str]] = []
    artifacts: list[str] = []
    font = ImageFont.load_default()

    for contract in (_coerce_contract(item) for item in contracts):
        width, height = _contract_dimensions(contract)
        path = safe_artifact_path(rendered_dir, contract.id, ".png")

        image = Image.new("RGBA", (width, height), (19, 14, 16, 255))
        draw = ImageDraw.Draw(image)
        _draw_dark_fantasy_widget(draw, contract, width, height, font)
        image.save(path)

        rendered.append({"contract_id": contract.id, "rendered_path": str(path)})
        artifacts.append(str(path))

    status = StageStatus.PASS if len(artifacts) == len(rendered) else StageStatus.FAIL
    reason = f"rendered {len(rendered)} deterministic fake widget crops"
    return rendered, StageResult("rendering", status, reason, artifacts=tuple(artifacts))


def _coerce_contract(value: WidgetElementContract | dict[str, Any]) -> WidgetElementContract:
    if isinstance(value, WidgetElementContract):
        return value
    return WidgetElementContract.from_dict(value)


def _contract_dimensions(contract: WidgetElementContract) -> tuple[int, int]:
    width, height = contract.dimensions
    if width <= 0 or height <= 0:
        width, height = contract.bbox[2], contract.bbox[3]
    return max(1, int(width)), max(1, int(height))


def _draw_dark_fantasy_widget(draw: Any, contract: WidgetElementContract, width: int, height: int, font: Any) -> None:
    gold = (196, 145, 55, 255)
    bronze = (94, 61, 34, 255)
    ember = (132, 45, 34, 255)
    muted = (52, 37, 36, 255)
    text = (231, 196, 116, 255)

    draw.rectangle((0, 0, width - 1, height - 1), fill=(19, 14, 16, 255), outline=gold)
    if width > 4 and height > 4:
        draw.rectangle((2, 2, width - 3, height - 3), outline=bronze)
    if width > 10 and height > 10:
        draw.rounded_rectangle((5, 5, width - 6, height - 6), radius=max(2, min(width, height) // 10), fill=muted, outline=gold)

    role = contract.role.lower()
    if "workspace" in role:
        _draw_workspace_slots(draw, contract, width, height, font, gold, text)
    elif "clock" in role:
        label = contract.expected_text[0] if contract.expected_text else "12:00"
        _draw_centered_text(draw, label, width, height, font, text)
    elif "status" in role or "bar" in role:
        _draw_status_bars(draw, width, height, gold, ember)
    elif "power" in role:
        _draw_power_button(draw, width, height, gold, ember)
    else:
        label = contract.expected_text[0] if contract.expected_text else contract.id.replace("_", " ")
        _draw_centered_text(draw, label[:24], width, height, font, text)


def _draw_workspace_slots(draw: Any, contract: WidgetElementContract, width: int, height: int, font: Any, gold: tuple[int, ...], text: tuple[int, ...]) -> None:
    labels = contract.expected_text or ("1", "2", "3", "4", "5")
    slot_count = max(1, len(labels))
    margin = max(2, min(width, height) // 10)
    gap = max(1, width // 80)
    slot_w = max(1, (width - 2 * margin - gap * (slot_count - 1)) // slot_count)
    slot_h = max(1, height - 2 * margin)
    for index, label in enumerate(labels):
        x1 = margin + index * (slot_w + gap)
        x2 = min(width - margin, x1 + slot_w)
        fill = (74, 43, 34, 255) if index == 0 else (35, 25, 27, 255)
        draw.rounded_rectangle((x1, margin, max(x1, x2 - 1), margin + slot_h), radius=max(1, slot_h // 5), fill=fill, outline=gold)
        draw.text((x1 + max(1, slot_w // 3), margin + max(1, slot_h // 4)), str(label), fill=text, font=font)


def _draw_status_bars(draw: Any, width: int, height: int, gold: tuple[int, ...], ember: tuple[int, ...]) -> None:
    margin = max(1, min(width, height) // 8)
    if width <= 2 or height <= 2:
        draw.point((0, 0), fill=gold)
        return
    bar_h = max(1, (height - 3 * margin) // 2)
    x1 = min(margin, width - 2)
    x2 = max(x1 + 1, width - margin - 1)
    for index, fill in enumerate(((103, 28, 32, 255), (37, 79, 94, 255))):
        y1 = min(max(0, margin + index * (bar_h + margin)), height - 2)
        y2 = max(y1 + 1, min(height - 1, y1 + bar_h))
        draw.rounded_rectangle((x1, y1, x2, y2), radius=max(1, bar_h // 2), fill=(27, 20, 22, 255), outline=gold)
        fill_x2 = max(x1 + 1, min(x2, int(width * (0.72 - index * 0.18))))
        draw.rounded_rectangle((x1 + 1, y1 + 1, fill_x2, max(y1 + 1, y2 - 1)), radius=max(1, bar_h // 3), fill=fill)
        draw.ellipse((max(0, x1 - 1), max(0, y1 - 1), min(width - 1, x1 + bar_h), min(height - 1, y2 + 1)), fill=ember, outline=gold)


def _draw_power_button(draw: Any, width: int, height: int, gold: tuple[int, ...], ember: tuple[int, ...]) -> None:
    cx, cy = width // 2, height // 2
    radius = max(1, min(width, height) // 3)
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=ember, outline=gold, width=1)
    inner = max(1, radius // 2)
    draw.arc((cx - inner, cy - inner, cx + inner, cy + inner), 35, 325, fill=(250, 211, 122, 255), width=max(1, radius // 8))
    draw.line((cx, cy - inner, cx, cy), fill=(250, 211, 122, 255), width=max(1, radius // 8))


def _draw_centered_text(draw: Any, label: str, width: int, height: int, font: Any, fill: tuple[int, ...]) -> None:
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text((max(1, (width - text_w) // 2), max(1, (height - text_h) // 2)), label, fill=fill, font=font)
