"""Quickshell sandbox adapter for Milestone 2 widget pipeline validation.

This adapter writes a reviewable Quickshell/QML prototype under the caller's
``--out`` tree only. It does not promote, install, reload, or write live
``~/.config/quickshell`` configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from typing import Any, Iterable

from workflow.nodes.craft.texture_assets import TextureBundle

from ..models import StageResult, StageStatus, WidgetAction, WidgetElementContract
from ..safe_paths import safe_artifact_path

_LIVE_CONFIG_MARKERS = (
    "~/.config/quickshell",
    "/.config/quickshell",
    "~/.config/eww",
    "/.config/eww",
    "~/.config/ags",
    "/.config/ags",
    "~/.config/fabric",
    "/.config/fabric",
    "plasma-org.kde.plasma.desktop-appletsrc",
)
_FORBIDDEN_QML_TOKENS = ("FloatingWindow", "hyprctl")


@dataclass(frozen=True)
class QuickshellSandboxResult:
    sandbox_dir: str
    manifest_path: str
    qml_path: str
    stage: StageResult
    runtime_stage: StageResult
    screenshot_stage: StageResult
    screenshot_path: str = ""
    runtime_surface_bbox: tuple[int, int, int, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sandbox_dir": self.sandbox_dir,
            "manifest_path": self.manifest_path,
            "qml_path": self.qml_path,
            "stage": self.stage.to_dict(),
            "runtime_stage": self.runtime_stage.to_dict(),
            "screenshot_stage": self.screenshot_stage.to_dict(),
            "screenshot_path": self.screenshot_path,
            "runtime_surface_bbox": list(self.runtime_surface_bbox) if self.runtime_surface_bbox else None,
        }


def scaffold_quickshell_sandbox(
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    output_root: str | Path,
    *,
    asset_bundle: TextureBundle | None = None,
    desktop_recipe: str = "kde",
    no_launch: bool = True,
    render_mode: str = "components",
) -> QuickshellSandboxResult:
    """Generate sandbox-local Quickshell files and an auditable manifest."""

    normalized_contracts = tuple(_coerce_contract(contract) for contract in contracts)
    if render_mode not in {"components", "preview_texture"}:
        raise ValueError(f"unsupported Quickshell render mode: {render_mode}")
    output_root = Path(output_root).expanduser().resolve()
    sandbox_dir = _safe_managed_dir(output_root, "sandbox")
    quickshell_dir = _safe_managed_dir(sandbox_dir, "quickshell")
    assets_dir = _safe_managed_dir(quickshell_dir, "assets")
    screenshots_dir = _safe_managed_dir(output_root, "screenshots")

    asset_refs = _copy_asset_refs(asset_bundle, output_root, assets_dir) if asset_bundle is not None else []
    preview_texture_refs = _copy_preview_texture_refs(normalized_contracts, output_root, assets_dir) if render_mode == "preview_texture" else []
    render_geometry = _preview_texture_geometry(normalized_contracts) if render_mode == "preview_texture" else _render_geometry(normalized_contracts)
    qml = render_quickshell_qml(
        normalized_contracts,
        asset_refs=asset_refs,
        desktop_recipe=desktop_recipe,
        render_geometry=render_geometry,
        render_mode=render_mode,
        preview_texture_refs=preview_texture_refs,
    )
    static_reasons = validate_quickshell_qml(qml, sandbox_root=quickshell_dir)

    qml_path = _safe_fixed_file(quickshell_dir, "shell.qml")
    qml_path.write_text(qml, encoding="utf-8")
    qml_sha256 = _sha256_file(qml_path)

    artifacts = [str(qml_path), *(str(ref["sandbox_path"]) for ref in asset_refs), *(str(ref["sandbox_path"]) for ref in preview_texture_refs)]
    manifest_path = _safe_fixed_file(quickshell_dir, "manifest.json")
    runtime_stage, screenshot_stage, screenshot_path, runtime_surface_bbox = _runtime_and_screenshot_stages(
        quickshell_dir, qml_path, screenshots_dir=screenshots_dir, no_launch=no_launch, render_geometry=render_geometry
    )

    status = StageStatus.FAIL if static_reasons else StageStatus.PASS
    reason = (
        "; ".join(static_reasons)
        if static_reasons
        else f"generated Quickshell sandbox for {len(normalized_contracts)} widget contracts"
    )
    stage = StageResult("quickshell-sandbox", status, reason, artifacts=tuple(artifacts + [str(manifest_path)]))

    manifest = {
        "framework": "quickshell",
        "render_mode": render_mode,
        "desktop_recipe": desktop_recipe,
        "sandbox_dir": str(quickshell_dir),
        "live_config_written": False,
        "contracts": [contract.to_dict() for contract in normalized_contracts],
        "generated_files": [str(qml_path)],
        "generated_artifacts": {
            "qml_path": str(qml_path),
            "qml_sha256": qml_sha256,
            "semantic_validation_target": str(qml_path),
        },
        "render_geometry": render_geometry,
        "asset_refs": [
            {"variant": ref["variant"], "source_path": str(ref["source_path"]), "sandbox_path": str(ref["sandbox_path"])}
            for ref in [*asset_refs, *preview_texture_refs]
        ],
        "launch": {
            "attempted": runtime_stage.status is not StageStatus.SKIP,
            "stage": runtime_stage.to_dict(),
            "command": _launch_command(shutil.which("quickshell") or "quickshell", qml_path),
            "no_launch": bool(no_launch),
        },
        "screenshot": screenshot_stage.to_dict(),
        "runtime_surface_bbox": list(runtime_surface_bbox) if runtime_surface_bbox else None,
        "static_validation": {
            "passed": not static_reasons,
            "reasons": static_reasons,
            "requires_panel_window": True,
            "forbids_floating_window": True,
            "forbids_hyprctl_on_kde": desktop_recipe.lower() == "kde",
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return QuickshellSandboxResult(
        sandbox_dir=str(quickshell_dir),
        manifest_path=str(manifest_path),
        qml_path=str(qml_path),
        stage=stage,
        runtime_stage=runtime_stage,
        screenshot_stage=screenshot_stage,
        screenshot_path=screenshot_path,
        runtime_surface_bbox=runtime_surface_bbox,
    )


def render_quickshell_qml(
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    *,
    asset_refs: list[dict[str, Any]] | None = None,
    desktop_recipe: str = "kde",
    render_geometry: dict[str, Any] | None = None,
    render_mode: str = "components",
    preview_texture_refs: list[dict[str, Any]] | None = None,
) -> str:
    normalized_contracts = tuple(_coerce_contract(contract) for contract in contracts)
    asset_refs = asset_refs or []
    preview_texture_refs = preview_texture_refs or []
    panel_asset = _asset_url(asset_refs, "panel")
    button_asset = _asset_url(asset_refs, "button")
    slot_asset = _asset_url(asset_refs, "slot")
    if render_geometry is None:
        render_geometry = _preview_texture_geometry(normalized_contracts) if render_mode == "preview_texture" else _render_geometry(normalized_contracts)
    width = int(render_geometry["surface"]["width"])
    height = int(render_geometry["surface"]["height"])
    if render_mode == "preview_texture":
        return _render_preview_texture_qml(
            normalized_contracts,
            desktop_recipe=desktop_recipe,
            render_geometry=render_geometry,
            preview_texture_refs=preview_texture_refs,
            width=width,
            height=height,
        )
    body = "\n".join(_qml_for_contract(contract, button_asset=button_asset, slot_asset=slot_asset) for contract in normalized_contracts)
    contract_ids = ", ".join(contract.id for contract in normalized_contracts)
    return f"""// Generated by linux-ricing widget pipeline Milestone 2.
