from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from workflow.widget_pipeline.adapters.quickshell import (
    render_quickshell_qml,
    scaffold_quickshell_sandbox,
    validate_quickshell_qml,
)
from workflow.nodes.craft.texture_assets import TextureAsset, TextureBundle
from workflow.widget_pipeline.asset_compiler import compile_assets_for_contracts
from workflow.widget_pipeline.models import StageStatus, WidgetAction, WidgetElementContract


def sample_contracts(tmp_path: Path) -> tuple[WidgetElementContract, ...]:
    crop = tmp_path / "crop.png"
    crop.write_bytes(b"not-used-by-qml-tests")
    return (
        WidgetElementContract(
            id="workspace_group",
            role="workspace_group",
            bbox=(0, 0, 240, 48),
            crop_path=str(crop),
            dimensions=(240, 48),
            expected_text=("1", "2", "3"),
            actions=(WidgetAction(id="workspace-select", label="Workspace", command="qdbus org.kde.KWin"),),
            visual_traits=("ornate RPG slot row",),
            hard_requirements=("use texture assets",),
        ),
        WidgetElementContract(
            id="clock",
            role="clock_display",
            bbox=(0, 48, 120, 44),
            crop_path=str(crop),
            dimensions=(120, 44),
            expected_text=("12:00",),
            data_source="system_time",
            update_interval_ms=1000,
            format="HH:mm",
        ),
        WidgetElementContract(
            id="power_button",
            role="power_button",
            bbox=(120, 48, 48, 48),
            crop_path=str(crop),
            dimensions=(48, 48),
            expected_text=("⏻",),
        ),
    )


def test_quickshell_sandbox_generates_panelwindow_manifest_and_assets(tmp_path: Path) -> None:
    contracts = sample_contracts(tmp_path)
    bundle, asset_stage = compile_assets_for_contracts(contracts, tmp_path)
    assert asset_stage.status is StageStatus.PASS

    result = scaffold_quickshell_sandbox(contracts, tmp_path, asset_bundle=bundle, no_launch=True)

    assert result.stage.status is StageStatus.PASS
    assert result.runtime_stage.status is StageStatus.SKIP
    assert result.screenshot_stage.status is StageStatus.SKIP
    sandbox = Path(result.sandbox_dir)
    assert sandbox.is_relative_to(tmp_path.resolve())
    qml_path = Path(result.qml_path)
    manifest_path = Path(result.manifest_path)
    assert qml_path.is_file()
    assert manifest_path.is_file()

    qml = qml_path.read_text(encoding="utf-8")
    assert "PanelWindow" in qml
    assert "FloatingWindow" not in qml
    assert "hyprctl" not in qml
    assert "~/.config/quickshell" not in qml
    assert "/.config/quickshell" not in qml
    for contract in contracts:
        assert f"contract_{contract.id}" in qml
    assert "BorderImage" in qml
    assert "assets/panel.png" in qml

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["framework"] == "quickshell"
    assert manifest["live_config_written"] is False
    assert manifest["static_validation"]["passed"] is True
    assert manifest["launch"]["no_launch"] is True
    assert manifest["launch"]["attempted"] is False
    assert len(manifest["contracts"]) == len(contracts)
    assert manifest["render_geometry"]["surface"]["width"] >= 360
    assert set(manifest["render_geometry"]["contracts"]) == {contract.id for contract in contracts}
    assert {Path(ref["sandbox_path"]).name for ref in manifest["asset_refs"]} >= {
        "panel.png",
        "button.png",
        "slot.png",
    }
    for artifact in result.stage.artifacts:
        assert Path(artifact).resolve().is_relative_to(tmp_path.resolve())


def test_quickshell_static_validation_rejects_unsafe_qml(tmp_path: Path) -> None:
    qml = 'FloatingWindow { Text { text: "hyprctl ~/.config/quickshell" } }'

    reasons = validate_quickshell_qml(qml, sandbox_root=tmp_path)

    assert any("PanelWindow" in reason for reason in reasons)
    assert any("FloatingWindow" in reason for reason in reasons)
    assert any("hyprctl" in reason for reason in reasons)
    assert any("live config marker" in reason for reason in reasons)


