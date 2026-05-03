from __future__ import annotations

import os
from typing import Any

try:
    import fal_client  # type: ignore[import]
except ImportError:  # pragma: no cover - runtime dependency may be absent in unit tests
    fal_client = None  # type: ignore[assignment]

NANO_BANANA_ENDPOINT = "fal-ai/nano-banana"


def build_nano_banana_arguments(prompt: str, aspect_ratio: str) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "6",
        "limit_generations": True,
    }


def generate_desktop_concept(prompt: str, aspect_ratio: str, fal_key: str, log) -> str:
    if fal_client is None:
        log.warning("fal_client not installed — image generation unavailable")
        return ""
    os.environ.setdefault("FAL_KEY", fal_key)
    try:
        result = fal_client.subscribe(
            NANO_BANANA_ENDPOINT,
            arguments=build_nano_banana_arguments(prompt, aspect_ratio),
            with_logs=False,
        )
        url = result["images"][0]["url"]
        log.info("FAL image generated: %s", url[:80])
        return url
    except Exception as e:
        log.warning("FAL image generation failed: %s", e)
        return ""