// Sandbox-only Quickshell prototype. Contracts: {contract_ids}
// Desktop recipe: {desktop_recipe}
import QtQuick
import QtQuick.Layouts
import Quickshell

PanelWindow {{
    id: widgetSandboxRoot
    objectName: "widget_pipeline_quickshell_sandbox"
    implicitWidth: {width}
    implicitHeight: {height}
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore

    Rectangle {{
        id: blackironPanel
        objectName: "contract_full_hud_panel"
        anchors.fill: parent
        radius: 14
        color: "#130e10"
        border.color: "#c49137"
        border.width: 1

        BorderImage {{
            id: panelTexture
            anchors.fill: parent
            source: "{panel_asset}"
            border.left: 12; border.right: 12; border.top: 12; border.bottom: 12
            visible: source !== ""
        }}

        ColumnLayout {{
            anchors.fill: parent
            anchors.margins: 12
            spacing: 8
{body}
        }}
    }}
}}
"""


def _render_preview_texture_qml(
    contracts: tuple[WidgetElementContract, ...],
    *,
    desktop_recipe: str,
    render_geometry: dict[str, Any],
    preview_texture_refs: list[dict[str, Any]],
    width: int,
    height: int,
) -> str:
    texture_by_id = {str(ref.get("contract_id", "")): "assets/" + Path(ref["sandbox_path"]).name for ref in preview_texture_refs}
    contract_boxes = render_geometry.get("contracts", {}) if isinstance(render_geometry, dict) else {}
    image_nodes: list[str] = []
    for contract in contracts:
        box = contract_boxes.get(contract.id, [0, 0, *_contract_dimensions(contract)])
        x, y, local_width, local_height = (int(value) for value in box)
        cid = _qml_string(contract.id)
        source = _qml_string(texture_by_id.get(contract.id, ""))
        overlay = _preview_texture_functional_overlay(contract)
        image_nodes.append(
            f"""        Item {{
            objectName: "contract_{cid}"
            x: {x}; y: {y}; width: {max(1, local_width)}; height: {max(1, local_height)}
            Image {{
                objectName: "contract_{cid}_texture"
                anchors.fill: parent
                source: "{source}"
                fillMode: Image.Stretch
                smooth: true
                mipmap: true
                visible: source !== ""
            }}
{overlay}
        }}"""
        )
    contract_ids = ", ".join(contract.id for contract in contracts)
    body = "\n".join(image_nodes)
    io_import = "import Quickshell.Io\n" if _contracts_have_commands(contracts) else ""
    return f"""// Generated by linux-ricing widget pipeline Milestone 3.
