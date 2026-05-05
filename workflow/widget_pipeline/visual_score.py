"""Visual loss scoring for rendered widget dry-run crops."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import StageResult, StageStatus, VisualScorecard, WidgetElementContract
from .safe_paths import safe_artifact_path


def score_rendered_widgets(
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    rendered_results: Iterable[Mapping[str, Any]],
    comparisons_dir: str | Path,
) -> tuple[list[VisualScorecard], StageResult]:
    """Compare target crops with rendered crops using a simple Pillow MAD score.

    This fake MVP intentionally reports PASS when comparisons were produced; low
    scores are process feedback, not a hard failure gate.
    """

    try:
        from PIL import Image, ImageChops, ImageStat
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("Pillow is required to score rendered widget crops") from exc

    comparisons_dir = Path(comparisons_dir)
    comparisons_dir.mkdir(parents=True, exist_ok=True)
    rendered_by_id = {str(item.get("contract_id", "")): str(item.get("rendered_path", "")) for item in rendered_results}

    scorecards: list[VisualScorecard] = []
    artifacts: list[str] = []
    for contract in (_coerce_contract(item) for item in contracts):
        rendered_path = rendered_by_id.get(contract.id)
        if not rendered_path:
            continue

        target_path = Path(contract.crop_path)
        comparison_path = safe_artifact_path(comparisons_dir, contract.id, ".png")
        try:
            with Image.open(target_path) as target_image, Image.open(rendered_path) as rendered_image:
                target = target_image.convert("L")
                rendered = rendered_image.convert("L")
                if rendered.size != target.size:
                    rendered = rendered.resize(target.size)

                diff = ImageChops.difference(target, rendered)
                mean_abs = float(ImageStat.Stat(diff).mean[0]) if target.size[0] and target.size[1] else 255.0
                loss = max(0.0, min(1.0, mean_abs / 255.0))
                total = max(0.0, 10.0 * (1.0 - loss))

                _write_comparison_image(target_image.convert("RGBA"), rendered_image.convert("RGBA"), comparison_path)
        except OSError as exc:
            return scorecards, StageResult(
                "visual-score",
                StageStatus.FAIL,
                f"failed to compare {contract.id}: {exc}",
                artifacts=tuple(artifacts),
            )

        artifacts.append(str(comparison_path))
        scorecards.append(
            VisualScorecard(
                contract_id=contract.id,
                total=round(total, 4),
                loss=round(loss, 4),
                passed=total >= 5.0,
                subscores={"grayscale_mad": round(1.0 - loss, 4)},
                comparison_path=str(comparison_path),
                feedback="fake renderer MVP visual process score",
            )
        )

    status = StageStatus.PASS if scorecards else StageStatus.SKIP
    reason = f"scored {len(scorecards)} rendered widget comparisons" if scorecards else "no rendered widget comparisons available"
    return scorecards, StageResult("visual-score", status, reason, artifacts=tuple(artifacts))


def _coerce_contract(value: WidgetElementContract | dict[str, Any]) -> WidgetElementContract:
    if isinstance(value, WidgetElementContract):
        return value
    return WidgetElementContract.from_dict(value)


def _write_comparison_image(target: Any, rendered: Any, comparison_path: Path) -> None:
    from PIL import Image

    if rendered.size != target.size:
        rendered = rendered.resize(target.size)
    width, height = target.size
    spacer = 2 if width > 1 else 1
    comparison = Image.new("RGBA", (width * 2 + spacer, height), (8, 8, 8, 255))
    comparison.paste(target, (0, 0))
    comparison.paste(rendered, (width + spacer, 0))
    comparison.save(comparison_path)
