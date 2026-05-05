"""Deterministic and image-aware sample fixture regions for the widget dry-run harness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

_BASE_WIDTH = 1376
_BASE_HEIGHT = 768

_BASE_REGIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "full_hud",
        "role": "bottom_hud_container",
        "bbox": (0, 610, 1376, 158),
        "priority": 10,
        "anchor": "bottom",
        "visual_traits": (
            "fantasy-game bottom strip",
            "ornate dark translucent panel",
            "gold trim",
            "contains grouped HUD widgets",
        ),
        "expected_text": (),
        "actions": (),
        "hard_requirements": (
            "span the lower edge of the composition",
            "preserve fantasy HUD chrome and spacing",
            "remain a container rather than an interactive control",
        ),
        "non_goals": (
            "do not recreate wallpaper or character art",
            "do not launch a desktop shell in dry-run mode",
        ),
    },
    {
        "id": "workspace_group",
        "role": "workspace_switcher",
        "bbox": (160, 626, 330, 92),
        "priority": 80,
        "anchor": "bottom-left",
        "visual_traits": (
            "clustered fantasy tabs",
            "small numbered slots",
            "beveled dark buttons",
            "warm highlight accents",
        ),
        "expected_text": ("1", "2", "3", "4", "5"),
        "actions": (
            {
                "id": "workspace-1",
                "label": "Workspace 1",
                "command": "qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 1",
                "decorative": False,
                "visual_states": ("default", "hover", "pressed"),
                "preconditions": ("VirtualDesktopManager count >= 1",),
                "expected_effect": "active KDE virtual desktop becomes 1",
            },
            {
                "id": "workspace-2",
                "label": "Workspace 2",
                "command": "qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 2",
                "decorative": False,
                "visual_states": ("default", "hover", "pressed"),
                "preconditions": ("VirtualDesktopManager count >= 2",),
                "expected_effect": "active KDE virtual desktop becomes 2",
            },
            {
                "id": "workspace-3",
                "label": "Workspace 3",
                "command": "qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 3",
                "decorative": False,
                "visual_states": ("default", "hover", "pressed"),
                "preconditions": ("VirtualDesktopManager count >= 3",),
                "expected_effect": "active KDE virtual desktop becomes 3",
            },
            {
                "id": "workspace-4",
                "label": "Workspace 4",
                "command": "qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 4",
                "decorative": False,
                "visual_states": ("default", "hover", "pressed"),
                "preconditions": ("VirtualDesktopManager count >= 4",),
                "expected_effect": "active KDE virtual desktop becomes 4",
            },
            {
                "id": "workspace-5",
                "label": "Workspace 5",
                "command": "qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 5",
                "decorative": False,
                "visual_states": ("default", "hover", "pressed"),
                "preconditions": ("VirtualDesktopManager count >= 5",),
                "expected_effect": "active KDE virtual desktop becomes 5",
            },
        ),
        "hard_requirements": (
            "represent multiple workspaces as distinct slots",
            "show an active workspace state",
            "keep hit targets grouped on the lower-left side",
        ),
        "non_goals": (
            "do not implement live workspace switching in this dry-run fixture",
            "do not include unrelated status meters",
        ),
    },
    {
        "id": "clock",
        "role": "clock_display",
        "bbox": (570, 622, 250, 96),
        "priority": 90,
        "anchor": "bottom-center",
        "visual_traits": (
            "central ornate plaque",
            "large readable time text",
            "symmetrical frame",
            "glowing gold separators",
        ),
        "expected_text": ("12:00",),
        "data_source": "system_time",
        "update_interval_ms": 1000,
        "format": "HH:mm",
        "actions": (),
        "hard_requirements": (
            "reserve central bottom-strip placement",
            "keep time text legible at small sizes",
            "preserve decorative frame around text",
        ),
        "non_goals": (
            "do not implement calendar popovers in the sample contract",
            "do not infer real timezone behavior from the image",
        ),
    },
    {
        "id": "status_bars",
        "role": "system_status_bars",
        "bbox": (850, 628, 340, 86),
        "priority": 70,
        "anchor": "bottom-right",
        "visual_traits": (
            "stacked horizontal meters",
            "gem-like caps",
            "mana and health bar styling",
            "right-center HUD cluster",
        ),
        "expected_text": (),
        "actions": (),
        "hard_requirements": (
            "show at least two horizontal meter tracks",
            "keep meter cluster between clock and power button",
            "use decorative fantasy bar caps",
        ),
        "non_goals": (
            "do not bind to live CPU, RAM, battery, or network metrics yet",
            "do not animate meter values in the dry-run fixture",
        ),
    },
    {
        "id": "power_button",
        "role": "power_button",
        "bbox": (1224, 622, 112, 104),
        "priority": 60,
        "anchor": "bottom-right-edge",
        "visual_traits": (
            "far-right circular control",
            "ornate red-gold button",
            "decorative shutdown glyph area",
            "prominent edge placement",
        ),
        "expected_text": (),
        "actions": (
            {
                "id": "power-menu",
                "label": "Power menu",
                "command": "internal:power-menu",
                "decorative": False,
                "visual_states": ("default", "hover", "pressed"),
                "preconditions": ("power glyph toggles an in-artifact confirmation menu",),
                "expected_effect": "custom power menu popup opens without KRunner search",
            },
        ),
        "hard_requirements": (
            "remain visually distinct from status bars",
            "stay on the far-right edge of the bottom HUD",
            "be treated as decorative unless a command is supplied explicitly",
        ),
        "non_goals": (
            "do not run logout, shutdown, reboot, or lock commands from the sample harness",
            "do not write live desktop configuration",
        ),
    },
)


def sample_regions_for_image(width: int, height: int) -> list[dict[str, Any]]:
    """Return deterministic fixture regions scaled to an image size.

    The source fixture is authored for a 1376x768 fantasy HUD screenshot. Bboxes
    are scaled and clamped so every returned crop remains positive and inside the
    requested image dimensions, even for tiny test images.
    """

    width = int(width)
    height = int(height)
    if width <= 0 or height <= 0:
        raise ValueError("image width and height must be positive")

    regions = [_scaled_region(region, width, height) for region in _BASE_REGIONS]
    for region in regions:
        region["segmentation_method"] = "fixed_fixture_fallback"
    return regions


def preview_regions_for_image(image_path: str | Path) -> list[dict[str, Any]]:
    """Return widget fixture regions aligned to visible preview UI when possible.

    The first milestone harness still uses fixed semantic widget slots, but the
    slots must be anchored to the actual preview UI cluster rather than assuming
    every source image has a bottom HUD at the original fixture coordinates. This
    prevents the preview-texture renderer from proving only that gray background
    crops can be copied through Quickshell.
    """

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - already checked by caller
        raise RuntimeError("Pillow is required to segment preview widget regions") from exc

    image_path = Path(image_path)
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        detected = _detect_foreground_bbox(rgb)

    if detected is None:
        return sample_regions_for_image(width, height)

    regions = [_region_in_detected_bbox(region, detected) for region in _BASE_REGIONS]
    for region in regions:
        region["segmentation_method"] = "detected_preview_ui_cluster"
    return regions


def _scaled_region(region: dict[str, Any], width: int, height: int) -> dict[str, Any]:
    x, y, w, h = region["bbox"]
    x1 = round(x * width / _BASE_WIDTH)
    y1 = round(y * height / _BASE_HEIGHT)
    x2 = round((x + w) * width / _BASE_WIDTH)
    y2 = round((y + h) * height / _BASE_HEIGHT)

    sx1, sy1, sx2, sy2 = _clamp_positive_box(x1, y1, x2, y2, width, height)
    scaled = dict(region)
    scaled["bbox"] = (sx1, sy1, sx2 - sx1, sy2 - sy1)
    return scaled


def _region_in_detected_bbox(region: dict[str, Any], detected: tuple[int, int, int, int]) -> dict[str, Any]:
    detected_x, detected_y, detected_w, detected_h = detected
    base_x, base_y, base_w, base_h = _BASE_REGIONS[0]["bbox"]
    x, y, w, h = region["bbox"]
    rel_x = (x - base_x) / base_w
    rel_y = (y - base_y) / base_h
    rel_w = w / base_w
    rel_h = h / base_h
    mapped = dict(region)
    mapped["bbox"] = (
        int(round(detected_x + rel_x * detected_w)),
        int(round(detected_y + rel_y * detected_h)),
        max(1, int(round(rel_w * detected_w))),
        max(1, int(round(rel_h * detected_h))),
    )
    return mapped


def _detect_foreground_bbox(image: Any) -> tuple[int, int, int, int] | None:
    width, height = image.size
    pixels = image.load()
    bg = _border_median_color(image)
    threshold = 28
    xs: list[int] = []
    ys: list[int] = []
    stride = 1 if width * height <= 1_500_000 else max(1, round((width * height / 1_500_000) ** 0.5))
    for y in range(0, height, stride):
        for x in range(0, width, stride):
            r, g, b = pixels[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > threshold:
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return None
    x1 = max(0, min(xs) - 12)
    y1 = max(0, min(ys) - 12)
    x2 = min(width, max(xs) + stride + 12)
    y2 = min(height, max(ys) + stride + 12)
    detected_w = x2 - x1
    detected_h = y2 - y1
    if detected_w * detected_h < max(64, int(width * height * 0.01)):
        return None
    if detected_w < 32 or detected_h < 24:
        return None
    return (x1, y1, detected_w, detected_h)


def _border_median_color(image: Any) -> tuple[int, int, int]:
    width, height = image.size
    pixels = image.load()
    border = max(1, min(width, height, 24))
    samples: list[tuple[int, int, int]] = []
    step = max(1, min(width, height) // 256)
    for x in range(0, width, step):
        for y in range(border):
            samples.append(pixels[x, y])
            samples.append(pixels[x, height - 1 - y])
    for y in range(0, height, step):
        for x in range(border):
            samples.append(pixels[x, y])
            samples.append(pixels[width - 1 - x, y])
    if not samples:
        return (0, 0, 0)
    channels = list(zip(*samples, strict=True))
    return tuple(sorted(channel)[len(channel) // 2] for channel in channels)  # type: ignore[return-value]


def _clamp_positive_box(x1: int, y1: int, x2: int, y2: int, width: int, height: int) -> tuple[int, int, int, int]:
    x1 = max(0, min(int(x1), width - 1))
    y1 = max(0, min(int(y1), height - 1))
    x2 = max(0, min(int(x2), width))
    y2 = max(0, min(int(y2), height))

    if x2 <= x1:
        x2 = min(width, x1 + 1)
        if x2 <= x1:
            x1 = max(0, width - 1)
            x2 = width
    if y2 <= y1:
        y2 = min(height, y1 + 1)
        if y2 <= y1:
            y1 = max(0, height - 1)
            y2 = height
    return x1, y1, x2, y2
