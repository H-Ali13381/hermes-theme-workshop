from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "widget_pipeline_sample.py"
EXPECTED_DIRS = ("crops", "contracts", "assets", "rendered", "comparisons", "sandbox", "reports")
EXPECTED_SKIP_STAGES = {
    "runtime-launch": "dry-run",
    "desktop-promotion": "dry-run",
}


def run_sample(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_missing_image_exits_nonzero(tmp_path: Path) -> None:
    result = run_sample("--image", str(tmp_path / "missing.png"), "--out", str(tmp_path / "out"), "--dry-run")

    assert result.returncode != 0
    assert "image does not exist" in result.stderr
    assert not (tmp_path / "out" / "reports" / "report.json").exists()


def test_dry_run_flag_is_required(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "tiny.png"
    Image.new("RGBA", (2, 3), (255, 0, 0, 255)).save(image_path)

    result = run_sample("--image", str(image_path), "--out", str(tmp_path / "out"))

    assert result.returncode != 0
    assert "dry-run only" in result.stderr


def test_valid_tiny_image_creates_dirs_and_reports_with_skips(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "tiny.png"
    out_dir = tmp_path / "sample-out"
    image = Image.new("RGBA", (2, 3), (255, 0, 0, 255))
    image.save(image_path)

    result = run_sample(
        "--image",
        str(image_path),
        "--out",
        str(out_dir),
        "--framework",
        "quickshell",
        "--dry-run",
        "--strict",
    )

    assert result.returncode == 0, result.stderr
    for name in EXPECTED_DIRS:
        assert (out_dir / name).is_dir()

    report_json = out_dir / "reports" / "report.json"
    report_md = out_dir / "reports" / "report.md"
    assert report_json.is_file()
    assert report_md.is_file()

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["framework"] == "quickshell"
    assert report["dry_run"] is True
    assert report["strict"] is True
    assert report["image_path"] == str(image_path)
    assert report["output_dir"] == str(out_dir)
    output_root = out_dir.resolve()
    for stage in report["stages"]:
        for artifact in stage.get("artifacts", []):
            if str(artifact).startswith("sha256:"):
                continue
            artifact_path = Path(artifact).resolve()
            if artifact_path != image_path.resolve():
                assert artifact_path.is_relative_to(output_root)
    assert report["image_dimensions"] == [2, 3]
    assert len(report["contracts"]) == 5
    assert {contract["id"] for contract in report["contracts"]} == {
        "full_hud",
        "workspace_group",
        "clock",
        "status_bars",
        "power_button",
    }
    assert len(report["visual_scores"]) == 5
    assert {score["contract_id"] for score in report["visual_scores"]} == {
        "full_hud",
        "workspace_group",
        "clock",
        "status_bars",
        "power_button",
    }

    crop_paths = {path.name for path in (out_dir / "crops").glob("*.png")}
    assert crop_paths == {
        "full_hud.png",
        "workspace_group.png",
        "clock.png",
        "status_bars.png",
        "power_button.png",
    }
    contract_paths = {path.name for path in (out_dir / "contracts").glob("*.json")}
    assert contract_paths == {
        "full_hud.json",
        "workspace_group.json",
        "clock.json",
        "status_bars.json",
        "power_button.json",
        "contracts.json",
    }
    aggregate_contracts = json.loads((out_dir / "contracts" / "contracts.json").read_text(encoding="utf-8"))
    assert len(aggregate_contracts) == 5
    rendered_paths = {path.name for path in (out_dir / "rendered").glob("*.png")}
    assert rendered_paths == {
        "full_hud.png",
        "workspace_group.png",
        "clock.png",
        "status_bars.png",
        "power_button.png",
    }
    comparison_paths = {path.name for path in (out_dir / "comparisons").glob("*.png")}
    assert comparison_paths == rendered_paths

    stages = {stage["name"]: stage for stage in report["stages"]}
    assert stages["preview-source"]["status"] == "PASS"
    assert stages["preview-source"]["reason"] == "source image loaded"
    assert stages["segmentation"]["status"] == "PASS"
    assert len(stages["segmentation"]["artifacts"]) == 5
    assert stages["contracts"]["status"] == "PASS"
    assert len(stages["contracts"]["artifacts"]) == 6
    assert stages["assets"]["status"] == "PASS"
    assert "generated 3 deterministic ornate texture assets" in stages["assets"]["reason"]
    assert len(stages["assets"]["artifacts"]) == 5
    assert (out_dir / "assets" / "sample-widget-hud" / "texture_bundle.json").is_file()
    assert (out_dir / "assets" / "sample-widget-hud" / "asset_contact_sheet.png").is_file()
    assert stages["rendering"]["status"] == "PASS"
    assert len(stages["rendering"]["artifacts"]) == 5
    assert stages["visual-score"]["status"] == "PASS"
    assert len(stages["visual-score"]["artifacts"]) == 5
    assert stages["function-validation"]["status"] == "PASS"
    assert "validated actions/data bindings" in stages["function-validation"]["reason"]
    for name, reason in EXPECTED_SKIP_STAGES.items():
        assert stages[name]["status"] == "SKIP"
        assert stages[name]["reason"] == reason

    md = report_md.read_text(encoding="utf-8")
    assert "# Widget Pipeline Sample Report" in md
    assert "| segmentation | PASS | cropped 5 deterministic fixture regions (no preview UI cluster detected) |" in md
    assert "| contracts | PASS | normalized 5 widget contracts |" in md
    assert "| assets | PASS | generated 3 deterministic ornate texture assets |" in md
    assert "| rendering | PASS | rendered 5 deterministic fake widget crops |" in md
    assert "| visual-score | PASS | scored 5 rendered widget comparisons |" in md
    assert "## Visual Scores" in md
    assert "| workspace_group |" in md
    assert "| runtime-launch | SKIP | dry-run |" in md


def test_preview_texture_segments_detected_hud_instead_of_empty_bottom_band(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image_path = tmp_path / "centered-hud.png"
    out_dir = tmp_path / "sample-out"
    image = Image.new("RGBA", (1376, 768), (177, 177, 177, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((78, 276, 1298, 454), radius=18, fill=(42, 27, 18, 255), outline=(210, 153, 58, 255), width=8)
    for index, x in enumerate((180, 280, 380)):
        draw.ellipse((x, 328, x + 72, 400), fill=((55 + index * 40), 80, 170, 255), outline=(238, 198, 96, 255), width=5)
    draw.rounded_rectangle((560, 300, 820, 430), radius=26, fill=(80, 48, 28, 255), outline=(244, 200, 92, 255), width=7)
    draw.text((650, 350), "10:00", fill=(255, 232, 145, 255))
    draw.rounded_rectangle((880, 318, 1160, 350), radius=10, fill=(160, 32, 28, 255), outline=(237, 186, 80, 255), width=4)
    draw.rounded_rectangle((880, 372, 1160, 404), radius=10, fill=(33, 72, 180, 255), outline=(237, 186, 80, 255), width=4)
    draw.ellipse((1210, 312, 1290, 392), fill=(170, 25, 25, 255), outline=(255, 220, 120, 255), width=5)
    image.save(image_path)

    result = run_sample(
        "--image",
        str(image_path),
        "--out",
        str(out_dir),
        "--renderer",
        "quickshell",
        "--preview-texture",
        "--no-launch",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    report = json.loads((out_dir / "reports" / "report.json").read_text(encoding="utf-8"))
    stages = {stage["name"]: stage for stage in report["stages"]}
    assert "detected preview UI cluster" in stages["segmentation"]["reason"]
    full_hud = next(contract for contract in report["contracts"] if contract["id"] == "full_hud")
    assert full_hud["bbox"][1] < 500
    with Image.open(out_dir / "crops" / "full_hud.png") as crop:
        colors = crop.convert("RGB").getcolors(maxcolors=1_000_000)
    assert colors is not None
    dominant_count, dominant_color = max(colors, key=lambda item: item[0])
    assert dominant_color != (177, 177, 177)
    assert dominant_count / sum(count for count, _ in colors) < 0.85


def test_quickshell_renderer_no_launch_writes_sandbox_manifest(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "tiny.png"
    out_dir = tmp_path / "sample-out"
    Image.new("RGBA", (64, 48), (18, 12, 14, 255)).save(image_path)

    result = run_sample(
        "--image",
        str(image_path),
        "--out",
        str(out_dir),
        "--renderer",
        "quickshell",
        "--no-launch",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    qml_path = out_dir / "sandbox" / "quickshell" / "shell.qml"
    manifest_path = out_dir / "sandbox" / "quickshell" / "manifest.json"
    assert qml_path.is_file()
    assert manifest_path.is_file()
    qml = qml_path.read_text(encoding="utf-8")
    assert "PanelWindow" in qml
    assert "FloatingWindow" not in qml
    assert "hyprctl" not in qml
    assert "~/.config/quickshell" not in qml
    report = json.loads((out_dir / "reports" / "report.json").read_text(encoding="utf-8"))
    stages = {stage["name"]: stage for stage in report["stages"]}
    assert report["renderer"] == "quickshell"
    assert report["no_launch"] is True
    assert stages["quickshell-sandbox"]["status"] == "PASS"
    assert stages["runtime-launch"]["status"] == "SKIP"
    assert stages["runtime-launch"]["reason"] == "no-launch requested; generated sandbox only"
    assert stages["screenshot-capture"]["status"] == "SKIP"
    assert stages["visual-score"]["status"] == "SKIP"
    for stage in report["stages"]:
        for artifact in stage.get("artifacts", []):
            if str(artifact).startswith("sha256:"):
                continue
            artifact_path = Path(artifact).resolve()
            if artifact_path != image_path.resolve():
                assert artifact_path.is_relative_to(out_dir.resolve())


def test_quickshell_preview_texture_flag_writes_upper_bound_manifest(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "tiny.png"
    out_dir = tmp_path / "sample-out"
    Image.new("RGBA", (64, 48), (18, 12, 14, 255)).save(image_path)

    result = run_sample(
        "--image",
        str(image_path),
        "--out",
        str(out_dir),
        "--renderer",
        "quickshell",
        "--preview-texture",
        "--no-launch",
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    manifest = json.loads((out_dir / "sandbox" / "quickshell" / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((out_dir / "reports" / "report.json").read_text(encoding="utf-8"))
    assert manifest["render_mode"] == "preview_texture"
    assert report["preview_texture"] is True
    assert (out_dir / "sandbox" / "quickshell" / "assets" / "clock.preview.png").is_file()
    stages = {stage["name"]: stage for stage in report["stages"]}
    assert stages["artifact-function-validation"]["status"] == "PASS"
    assert "same generated artifact" in stages["artifact-function-validation"]["reason"]
    assert str(out_dir / "sandbox" / "quickshell" / "shell.qml") in stages["artifact-function-validation"]["artifacts"]
    assert any(artifact.startswith("sha256:") for artifact in stages["artifact-function-validation"]["artifacts"])


def test_output_root_symlink_is_rejected(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "tiny.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(image_path)
    real_out = tmp_path / "real-out"
    real_out.mkdir()
    symlink_out = tmp_path / "symlink-out"
    symlink_out.symlink_to(real_out, target_is_directory=True)

    result = run_sample("--image", str(image_path), "--out", str(symlink_out), "--dry-run")

    assert result.returncode != 0
    assert "must not be a symlink" in result.stderr
    assert not (real_out / "reports" / "report.json").exists()


def test_managed_output_subdir_symlink_is_rejected(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    image_path = tmp_path / "tiny.png"
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(image_path)
    out_dir = tmp_path / "sample-out"
    escape_dir = tmp_path / "escape"
    out_dir.mkdir()
    escape_dir.mkdir()
    (out_dir / "crops").symlink_to(escape_dir, target_is_directory=True)

    result = run_sample("--image", str(image_path), "--out", str(out_dir), "--dry-run")

    assert result.returncode != 0
    assert "managed output subdirectory must not be a symlink" in result.stderr
    assert not any(escape_dir.iterdir())
    assert not (out_dir / "reports" / "report.json").exists()
