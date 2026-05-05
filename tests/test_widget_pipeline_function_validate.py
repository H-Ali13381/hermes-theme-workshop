from __future__ import annotations

from pathlib import Path

from workflow.widget_pipeline.function_validate import validate_contract_actions, validate_rendered_artifact_contracts
from workflow.widget_pipeline.models import StageStatus, WidgetAction, WidgetElementContract


def contract_with_actions(*actions: WidgetAction) -> WidgetElementContract:
    return WidgetElementContract(
        id="sample",
        role="button",
        bbox=(0, 0, 16, 16),
        crop_path="sample.png",
        dimensions=(16, 16),
        actions=actions,
    )


def test_decorative_action_without_command_passes() -> None:
    contract = contract_with_actions(WidgetAction(id="ornament", label="Ornament", command=None, decorative=True))

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.PASS
    assert result.name == "function-validation"


def test_missing_non_decorative_command_skips_for_live_binding() -> None:
    contract = contract_with_actions(WidgetAction(id="workspace-select", label="Select workspace", command=None))

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.SKIP
    assert "sample:workspace-select" in result.reason
    assert "live command binding needed" in result.reason


def test_hyprctl_command_fails_on_kde_recipe() -> None:
    contract = contract_with_actions(
        WidgetAction(id="workspace-select", label="Select workspace", command="hyprctl dispatch workspace 1")
    )

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.FAIL
    assert "hyprctl" in result.reason
    assert "sample:workspace-select" in result.reason


def test_krunner_power_search_command_fails_on_kde_recipe() -> None:
    contract = contract_with_actions(
        WidgetAction(
            id="power-menu",
            label="Power menu",
            command="qdbus6 org.kde.krunner /App org.kde.krunner.App.query power",
            visual_states=("default", "hover", "pressed"),
            expected_effect="custom in-artifact power menu opens",
        )
    )

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.FAIL
    assert "KRunner power search" in result.reason
    assert "sample:power-menu" in result.reason


def test_workspace_switch_command_requires_target_count_precondition_on_kde() -> None:
    contract = contract_with_actions(
        WidgetAction(
            id="workspace-3",
            label="Workspace 3",
            command="qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 3",
            visual_states=("default", "hover", "pressed"),
            expected_effect="active desktop becomes 3",
        )
    )

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.SKIP
    assert "workspace target precondition needed" in result.reason
    assert "sample:workspace-3" in result.reason


def test_workspace_switch_command_with_precondition_passes_on_kde() -> None:
    contract = contract_with_actions(
        WidgetAction(
            id="workspace-3",
            label="Workspace 3",
            command="qdbus6 org.kde.KWin /KWin org.kde.KWin.setCurrentDesktop 3",
            visual_states=("default", "hover", "pressed"),
            preconditions=("VirtualDesktopManager count >= 3",),
            expected_effect="active desktop becomes 3",
        )
    )

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.PASS


def test_clock_contract_without_system_time_binding_skips() -> None:
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 120, 44),
        crop_path="clock.png",
        dimensions=(120, 44),
        expected_text=("12:00",),
    )

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.SKIP
    assert "clock:system_time" in result.reason
    assert "live data binding needed" in result.reason


def test_clock_contract_with_system_time_binding_passes() -> None:
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 120, 44),
        crop_path="clock.png",
        dimensions=(120, 44),
        data_source="system_time",
        update_interval_ms=1000,
        format="HH:mm",
    )

    result = validate_contract_actions([contract], desktop_recipe="kde")

    assert result.status == StageStatus.PASS
    assert "validated actions/data bindings" in result.reason


def test_rendered_artifact_validation_fails_when_live_clock_binding_is_in_different_qml(tmp_path: Path) -> None:
    contract = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 120, 44),
        crop_path="clock.png",
        dimensions=(120, 44),
        expected_text=("12:00",),
        data_source="system_time",
        update_interval_ms=1000,
        format="HH:mm",
    )
    visual_only_qml = tmp_path / "visual_only.qml"
    visual_only_qml.write_text(
        '''
import QtQuick
import Quickshell
PanelWindow {
    Item {
        objectName: "contract_clock"
        Image { anchors.fill: parent; source: "assets/clock.preview.png" }
        Text { text: "12:00" }
    }
}
''',
        encoding="utf-8",
    )

    result = validate_rendered_artifact_contracts([contract], visual_only_qml, framework="quickshell")

    assert result.status is StageStatus.FAIL
    assert result.name == "artifact-function-validation"
    assert "clock:system_time" in result.reason
    assert "same generated artifact" in result.reason


def test_rendered_artifact_validation_passes_for_same_qml_clock_and_action_hitbox(tmp_path: Path) -> None:
    clock = WidgetElementContract(
        id="clock",
        role="clock_display",
        bbox=(0, 0, 120, 44),
        crop_path="clock.png",
        dimensions=(120, 44),
        data_source="system_time",
        update_interval_ms=1000,
        format="HH:mm",
    )
    power = WidgetElementContract(
        id="power_button",
        role="power_button",
        bbox=(120, 0, 48, 44),
        crop_path="power.png",
        dimensions=(48, 44),
        actions=(WidgetAction(id="power-menu", label="Power", command="qdbus org.kde.Shutdown"),),
    )
    qml_path = tmp_path / "shell.qml"
    qml_path.write_text(
        '''
import QtQuick
import Quickshell
PanelWindow {
    Item {
        objectName: "contract_clock"
        property date currentTime: new Date()
        Timer { interval: 1000; running: true; repeat: true; onTriggered: currentTime = new Date() }
        Text { text: Qt.formatDateTime(currentTime, "HH:mm") }
    }
    Item {
        objectName: "contract_power_button"
        MouseArea {
            objectName: "contract_power_button_action_power-menu"
            anchors.fill: parent
            onClicked: console.log("qdbus org.kde.Shutdown")
        }
    }
}
''',
        encoding="utf-8",
    )

    result = validate_rendered_artifact_contracts([clock, power], qml_path, framework="quickshell")

    assert result.status is StageStatus.PASS
    assert "same generated artifact" in result.reason
    assert str(qml_path) in result.artifacts
    assert any(artifact.startswith("sha256:") for artifact in result.artifacts)


def test_rendered_artifact_validation_fails_for_flat_hitbox_without_hover_pressed_feedback(tmp_path: Path) -> None:
    power = WidgetElementContract(
        id="power_button",
        role="power_button",
        bbox=(0, 0, 48, 44),
        crop_path="power.png",
        dimensions=(48, 44),
        actions=(
            WidgetAction(
                id="power-menu",
                label="Power",
                command="console.log power",
                visual_states=("default", "hover", "pressed"),
            ),
        ),
    )
    qml_path = tmp_path / "flat.qml"
    qml_path.write_text(
        '''
import QtQuick
import Quickshell
PanelWindow {
    Item {
        objectName: "contract_power_button"
        MouseArea {
            objectName: "contract_power_button_action_power-menu"
            anchors.fill: parent
            onClicked: console.log("console.log power")
        }
    }
}
''',
        encoding="utf-8",
    )

    result = validate_rendered_artifact_contracts([power], qml_path, framework="quickshell")

    assert result.status is StageStatus.FAIL
    assert "power_button:power-menu:visual-feedback" in result.reason
