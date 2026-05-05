"""Deterministic texture asset generation for ornate Quickshell chrome.

This module is intentionally local/offline: it creates tileable 9-slice PNG
assets before LLM codegen so ornate menu prompts reference real files instead of
asking the model to fake craft with flat Rectangle borders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

Image: Any = None
ImageDraw: Any = None
ImageFilter: Any = None


ORNATE_TERMS = (
    "ornate", "thorn", "thorns", "diablo", "rpg menu", "inventory frame",
    "carved border", "carved", "filigree", "9-slice", "tiled border",
    "borderimage", "relic", "blackiron", "bonfire", "dark souls", "campfire",
)


@dataclass(frozen=True)
class TextureIntent:
    """Visual intent for a generated 9-slice texture bundle."""

    theme_slug: str
    palette: dict[str, str] = field(default_factory=dict)
    motif: str = "blackened iron, thorn filigree, ember cracks"
    variants: tuple[str, ...] = ("panel", "button", "slot")
    size_px: int = 192
    slice_px: int = 48
    seed: int = 0


@dataclass(frozen=True)
class TextureAsset:
    """One generated image asset plus validation metrics."""

    variant: str
    path: str
    slice_px: int
    width: int
    height: int
    seam_score: float
    sha256: str


@dataclass(frozen=True)
class TextureBundle:
    """Prompt/copy metadata for a generated texture bundle."""

    root: str
    theme_slug: str
    assets: tuple[TextureAsset, ...]
    metadata_path: str

    def as_prompt_context(self) -> str:
        return json.dumps(
            {
                "root": self.root,
                "theme_slug": self.theme_slug,
                "metadata_path": self.metadata_path,
                "assets": [asdict(asset) for asset in self.assets],
                "qml_contract": (
                    "Use these source paths exactly in BorderImage.source. "
                    "Set border.left/right/top/bottom to slice_px and use BorderImage.Repeat "
                    "for tiled edge segments. Do not invent asset paths."
                ),
            },
            indent=2,
            sort_keys=True,
        )


def needs_texture_assets(element: str, design: dict) -> bool:
    """Return True when this element/design needs generated ornate assets."""

    if "quickshell" not in str(element).lower():
        return False
    return any(term in json.dumps(design or {}, sort_keys=True).lower() for term in ORNATE_TERMS)


def extract_texture_intent(design: dict) -> TextureIntent:
    """Build a deterministic texture intent from design.json-ish data."""

    name = str(design.get("name") or design.get("theme_name") or "generated-theme")
    slug = _slugify(name)
    palette = design.get("palette") if isinstance(design.get("palette"), dict) else {}
    if not palette:
        palette = {
            "background": "#111513",
            "soot": "#252623",
            "iron": "#6b4b2f",
            "bone": "#d6c8aa",
            "ember": "#d06f22",
            "amber": "#f0a33a",
        }
    blob = json.dumps(design or {}, sort_keys=True)
    seed = int(hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8], 16)
    return TextureIntent(theme_slug=slug, palette={k: str(v) for k, v in palette.items()}, seed=seed)


def generate_texture_bundle(intent: TextureIntent, output_root: Path) -> TextureBundle:
    """Generate deterministic PNG assets and metadata under ``output_root``."""

    _require_pillow()
    output_root = Path(output_root)
    asset_root = output_root / "assets" / intent.theme_slug
    asset_root.mkdir(parents=True, exist_ok=True)
    assets: list[TextureAsset] = []
    for variant in intent.variants:
        image = _draw_ornate_atlas(intent, variant)
        rel = Path("assets") / intent.theme_slug / f"{variant}_ornate_9slice.png"
        path = output_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        variant_slice = _variant_slice_px(intent, variant)
        assets.append(
            TextureAsset(
                variant=variant,
                path=str(rel).replace("\\", "/"),
                slice_px=variant_slice,
                width=image.width,
                height=image.height,
                seam_score=seam_distance(image),
                sha256=digest,
            )
        )
    metadata_rel = Path("assets") / intent.theme_slug / "texture_bundle.json"
    bundle = TextureBundle(
        root=str(output_root),
        theme_slug=intent.theme_slug,
        assets=tuple(assets),
        metadata_path=str(metadata_rel).replace("\\", "/"),
    )
    (output_root / metadata_rel).write_text(bundle.as_prompt_context() + "\n", encoding="utf-8")
    return bundle


def validate_texture_bundle(bundle: TextureBundle) -> list[str]:
    """Validate generated files, safe paths, and seam quality."""

    reasons: list[str] = []
    root = Path(bundle.root)
    if not bundle.assets:
        reasons.append("texture bundle contains no assets")
    for asset in bundle.assets:
        rel = Path(asset.path)
        if rel.is_absolute() or ".." in rel.parts:
            reasons.append(f"unsafe texture asset path: {asset.path!r}")
            continue
        path = root / rel
        if not path.exists():
            reasons.append(f"texture asset missing on disk: {asset.path}")
            continue
        if asset.width < 48 or asset.height < 48:
            reasons.append(f"texture asset too small for 9-slice: {asset.path}")
        if asset.slice_px <= 0 or asset.slice_px * 2 >= min(asset.width, asset.height):
            reasons.append(f"invalid 9-slice border for {asset.path}: {asset.slice_px}px")
        if asset.seam_score > 16.0:
            reasons.append(f"texture asset seam too visible ({asset.seam_score:.2f}): {asset.path}")
    if bundle.metadata_path:
        meta = root / bundle.metadata_path
        if not meta.exists():
            reasons.append(f"texture metadata missing on disk: {bundle.metadata_path}")
    return reasons


def seam_distance(image: Any) -> float:
    """Mean RGB distance between opposite edges; lower means more tileable."""

    rgba = image.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    distances: list[float] = []
    for y in range(h):
        distances.append(_rgb_distance(px[0, y], px[w - 1, y]))
    for x in range(w):
        distances.append(_rgb_distance(px[x, 0], px[x, h - 1]))
    return sum(distances) / max(1, len(distances))


def declared_asset_paths(texture_assets: dict | None) -> set[str]:
    """Return normalized source paths declared in bundle metadata."""

    if not isinstance(texture_assets, dict):
        return set()
    return {
        str(asset.get("path", "")).replace("\\", "/")
        for asset in texture_assets.get("assets", [])
        if isinstance(asset, dict) and asset.get("path")
    }


def referenced_borderimage_sources(qml: str) -> set[str]:
    """Extract local BorderImage source paths from QML content."""

    sources = set()
    for match in re.finditer(r"\bsource\s*:\s*([\"'])(.*?)\1", qml):
        src = match.group(2).strip().replace("\\", "/")
        if src and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", src):
            sources.add(src)
    return sources


def _draw_ornate_atlas(intent: TextureIntent, variant: str) -> Any:
    _require_pillow()
    output_size = intent.size_px
    render_scale = 3
    size = output_size * render_scale
    slice_px = _variant_slice_px(intent, variant) * render_scale
    palette = _resolved_palette(intent.palette)
    img = Image.new("RGBA", (size, size), palette["transparent"])
    draw = ImageDraw.Draw(img, "RGBA")

    # Sooty/parchment-black center, deliberately quiet so content remains usable.
    center = (slice_px, slice_px, size - slice_px, size - slice_px)
    draw.rounded_rectangle(center, radius=6 * render_scale, fill=palette["center"])
    _draw_tileable_mottle(draw, size, palette, intent.seed + len(variant))

    # Worn metal frame bands.
    band = slice_px - 4 * render_scale
    edge_fill = palette["iron_dark"]
    edge_hi = palette["iron_hi"]
    ember = palette["ember"]
    draw.rectangle((0, 0, size, band), fill=edge_fill)
    draw.rectangle((0, size - band, size, size), fill=edge_fill)
    draw.rectangle((0, 0, band, size), fill=edge_fill)
    draw.rectangle((size - band, 0, size, size), fill=edge_fill)

    # Repeating thorn strokes on all four sides; endpoints wrap for seamless tiling.
    spacing = (34 if variant == "panel" else 28 if variant == "button" else 24) * render_scale
    for i in range(-spacing, size + spacing, spacing):
        phase = ((i // spacing) & 1) * 5 * render_scale
        _wrapped_line(draw, size, (i, 11 * render_scale + phase), (i + spacing // 2, band - 12 * render_scale), edge_hi, 3 * render_scale)
        _wrapped_line(draw, size, (i, size - 12 * render_scale - phase), (i + spacing // 2, size - band + 12 * render_scale), edge_hi, 3 * render_scale)
        _wrapped_line(draw, size, (11 * render_scale + phase, i), (band - 12 * render_scale, i + spacing // 2), edge_hi, 3 * render_scale)
        _wrapped_line(draw, size, (size - 12 * render_scale - phase, i), (size - band + 12 * render_scale, i + spacing // 2), edge_hi, 3 * render_scale)
        if (i // spacing) % 3 == 0:
            _wrapped_line(draw, size, (i + 8 * render_scale, 6 * render_scale), (i + 18 * render_scale, 6 * render_scale), ember, 2 * render_scale)
            _wrapped_line(draw, size, (i + 8 * render_scale, size - 7 * render_scale), (i + 18 * render_scale, size - 7 * render_scale), ember, 2 * render_scale)

    # Corner caps: black iron riveted plates with amber scoring.
    cap = slice_px + 6 * render_scale
    for x0, y0 in ((0, 0), (size - cap, 0), (0, size - cap), (size - cap, size - cap)):
        draw.rounded_rectangle((x0 + 3 * render_scale, y0 + 3 * render_scale, x0 + cap - 3 * render_scale, y0 + cap - 3 * render_scale), radius=7 * render_scale, fill=palette["corner"])
        draw.rounded_rectangle((x0 + 7 * render_scale, y0 + 7 * render_scale, x0 + cap - 7 * render_scale, y0 + cap - 7 * render_scale), radius=5 * render_scale, outline=edge_hi, width=2 * render_scale)
        cx, cy = x0 + cap // 2, y0 + cap // 2
        draw.ellipse((cx - 3 * render_scale, cy - 3 * render_scale, cx + 3 * render_scale, cy + 3 * render_scale), fill=ember)

    # Inner soot/bone hairlines: thin, worn, not bulky.
    inner = slice_px - 3 * render_scale
    outer = size - slice_px + 3 * render_scale
    draw.rectangle((inner, inner, outer, outer), outline=palette["bone_dim"], width=render_scale)
    draw.rectangle((inner + 3 * render_scale, inner + 3 * render_scale, outer - 3 * render_scale, outer - 3 * render_scale), outline=palette["ember_dim"], width=render_scale)

    img = img.filter(ImageFilter.GaussianBlur(radius=0.25 * render_scale))
    img = img.filter(ImageFilter.UnsharpMask(radius=1.0 * render_scale, percent=45, threshold=4))
    img = img.resize((output_size, output_size), Image.Resampling.LANCZOS)
    _force_tileable_outer_edges(img)
    return img


def _variant_slice_px(intent: TextureIntent, variant: str) -> int:
    if variant == "button":
        return max(24, int(intent.slice_px * 0.65))
    if variant == "slot":
        return max(18, int(intent.slice_px * 0.50))
    return intent.slice_px


def _draw_tileable_mottle(draw: Any, size: int, palette: dict[str, tuple[int, int, int, int]], seed: int) -> None:
    colors = [palette["ash"], palette["soot"], palette["ember_dim"]]
    for idx in range(42):
        x = (seed * 17 + idx * 29) % size
        y = (seed * 31 + idx * 23) % size
        r = 1 + ((seed + idx) % 3)
        color = colors[idx % len(colors)]
        for dx in (-size, 0, size):
            for dy in (-size, 0, size):
                draw.ellipse((x + dx - r, y + dy - r, x + dx + r, y + dy + r), fill=color)


def _wrapped_line(draw: Any, size: int, a: tuple[int, int], b: tuple[int, int], color: tuple[int, int, int, int], width: int) -> None:
    for dx in (-size, 0, size):
        for dy in (-size, 0, size):
            draw.line((a[0] + dx, a[1] + dy, b[0] + dx, b[1] + dy), fill=color, width=width)


def _force_tileable_outer_edges(image: Any) -> None:
    px = image.load()
    w, h = image.size
    for y in range(h):
        avg = tuple((px[0, y][i] + px[w - 1, y][i]) // 2 for i in range(4))
        px[0, y] = avg
        px[w - 1, y] = avg
    for x in range(w):
        avg = tuple((px[x, 0][i] + px[x, h - 1][i]) // 2 for i in range(4))
        px[x, 0] = avg
        px[x, h - 1] = avg


def _resolved_palette(raw: dict[str, str]) -> dict[str, tuple[int, int, int, int]]:
    values = list(raw.values())
    bg = _hex(values, (17, 21, 19), 0)
    soot = _hex(values, (37, 38, 35), 1)
    iron = _hex(values, (107, 75, 47), 2)
    bone = _hex(values, (214, 200, 170), 3)
    amber = _hex(values, (240, 163, 58), 4)
    ember = _hex(values, (208, 111, 34), 5)
    return {
        "transparent": (0, 0, 0, 0),
        "center": (*_mix(bg, soot, 0.35), 218),
        "soot": (*soot, 38),
        "ash": (*_mix(soot, bone, 0.25), 44),
        "iron_dark": (*_mix(bg, iron, 0.58), 236),
        "iron_hi": (*_mix(iron, bone, 0.33), 210),
        "corner": (*_mix(bg, iron, 0.42), 252),
        "bone_dim": (*bone, 92),
        "ember": (*ember, 220),
        "ember_dim": (*_mix(ember, amber, 0.28), 58),
    }


def _hex(values: Iterable[str], fallback: tuple[int, int, int], index: int) -> tuple[int, int, int]:
    vals = [v for v in values if isinstance(v, str) and re.match(r"^#[0-9a-fA-F]{6}$", v)]
    if index < len(vals):
        v = vals[index].lstrip("#")
        return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    return fallback


def _mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))


def _rgb_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    return math.sqrt(sum((int(a[i]) - int(b[i])) ** 2 for i in range(4)))


def _require_pillow() -> None:
    """Load Pillow on demand for texture generation paths."""

    global Image, ImageDraw, ImageFilter
    if Image is not None and ImageDraw is not None and ImageFilter is not None:
        return
    try:
        from PIL import Image as PILImage
        from PIL import ImageDraw as PILImageDraw
        from PIL import ImageFilter as PILImageFilter
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required for texture asset generation; install Pillow to generate ornate texture assets."
        ) from exc
    Image = PILImage
    ImageDraw = PILImageDraw
    ImageFilter = PILImageFilter


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "generated-theme"