// Sandbox-only Quickshell preview-texture upper-bound renderer. Contracts: {contract_ids}
// Desktop recipe: {desktop_recipe}
import QtQuick
import Quickshell
{io_import}
PanelWindow {{
    id: widgetSandboxRoot
    objectName: "widget_pipeline_quickshell_sandbox"
    implicitWidth: {width}
    implicitHeight: {height}
    color: "transparent"
    exclusionMode: ExclusionMode.Ignore

    Item {{
        objectName: "preview_texture_surface"
        anchors.fill: parent
{body}
    }}
}}
"""


def _preview_texture_functional_overlay(contract: WidgetElementContract) -> str:
    """Return transparent/live controls layered over copied target crops.

    Preview-texture mode must be the same QML artifact that carries semantic
    bindings; otherwise visual validation and manual functionality checks test
    different widgets. Keep overlays minimal so the crop remains visually close
    while dynamic contracts such as clocks are actually live.
    """

    role = contract.role.lower()
    cid = _qml_string(contract.id)
    if "clock" in role and contract.data_source.strip().lower() == "system_time":
        interval = max(250, int(contract.update_interval_ms or 1000))
        time_format = _qml_string(contract.format or "HH:mm")
        qid = _qml_identifier(f"preview_clock_{contract.id}")
        return f"""            Item {{
                id: {qid}
                objectName: "contract_{cid}_live_binding"
                anchors.fill: parent
                property date currentTime: new Date()
                function refreshClock() {{ currentTime = new Date() }}
                Timer {{
                    interval: {interval}
                    running: true
                    repeat: true
                    triggeredOnStart: true
                    onTriggered: {qid}.refreshClock()
                }}
                Text {{
                    anchors.centerIn: parent
                    text: Qt.formatDateTime({qid}.currentTime, "{time_format}")
                    color: "#f7d77a"
                    font.pixelSize: Math.max(14, Math.min(parent.width * 0.16, parent.height * 0.34))
                    font.bold: true
                    style: Text.Outline
                    styleColor: "#1b0d08"
                }}
            }}"""
    if contract.actions:
        if "workspace" in role and len(contract.actions) > 1:
            return _preview_texture_workspace_action_overlay(contract)
        return _preview_texture_centered_action_overlay(contract)
    return ""


def _preview_texture_workspace_action_overlay(contract: WidgetElementContract) -> str:
    cid = _qml_string(contract.id)
    action_count = max(1, len(contract.actions))
    process_nodes: list[str] = []
    mouse_nodes: list[str] = []
    for index, action in enumerate(contract.actions):
        aid = _qml_string(action.id or action.label or f"action_{index}")
        label = _qml_string(action.label or action.id or f"Action {index + 1}")
        command = _qml_string(_action_command_text(action))
        decorative = "true" if action.decorative else "false"
        process_id = _qml_identifier(f"action_{contract.id}_{action.id or index}")
        process_nodes.append(_qml_process_node(process_id, action, indent="                "))
        click_body = _qml_action_click_body(
            process_id,
            cid=cid,
            aid=aid,
            label=label,
            decorative=decorative,
            command=command,
            indent="                        ",
            has_command=bool(action.command or action.command_argv),
        )
        region_id = _qml_identifier(f"action_region_{contract.id}_{action.id or index}")
        mouse_id = _qml_identifier(f"action_mouse_{contract.id}_{action.id or index}")
        mouse_nodes.append(
            f"""                Item {{
                    id: {region_id}
                    objectName: "contract_{cid}_action_{aid}"
                    property string action_region: x + "," + y + "," + width + "," + height
                    x: parent.width / {action_count} * {index} + parent.width / {action_count} * 0.12
                    y: parent.height * 0.27
                    width: parent.width / {action_count} * 0.76
                    height: Math.max(24, parent.height * 0.46)
                    scale: {mouse_id}.pressed ? 0.94 : ({mouse_id}.containsMouse ? 1.04 : 1.0)
                    Behavior on scale {{ NumberAnimation {{ duration: 90; easing.type: Easing.OutQuad }} }}
                    Rectangle {{
                        anchors.fill: parent
                        radius: Math.max(4, height * 0.18)
                        color: {mouse_id}.pressed ? "#7a241d" : ({mouse_id}.containsMouse ? "#4a2b22" : "transparent")
                        border.color: {mouse_id}.pressed ? "#f2c15b" : ({mouse_id}.containsMouse ? "#c49137" : "transparent")
                        border.width: {mouse_id}.containsMouse || {mouse_id}.pressed ? 2 : 0
                        opacity: {mouse_id}.containsMouse || {mouse_id}.pressed ? 0.72 : 0.0
                        Behavior on opacity {{ NumberAnimation {{ duration: 90 }} }}
                    }}
                    MouseArea {{
                        id: {mouse_id}
                        x: 0; y: 0; width: parent.width; height: parent.height
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {{
{click_body}
                        }}
                    }}
                }}"""
        )
    return "            Item {\n                anchors.fill: parent\n" + "\n".join(process_nodes + mouse_nodes) + "\n            }"


def _preview_texture_centered_action_overlay(contract: WidgetElementContract) -> str:
    cid = _qml_string(contract.id)
    nodes: list[str] = []
    for index, action in enumerate(contract.actions):
        aid = _qml_string(action.id or action.label or f"action_{index}")
        label = _qml_string(action.label or action.id or f"Action {index + 1}")
        command = _qml_string(_action_command_text(action))
        decorative = "true" if action.decorative else "false"
        process_id = _qml_identifier(f"action_{contract.id}_{action.id or index}")
        nodes.append(_qml_process_node(process_id, action, indent="                "))
        click_body = _qml_action_click_body(
            process_id,
            cid=cid,
            aid=aid,
            label=label,
            decorative=decorative,
            command=command,
            indent="                        ",
            has_command=bool(action.command or action.command_argv),
        )
        region_id = _qml_identifier(f"action_region_{contract.id}_{action.id or index}")
        mouse_id = _qml_identifier(f"action_mouse_{contract.id}_{action.id or index}")
        nodes.append(
            f"""                Item {{
                    id: {region_id}
                    objectName: "contract_{cid}_action_{aid}"
                    property string action_region: x + "," + y + "," + width + "," + height
                    anchors.centerIn: parent
                    width: Math.max(28, Math.min(parent.width, parent.height) * 0.72)
                    height: width
                    scale: {mouse_id}.pressed ? 0.92 : ({mouse_id}.containsMouse ? 1.05 : 1.0)
                    Behavior on scale {{ NumberAnimation {{ duration: 90; easing.type: Easing.OutQuad }} }}
                    Rectangle {{
                        anchors.fill: parent
                        radius: width / 2
                        color: {mouse_id}.pressed ? "#7a241d" : ({mouse_id}.containsMouse ? "#4a2b22" : "transparent")
                        border.color: {mouse_id}.pressed ? "#f2c15b" : ({mouse_id}.containsMouse ? "#c49137" : "transparent")
                        border.width: {mouse_id}.containsMouse || {mouse_id}.pressed ? 2 : 0
                        opacity: {mouse_id}.containsMouse || {mouse_id}.pressed ? 0.72 : 0.0
                        Behavior on opacity {{ NumberAnimation {{ duration: 90 }} }}
                    }}
                    MouseArea {{
                        id: {mouse_id}
                        x: 0; y: 0; width: parent.width; height: parent.height
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {{
{click_body}
                        }}
                    }}
                }}"""
        )
    return "            Item {\n                anchors.fill: parent\n" + "\n".join(nodes) + "\n            }"


def _contracts_have_commands(contracts: Iterable[WidgetElementContract]) -> bool:
    return any(bool(action.command or action.command_argv) for contract in contracts for action in contract.actions)


def _qml_process_node(process_id: str, action: WidgetAction, *, indent: str) -> str:
    if not (action.command or action.command_argv):
        return ""
    command = _qml_command_array(action)
    return (
        f'{indent}Process {{\n'
        f'{indent}    id: {process_id}\n'
        f'{indent}    command: {command}\n'
        f'{indent}    running: false\n'
        f'{indent}}}'
    )


def _qml_command_array(action: WidgetAction) -> str:
    if action.command_argv:
        return json.dumps(list(action.command_argv))
    return f'["sh", "-lc", "{_qml_string(action.command or "")}"]'


def _action_command_text(action: WidgetAction) -> str:
    if action.command:
        return action.command.strip()
    if action.command_argv:
        return " ".join(action.command_argv).strip()
    return ""


def _qml_action_click_body(
    process_id: str,
    *,
    cid: str,
    aid: str,
    label: str,
    decorative: str,
    command: str,
    indent: str,
    has_command: bool,
) -> str:
    lines = [
        f'{indent}console.log("widget-pipeline action", "{cid}", "{aid}", "{label}", "decorative={decorative}", "command={command}")'
    ]
    if has_command:
        lines.append(f"{indent}{process_id}.running = false")
        lines.append(f"{indent}{process_id}.running = true")
    return "\n".join(lines)


def _render_geometry(contracts: Iterable[WidgetElementContract]) -> dict[str, Any]:
    normalized = tuple(contracts)
    width = max(360, min(1200, max((contract.bbox[2] for contract in normalized), default=480)))
    margin = 12
    spacing = 8
    y = margin
    contract_boxes: dict[str, list[int]] = {}
    for contract in normalized:
        _, preferred_height = _contract_dimensions(contract)
        height = max(32, min(96, preferred_height))
        role = contract.role.lower()
        if "workspace" in role:
            slot_count = max(1, min(8, len(contract.expected_text) or 5))
            local_width = slot_count * 34 + max(0, slot_count - 1) * 6
        elif "power" in role:
            local_width = max(42, min(96, contract.bbox[2]))
        else:
            local_width = width - margin * 2
        contract_boxes[contract.id] = [margin, y, max(1, int(local_width)), int(height)]
        y += height + spacing
    surface_height = max(72, min(640, y - spacing + margin if normalized else 96))
    return {
        "surface": {"width": int(width), "height": int(surface_height), "margin": margin, "spacing": spacing},
        "contracts": contract_boxes,
    }


def _preview_texture_geometry(contracts: Iterable[WidgetElementContract]) -> dict[str, Any]:
    normalized = tuple(contracts)
    if not normalized:
        return {"surface": {"width": 1, "height": 1, "origin_x": 0, "origin_y": 0}, "contracts": {}}
    min_x = min(int(contract.bbox[0]) for contract in normalized)
    min_y = min(int(contract.bbox[1]) for contract in normalized)
    max_x = max(int(contract.bbox[0]) + max(1, int(contract.bbox[2])) for contract in normalized)
    max_y = max(int(contract.bbox[1]) + max(1, int(contract.bbox[3])) for contract in normalized)
    contract_boxes = {
        contract.id: [
            int(contract.bbox[0]) - min_x,
            int(contract.bbox[1]) - min_y,
            max(1, int(contract.bbox[2])),
            max(1, int(contract.bbox[3])),
        ]
        for contract in normalized
    }
    return {
        "surface": {"width": max(1, max_x - min_x), "height": max(1, max_y - min_y), "origin_x": min_x, "origin_y": min_y},
        "contracts": contract_boxes,
    }


def validate_quickshell_qml(qml: str, *, sandbox_root: str | Path) -> list[str]:
    reasons: list[str] = []
    if "PanelWindow" not in qml:
        reasons.append("Quickshell sandbox must use PanelWindow")
    for token in _FORBIDDEN_QML_TOKENS:
        if token in qml:
            reasons.append(f"Quickshell sandbox must not contain {token}")
    lowered = qml.lower()
    if 'objectname: "contract_clock"' in lowered and 'text: "12:00"' in lowered:
        live_clock_tokens = ("timer", "new date()", "qt.formatdatetime")
        if not all(token in lowered for token in live_clock_tokens):
            reasons.append("Quickshell clock contract must use live system time instead of static 12:00 text")
    for marker in _LIVE_CONFIG_MARKERS:
        if marker.lower() in lowered:
            reasons.append(f"Quickshell sandbox must not reference live config marker {marker}")
    sandbox = Path(sandbox_root).resolve()
    if sandbox.is_symlink():
        reasons.append(f"Quickshell sandbox root must not be a symlink: {sandbox}")
    return reasons


def _qml_for_contract(contract: WidgetElementContract, *, button_asset: str, slot_asset: str) -> str:
    cid = _qml_string(contract.id)
    role = contract.role.lower()
    width, height = _contract_dimensions(contract)
    if "workspace" in role:
        labels = contract.expected_text or ("1", "2", "3", "4", "5")
        buttons = "\n".join(
            f"""                    Rectangle {{
                        objectName: "contract_{cid}_slot_{index}"
                        width: 34; height: 30; radius: 6
                        color: {repr('#4a2b22' if index == 0 else '#21191b')}
                        border.color: "#c49137"
                        Text {{ anchors.centerIn: parent; text: "{_qml_string(label)}"; color: "#e7c474" }}
                        BorderImage {{ anchors.fill: parent; source: "{slot_asset}"; border.left: 8; border.right: 8; border.top: 8; border.bottom: 8; visible: source !== "" }}
                    }}""".replace("'", '"')
            for index, label in enumerate(labels)
        )
        return f"""            RowLayout {{
                objectName: "contract_{cid}"
                Layout.preferredHeight: {max(32, min(72, height))}
                spacing: 6
{buttons}
            }}"""
    if "clock" in role:
        label = contract.expected_text[0] if contract.expected_text else "12:00"
        if contract.data_source.strip().lower() == "system_time":
            interval = max(250, int(contract.update_interval_ms or 1000))
            time_format = _qml_string(contract.format or "HH:mm")
            qid = _qml_identifier(f"clock_{contract.id}")
            return f"""            Rectangle {{
                id: {qid}
                objectName: "contract_{cid}"
                Layout.fillWidth: true
                Layout.preferredHeight: {max(32, min(72, height))}
                radius: 8
                color: "#21191b"
                border.color: "#c49137"
                property date currentTime: new Date()
                function refreshClock() {{ currentTime = new Date() }}
                Timer {{
                    interval: {interval}
                    running: true
                    repeat: true
                    triggeredOnStart: true
                    onTriggered: {qid}.refreshClock()
                }}
                Text {{ anchors.centerIn: parent; text: Qt.formatDateTime({qid}.currentTime, "{time_format}"); color: "#e7c474" }}
            }}"""
        return f"""            Rectangle {{
                objectName: "contract_{cid}"
                Layout.fillWidth: true
                Layout.preferredHeight: {max(32, min(72, height))}
                radius: 8
                color: "#21191b"
                border.color: "#c49137"
                Text {{ anchors.centerIn: parent; text: "{_qml_string(label)}"; color: "#e7c474" }}
            }}"""
    if "status" in role or "bar" in role:
        return f"""            ColumnLayout {{
                objectName: "contract_{cid}"
                Layout.fillWidth: true
                Layout.preferredHeight: {max(38, min(90, height))}
                spacing: 4
                Repeater {{
                    model: [0.72, 0.54]
                    Rectangle {{
                        Layout.fillWidth: true; height: 12; radius: 6
                        color: "#1b1416"; border.color: "#c49137"
                        Rectangle {{ width: parent.width * modelData; height: parent.height - 4; x: 2; y: 2; radius: 4; color: index === 0 ? "#671c20" : "#254f5e" }}
                    }}
                }}
            }}"""
    if "power" in role:
        return f"""            Rectangle {{
                objectName: "contract_{cid}"
                Layout.preferredWidth: {max(42, min(96, width))}
                Layout.preferredHeight: {max(42, min(96, height))}
                radius: width / 2
                color: "#842d22"
                border.color: "#f2c15b"
                BorderImage {{ anchors.fill: parent; source: "{button_asset}"; border.left: 8; border.right: 8; border.top: 8; border.bottom: 8; visible: source !== "" }}
                Text {{ anchors.centerIn: parent; text: "⏻"; color: "#f2c15b" }}
            }}"""
    label = contract.expected_text[0] if contract.expected_text else contract.id.replace("_", " ")
    return f"""            Rectangle {{
                objectName: "contract_{cid}"
                Layout.fillWidth: true
                Layout.preferredHeight: {max(40, min(120, height))}
                radius: 10
                color: "#21191b"
                border.color: "#c49137"
                Text {{ anchors.centerIn: parent; text: "{_qml_string(label[:30])}"; color: "#e7c474" }}
            }}"""


def _runtime_and_screenshot_stages(
    quickshell_dir: Path,
    qml_path: Path,
    *,
    screenshots_dir: Path,
    no_launch: bool,
    render_geometry: dict[str, Any] | None = None,
    launch_settle_seconds: float = 1.0,
    capture_timeout_seconds: float = 8.0,
) -> tuple[StageResult, StageResult, str, tuple[int, int, int, int] | None]:
    """Launch sandbox QML long enough to capture a screen artifact, then clean up."""

    if no_launch:
        return (
            StageResult("runtime-launch", StageStatus.SKIP, "no-launch requested; generated sandbox only"),
            StageResult("screenshot-capture", StageStatus.SKIP, "no-launch requested; screenshot capture skipped"),
            "",
            None,
        )

    executable = shutil.which("quickshell")
    if not executable:
        return (
            StageResult("runtime-launch", StageStatus.SKIP, "quickshell executable not found; sandbox generated but not launched"),
            StageResult("screenshot-capture", StageStatus.SKIP, "runtime launch skipped; screenshot capture unavailable"),
            "",
            None,
        )

    if not (os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY")):
        return (
            StageResult("runtime-launch", StageStatus.SKIP, "no graphical session detected; sandbox generated but not launched"),
            StageResult("screenshot-capture", StageStatus.SKIP, "no graphical session detected; screenshot capture skipped"),
            "",
            None,
        )

    log_path = _safe_fixed_file(quickshell_dir, "runtime.log")
    command = _launch_command(executable, qml_path)
    process: subprocess.Popen[str] | None = None
    baseline_stage, baseline_path = _capture_screenshot(
        screenshots_dir,
        timeout_seconds=capture_timeout_seconds,
        filename="quickshell-baseline.png",
        stage_name="screenshot-baseline",
    )
    try:
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                command,
                cwd=quickshell_dir,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
            time.sleep(max(0.0, launch_settle_seconds))
            if process.poll() is not None:
                return (
                    StageResult(
                        "runtime-launch",
                        StageStatus.FAIL,
                        f"Quickshell sandbox exited before screenshot capture with code {process.returncode}",
                        artifacts=(str(log_path), str(qml_path)),
                    ),
                    StageResult("screenshot-capture", StageStatus.SKIP, "runtime launch failed before screenshot capture"),
                    "",
                    None,
                )

            runtime_stage = StageResult(
                "runtime-launch",
                StageStatus.PASS,
                "bounded Quickshell sandbox launch stayed alive for screenshot capture",
                artifacts=(str(log_path), str(qml_path), str(quickshell_dir)),
            )
            screenshot_stage, screenshot_path = _capture_screenshot(screenshots_dir, timeout_seconds=capture_timeout_seconds)
            runtime_surface_bbox = None
            if screenshot_stage.status is StageStatus.PASS and baseline_stage.status is StageStatus.PASS and render_geometry:
                runtime_surface_bbox = _diff_surface_bbox(Path(baseline_path), Path(screenshot_path), render_geometry)
                artifacts = tuple(screenshot_stage.artifacts) + (str(baseline_path),)
                reason = screenshot_stage.reason
                if runtime_surface_bbox:
                    reason += "; localized sandbox surface by before/after diff"
                else:
                    reason += "; before/after diff could not isolate sandbox surface"
                screenshot_stage = StageResult(screenshot_stage.name, screenshot_stage.status, reason, artifacts=artifacts)
            return runtime_stage, screenshot_stage, screenshot_path, runtime_surface_bbox
    except OSError as exc:
        return (
            StageResult("runtime-launch", StageStatus.FAIL, f"failed to launch Quickshell sandbox: {exc}", artifacts=(str(log_path), str(qml_path))),
            StageResult("screenshot-capture", StageStatus.SKIP, "runtime launch failed before screenshot capture"),
            "",
            None,
        )
    finally:
        if process is not None and process.poll() is None:
            _terminate_process_group(process)


def _capture_screenshot(
    screenshots_dir: Path,
    *,
    timeout_seconds: float,
    filename: str = "quickshell-sandbox.png",
    stage_name: str = "screenshot-capture",
) -> tuple[StageResult, str]:
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = _safe_fixed_file(screenshots_dir, filename)
    tool = shutil.which("spectacle")
    if tool:
        command = [tool, "-b", "-n", "-o", str(screenshot_path)]
    else:
        tool = shutil.which("grim")
        if tool:
            command = [tool, str(screenshot_path)]
        else:
            return StageResult(stage_name, StageStatus.SKIP, "no supported screenshot tool found (spectacle or grim)"), ""

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return StageResult(stage_name, StageStatus.FAIL, f"screenshot command failed: {exc}"), ""

    if completed.returncode != 0:
        reason = (completed.stderr or completed.stdout or f"exit code {completed.returncode}").strip()
        return StageResult(stage_name, StageStatus.FAIL, f"screenshot command failed: {reason}"), ""
    if not screenshot_path.is_file():
        return StageResult(stage_name, StageStatus.FAIL, "screenshot tool reported success but did not create an image"), ""
    blank_reason = _blank_screenshot_reason(screenshot_path)
    if blank_reason:
        return StageResult(stage_name, StageStatus.FAIL, blank_reason, artifacts=(str(screenshot_path),)), str(screenshot_path)
    return (
        StageResult(stage_name, StageStatus.PASS, "captured sandbox screenshot", artifacts=(str(screenshot_path),)),
        str(screenshot_path),
    )


def _diff_surface_bbox(
    baseline_path: Path,
    screenshot_path: Path,
    render_geometry: dict[str, Any],
) -> tuple[int, int, int, int] | None:
    surface = render_geometry.get("surface") if isinstance(render_geometry, dict) else None
    if not isinstance(surface, dict):
        return None
    expected_width = int(surface.get("width") or 0)
    expected_height = int(surface.get("height") or 0)
    if expected_width <= 0 or expected_height <= 0:
        return None

    try:
        from PIL import Image

        with Image.open(baseline_path) as before_image, Image.open(screenshot_path) as after_image:
            before = before_image.convert("RGB")
            after = after_image.convert("RGB")
            if before.size != after.size:
                return None
            scale = 4 if max(before.size) >= 1600 else 1
            small_size = (max(1, before.size[0] // scale), max(1, before.size[1] // scale))
            if scale > 1:
                before = before.resize(small_size)
                after = after.resize(small_size)
            width, height = after.size
            before_pixels = before.load()
            after_pixels = after.load()
            changed: set[tuple[int, int]] = set()
            for y in range(height):
                for x in range(width):
                    br, bg, bb = before_pixels[x, y]
                    ar, ag, ab = after_pixels[x, y]
                    if max(abs(ar - br), abs(ag - bg), abs(ab - bb)) >= 18:
                        changed.add((x, y))
    except Exception:
        return None

    if not changed:
        return None

    components: list[tuple[int, int, int, int, int]] = []
    while changed:
        start = changed.pop()
        stack = [start]
        area = 0
        min_x = max_x = start[0]
        min_y = max_y = start[1]
        while stack:
            x, y = stack.pop()
            area += 1
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            for ny in (y - 1, y, y + 1):
                for nx in (x - 1, x, x + 1):
                    point = (nx, ny)
                    if point in changed:
                        changed.remove(point)
                        stack.append(point)
        observed_width = (max_x - min_x + 1) * scale
        observed_height = (max_y - min_y + 1) * scale
        if area >= 8:
            components.append((area, min_x * scale, min_y * scale, observed_width, observed_height))

    if not components:
        return None

    def component_score(component: tuple[int, int, int, int, int]) -> tuple[float, int]:
        area, _, _, observed_width, observed_height = component
        width_ratio = observed_width / max(1, expected_width)
        height_ratio = observed_height / max(1, expected_height)
        if not (0.35 <= width_ratio <= 3.2 and 0.35 <= height_ratio <= 3.2):
            return (999.0, -area)
        scale_consistency = abs(width_ratio - height_ratio)
        scale_integer_penalty = abs(round((width_ratio + height_ratio) / 2.0) - ((width_ratio + height_ratio) / 2.0))
        return (scale_consistency + scale_integer_penalty * 0.25, -area)

    best = min(components, key=component_score)
    if component_score(best)[0] >= 999.0:
        return None
    _, origin_x, origin_y, observed_width, observed_height = best
    return int(origin_x), int(origin_y), int(observed_width), int(observed_height)


def _blank_screenshot_reason(path: Path) -> str:
    try:
        from PIL import Image, ImageStat

        with Image.open(path) as image:
            rgba = image.convert("RGBA")
            if rgba.size[0] <= 1 or rgba.size[1] <= 1:
                return "screenshot is too small to validate"
            alpha_extrema = rgba.getchannel("A").getextrema()
            if alpha_extrema == (0, 0):
                return "screenshot is fully transparent"
            stat = ImageStat.Stat(rgba.convert("L"))
            extrema = rgba.convert("L").getextrema()
            if extrema[0] == extrema[1] and stat.stddev[0] < 0.01:
                return "screenshot appears blank/flat color"
    except Exception as exc:  # pragma: no cover - defensive clarity for corrupt screenshots
        return f"failed to inspect screenshot: {exc}"
    return ""


def _launch_command(binary: str, qml_path: Path) -> list[str]:
    return [binary, "--path", str(qml_path), "--no-color"]


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()
        process.wait(timeout=2)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_asset_refs(bundle: TextureBundle, output_root: Path, assets_dir: Path) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for asset in bundle.assets:
        source = (output_root / asset.path).resolve()
        if not source.is_relative_to(output_root.resolve()):
            raise ValueError(f"asset source escapes output root: {source}")
        if not source.is_file():
            continue
        dest = safe_artifact_path(assets_dir, asset.variant, ".png")
        _reject_existing_symlink(dest)
        shutil.copy2(source, dest)
        refs.append({"variant": asset.variant, "source_path": source, "sandbox_path": dest})
    return refs


def _copy_preview_texture_refs(
    contracts: Iterable[WidgetElementContract], output_root: Path, assets_dir: Path
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    resolved_output = output_root.resolve()
    for contract in contracts:
        crop = Path(contract.crop_path).expanduser()
        if crop.is_symlink():
            raise ValueError(f"preview texture source must not be a symlink: {crop}")
        source = crop.resolve()
        if not source.is_relative_to(resolved_output):
            raise ValueError(f"preview texture source escapes output root: {source}")
        if not source.is_file():
            raise ValueError(f"preview texture source is missing: {source}")
        dest = safe_artifact_path(assets_dir, contract.id, ".preview.png")
        _reject_existing_symlink(dest)
        shutil.copy2(source, dest)
        refs.append({
            "variant": f"preview:{contract.id}",
            "contract_id": contract.id,
            "source_path": source,
            "sandbox_path": dest,
        })
    return refs


def _asset_url(asset_refs: list[dict[str, Any]], variant: str) -> str:
    for ref in asset_refs:
        if ref.get("variant") == variant:
            return "assets/" + Path(ref["sandbox_path"]).name
    return ""


def _safe_managed_dir(parent: Path, name: str) -> Path:
    path = parent / name
    if path.is_symlink():
        raise ValueError(f"managed sandbox directory must not be a symlink: {path}")
    path.mkdir(parents=True, exist_ok=True)
    resolved_parent = parent.resolve()
    resolved_path = path.resolve()
    if not resolved_path.is_relative_to(resolved_parent):
        raise ValueError(f"managed sandbox directory escapes parent: {path}")
    return path


def _safe_fixed_file(parent: Path, name: str) -> Path:
    path = parent / name
    _reject_existing_symlink(path)
    resolved_parent = parent.resolve()
    resolved_path = path.resolve()
    if resolved_path.parent != resolved_parent:
        raise ValueError(f"managed sandbox file escapes parent: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"managed sandbox file must be a regular file: {path}")
    return path


def _reject_existing_symlink(path: Path) -> None:
    if path.is_symlink():
        raise ValueError(f"managed sandbox file must not be a symlink: {path}")


def _coerce_contract(value: WidgetElementContract | dict[str, Any]) -> WidgetElementContract:
    if isinstance(value, WidgetElementContract):
        return value
    return WidgetElementContract.from_dict(value)


def _contract_dimensions(contract: WidgetElementContract) -> tuple[int, int]:
    width, height = contract.dimensions
    if width <= 0 or height <= 0:
        width, height = contract.bbox[2], contract.bbox[3]
    return max(1, int(width)), max(1, int(height))


def _qml_string(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _qml_identifier(value: object) -> str:
    identifier = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(value))
    if not identifier or identifier[0].isdigit():
        identifier = f"widget_{identifier}"
    return identifier