def test_quickshell_clock_uses_live_system_time_timer(tmp_path: Path) -> None:
    crop = tmp_path / "clock.png"
    crop.write_bytes(b"not-used-by-qml-tests")
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 120, 44),
        crop_path=str(crop),
        dimensions=(120, 44),
        data_source="system_time",
        update_interval_ms=1000,
        format="HH:mm",
    )

    qml = render_quickshell_qml([contract])

    assert "Timer" in qml
    assert "interval: 1000" in qml
    assert "new Date()" in qml
    assert "Qt.formatDateTime" in qml
    assert "HH:mm" in qml
    assert 'text: "12:00"' not in qml


def test_quickshell_preview_texture_mode_uses_target_crops_as_sandbox_assets(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    crop = tmp_path / "crop.png"
    Image.new("RGBA", (240, 96), (22, 14, 16, 255)).save(crop)
    contracts = sample_contracts(tmp_path)

    result = scaffold_quickshell_sandbox(contracts, tmp_path, no_launch=True, render_mode="preview_texture")

    qml = Path(result.qml_path).read_text(encoding="utf-8")
    assert "preview-texture upper-bound renderer" in qml
    assert "Image {" in qml
    assert "assets/workspace_group.preview.png" in qml
    assert "assets/clock.preview.png" in qml
    assert "assets/power_button.preview.png" in qml
    assert "x: 0; y: 48; width: 120; height: 44" in qml
    assert "Timer" in qml
    assert "new Date()" in qml
    assert "Qt.formatDateTime" in qml
    assert 'text: "12:00"' not in qml

    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["render_mode"] == "preview_texture"
    assert manifest["generated_artifacts"]["qml_path"] == str(Path(result.qml_path))
    assert len(manifest["generated_artifacts"]["qml_sha256"]) == 64
    assert manifest["live_config_written"] is False
    assert manifest["render_geometry"]["surface"] == {"width": 240, "height": 96, "origin_x": 0, "origin_y": 0}
    assert manifest["render_geometry"]["contracts"]["clock"] == [0, 48, 120, 44]
    assert (tmp_path / "sandbox" / "quickshell" / "assets" / "clock.preview.png").is_file()


def test_quickshell_preview_texture_uses_individual_command_hitboxes_for_actions(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    crop = tmp_path / "crop.png"
    Image.new("RGBA", (500, 120), (22, 14, 16, 255)).save(crop)
    contracts = (
        WidgetElementContract(
            id="workspace_group",
            role="workspace_switcher",
            bbox=(20, 20, 300, 70),
            crop_path=str(crop),
            dimensions=(300, 70),
            expected_text=("1", "2", "3"),
            actions=(
                WidgetAction(
                    id="workspace-1",
                    label="Workspace 1",
                    command="qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 1",
                ),
                WidgetAction(
                    id="workspace-2",
                    label="Workspace 2",
                    command="qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 2",
                ),
                WidgetAction(
                    id="workspace-3",
                    label="Workspace 3",
                    command="qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 3",
                ),
            ),
        ),
    )

    qml = render_quickshell_qml(contracts, render_mode="preview_texture")

    assert "import Quickshell.Io" in qml
    assert "Process {" in qml
    assert "command: [\"sh\", \"-lc\", \"qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 1\"]" in qml
    assert 'objectName: "contract_workspace_group_action_workspace-1"' in qml
    assert 'objectName: "contract_workspace_group_action_workspace-2"' in qml
    assert 'objectName: "contract_workspace_group_action_workspace-3"' in qml
    assert "width: parent.width / 3 * 0.76" in qml
    assert "height: Math.max(24, parent.height * 0.46)" in qml
    assert "x: parent.width / 3 * 0 + parent.width / 3 * 0.12" in qml
    assert "containsMouse" in qml
    assert "pressed" in qml
    assert "Behavior on scale" in qml
    assert "action_region" in qml
    assert "anchors.fill: parent" not in qml[qml.index('objectName: "contract_workspace_group_action_workspace-1"') - 220 : qml.index('objectName: "contract_workspace_group_action_workspace-1"') + 220]


def test_quickshell_preview_texture_uses_argv_process_for_safe_action_commands(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    crop = tmp_path / "crop.png"
    Image.new("RGBA", (100, 80), (22, 14, 16, 255)).save(crop)
    contracts = (
        WidgetElementContract(
            id="power_button",
            role="power_button",
            bbox=(0, 0, 80, 80),
            crop_path=str(crop),
            dimensions=(80, 80),
            actions=(
                WidgetAction(
                    id="power-menu",
                    label="Power menu",
                    command_argv=("qdbus6", "org.kde.LogoutPrompt", "/LogoutPrompt", "promptLogout"),
                    visual_states=("default", "hover", "pressed"),
                    expected_effect="custom power menu opens",
                ),
            ),
        ),
    )

    qml = render_quickshell_qml(contracts, render_mode="preview_texture")

    assert 'command: ["qdbus6", "org.kde.LogoutPrompt", "/LogoutPrompt", "promptLogout"]' in qml
    assert '["sh", "-lc"' not in qml
    assert "org.kde.krunner.App.query power" not in qml


def test_quickshell_preview_texture_mode_rejects_crop_escape(tmp_path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    outside_crop = tmp_path.parent / "outside-clock-crop.png"
    Image.new("RGBA", (32, 16), (255, 0, 0, 255)).save(outside_crop)
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 32, 16),
        crop_path=str(outside_crop),
        dimensions=(32, 16),
    )

    with pytest.raises(ValueError, match="preview texture source escapes output root"):
        scaffold_quickshell_sandbox([contract], tmp_path, no_launch=True, render_mode="preview_texture")


def test_quickshell_validation_rejects_static_clock_placeholder(tmp_path: Path) -> None:
    qml = '''
import QtQuick
import Quickshell
PanelWindow {
    Rectangle {
        objectName: "contract_clock"
        Text { anchors.centerIn: parent; text: "12:00"; color: "#e7c474" }
    }
}
'''

    reasons = validate_quickshell_qml(qml, sandbox_root=tmp_path)

    assert any("clock" in reason.lower() and "live system time" in reason.lower() for reason in reasons)


def test_quickshell_sandbox_rejects_symlinked_managed_dir(tmp_path: Path) -> None:
    contracts = sample_contracts(tmp_path)
    escape = tmp_path / "escape"
    escape.mkdir()
    sandbox_root = tmp_path / "sandbox"
    sandbox_root.mkdir()
    (sandbox_root / "quickshell").symlink_to(escape, target_is_directory=True)

    with pytest.raises(ValueError, match="managed sandbox directory must not be a symlink"):
        scaffold_quickshell_sandbox(contracts, tmp_path, no_launch=True)

    assert not any(escape.iterdir())


def test_quickshell_runtime_visual_validation_uses_bounded_sandbox_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    Image = pytest.importorskip("PIL.Image")
    contracts = sample_contracts(tmp_path)

    class FakeProcess:
        pid = 4242

        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args[0]
            self.returncode = None

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.returncode = -15

        def wait(self, timeout: float | None = None) -> int:
            self.returncode = -15
            return self.returncode

        def kill(self) -> None:
            self.returncode = -9

    def fake_which(name: str) -> str | None:
        return {"quickshell": "/usr/bin/quickshell", "spectacle": "/usr/bin/spectacle"}.get(name)

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output = Path(cmd[-1])
        image = Image.new("RGBA", (800, 240), (35, 24, 18, 255))
        for x in range(0, 800, 20):
            for y in range(0, 240, 20):
                if (x + y) // 20 % 2 == 0:
                    image.paste((80, 45, 25, 255), (x, y, min(x + 20, 800), min(y + 20, 240)))
        image.save(output)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.shutil.which", fake_which)
    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.subprocess.Popen", FakeProcess)
    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.subprocess.run", fake_run)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-test")

    result = scaffold_quickshell_sandbox(contracts, tmp_path, no_launch=False)

    assert result.runtime_stage.status is StageStatus.PASS
    assert "bounded Quickshell sandbox launch" in result.runtime_stage.reason
    assert result.screenshot_stage.status is StageStatus.PASS
    assert "captured sandbox screenshot" in result.screenshot_stage.reason
    screenshot = Path(result.screenshot_stage.artifacts[0])
    assert screenshot.is_file()
    assert screenshot.resolve().is_relative_to(tmp_path.resolve())

    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["live_config_written"] is False
    assert manifest["launch"]["attempted"] is True
    assert manifest["launch"]["stage"]["status"] == "PASS"
    assert manifest["screenshot"]["status"] == "PASS"


def test_quickshell_sandbox_rejects_symlinked_fixed_files(tmp_path: Path) -> None:
    contracts = sample_contracts(tmp_path)
    escape = tmp_path / "escape.qml"
    escape.write_text("do-not-overwrite", encoding="utf-8")
    quickshell_dir = tmp_path / "sandbox" / "quickshell"
    quickshell_dir.mkdir(parents=True)
    (quickshell_dir / "shell.qml").symlink_to(escape)

    with pytest.raises(ValueError, match="managed sandbox file must not be a symlink"):
        scaffold_quickshell_sandbox(contracts, tmp_path, no_launch=True)

    assert escape.read_text(encoding="utf-8") == "do-not-overwrite"


def test_quickshell_sandbox_rejects_asset_source_escape(tmp_path: Path) -> None:
    contracts = sample_contracts(tmp_path)
    escaped = tmp_path.parent / "escaped-asset.png"
    escaped.write_bytes(b"not-a-real-png-but-copy-would-have-leaked")
    bundle = TextureBundle(
        root=str(tmp_path),
        theme_slug="evil",
        metadata_path="texture_bundle.json",
        assets=(
            TextureAsset(
                variant="panel",
                path="../escaped-asset.png",
                slice_px=8,
                width=1,
                height=1,
                seam_score=0.0,
                sha256="0" * 64,
            ),
        ),
    )

    with pytest.raises(ValueError, match="asset source escapes output root"):
        scaffold_quickshell_sandbox(contracts, tmp_path, asset_bundle=bundle, no_launch=True)

    assert not (tmp_path / "sandbox" / "quickshell" / "assets" / "panel.png").exists()


def test_quickshell_runtime_cleanup_terminates_process_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    Image = pytest.importorskip("PIL.Image")
    contracts = sample_contracts(tmp_path)
    killpg_calls: list[tuple[int, int]] = []

    class FakeProcess:
        pid = 7777
        returncode = None

        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args[0]

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.returncode = -15

        def wait(self, timeout: float | None = None) -> int:
            self.returncode = -15
            return self.returncode

        def kill(self) -> None:
            self.returncode = -9

    def fake_which(name: str) -> str | None:
        return {"quickshell": "/usr/bin/quickshell", "spectacle": "/usr/bin/spectacle"}.get(name)

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output = Path(cmd[-1])
        image = Image.new("RGBA", (60, 60), (15, 15, 15, 255))
        image.paste((200, 120, 40, 255), (5, 5, 30, 30))
        image.save(output)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    def fake_killpg(pid: int, sig: int) -> None:
        killpg_calls.append((pid, sig))

    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.shutil.which", fake_which)
    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.subprocess.Popen", FakeProcess)
    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.subprocess.run", fake_run)
    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.os.killpg", fake_killpg)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-test")

    scaffold_quickshell_sandbox(contracts, tmp_path, no_launch=False)

    assert killpg_calls
    assert killpg_calls[0][0] == 7777


def test_quickshell_manifest_records_attempted_launch_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contracts = sample_contracts(tmp_path)

    def fake_which(name: str) -> str | None:
        return "/usr/bin/quickshell" if name == "quickshell" else None

    def fake_popen(*args: object, **kwargs: object) -> object:
        raise OSError("boom")

    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.shutil.which", fake_which)
    monkeypatch.setattr("workflow.widget_pipeline.adapters.quickshell.subprocess.Popen", fake_popen)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-test")

    result = scaffold_quickshell_sandbox(contracts, tmp_path, no_launch=False)

    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert result.runtime_stage.status is StageStatus.FAIL
    assert manifest["launch"]["attempted"] is True
    assert manifest["launch"]["stage"]["status"] == "FAIL"
