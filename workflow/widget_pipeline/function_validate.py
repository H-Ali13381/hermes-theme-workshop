"""Dry-run function/action validation for widget contracts."""

from __future__ import annotations

from pathlib import Path
import hashlib
from typing import Any, Iterable

from .models import StageResult, StageStatus, WidgetAction, WidgetElementContract


def validate_contract_actions(
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    desktop_recipe: str = "kde",
) -> StageResult:
    """Validate action bindings without executing or launching anything.

    Decorative actions are explicitly acceptable in dry-run mode. Non-decorative
    actions need command bindings before the pipeline can claim functional
    readiness. KDE recipes reject Hyprland-only commands early.
    """

    normalized = tuple(_coerce_contract(contract) for contract in contracts)
    recipe = desktop_recipe.strip().lower()
    missing: list[str] = []
    rejected: list[str] = []
    missing_data: list[str] = []
    missing_workspace_preconditions: list[str] = []

    for contract in normalized:
        role = contract.role.strip().lower()
        if "clock" in role and contract.data_source.strip().lower() != "system_time":
            missing_data.append(f"{contract.id}:system_time")
        for action in contract.actions:
            label = f"{contract.id}:{action.id or action.label}"
            command = _action_command_text(action)
            command_lower = command.lower()
            if command and recipe == "kde" and "hyprctl" in command_lower:
                rejected.append(f"{label}:hyprctl")
            if command and recipe == "kde" and _is_krunner_power_search(command_lower):
                rejected.append(f"{label}:KRunner power search")
            workspace_target = _workspace_target(command_lower)
            if recipe == "kde" and workspace_target is not None and not _has_workspace_target_precondition(action.preconditions, workspace_target):
                missing_workspace_preconditions.append(label)
            if not action.decorative and not command:
                missing.append(label)

    if rejected:
        return StageResult(
            "function-validation",
            StageStatus.FAIL,
            "kde recipe rejects unsafe commands for " + ", ".join(rejected),
        )
    if missing:
        return StageResult(
            "function-validation",
            StageStatus.SKIP,
            "live command binding needed for " + ", ".join(missing),
        )
    if missing_workspace_preconditions:
        return StageResult(
            "function-validation",
            StageStatus.SKIP,
            "workspace target precondition needed for " + ", ".join(missing_workspace_preconditions),
        )
    if missing_data:
        return StageResult(
            "function-validation",
            StageStatus.SKIP,
            "live data binding needed for " + ", ".join(missing_data),
        )
    return StageResult(
        "function-validation",
        StageStatus.PASS,
        f"validated actions/data bindings for {len(normalized)} contracts ({desktop_recipe} dry-run)",
    )


def validate_rendered_artifact_contracts(
    contracts: Iterable[WidgetElementContract | dict[str, Any]],
    artifact_path: str | Path,
    *,
    framework: str = "quickshell",
) -> StageResult:
    """Verify semantic bindings exist in the same rendered artifact used for review.

    Contract-only validation proves the spec asks for live data/actions; this
    function proves the generated widget file being visually scored also contains
    those bindings. This prevents validating a visual-only crop renderer and a
    separate functional component renderer as if they were one widget.
    """

    normalized = tuple(_coerce_contract(contract) for contract in contracts)
    artifact = Path(artifact_path).expanduser().resolve()
    if not artifact.exists() or not artifact.is_file():
        return StageResult(
            "artifact-function-validation",
            StageStatus.FAIL,
            f"same generated artifact missing: {artifact}",
            artifacts=(str(artifact),),
        )

    text = artifact.read_text(encoding="utf-8")
    lowered = text.lower()
    reasons: list[str] = []
    fw = framework.strip().lower()
    if fw != "quickshell":
        return StageResult(
            "artifact-function-validation",
            StageStatus.SKIP,
            f"same generated artifact semantic validation not implemented for {framework}",
            artifacts=(str(artifact), f"sha256:{_sha256_file(artifact)}"),
        )

    for contract in normalized:
        cid = _qml_string_fragment(contract.id)
        if f'objectname: "contract_{cid}"' not in lowered and f'objectname: "contract_{cid}_' not in lowered:
            reasons.append(f"{contract.id}:contract-marker")
        role = contract.role.strip().lower()
        if "clock" in role and contract.data_source.strip().lower() == "system_time":
            required = ("timer", "new date()", "qt.formatdatetime")
            if not all(token in lowered for token in required):
                reasons.append(f"{contract.id}:system_time")
            if contract.format and contract.format.lower() not in lowered:
                reasons.append(f"{contract.id}:format")
            for expected in contract.expected_text:
                static_text = f'text: "{str(expected).lower()}"'
                if static_text in lowered:
                    reasons.append(f"{contract.id}:static-placeholder")
                    break
        for action in contract.actions:
            action_id = _qml_string_fragment(action.id or action.label)
            action_marker = f'objectname: "contract_{cid}_action_{action_id}"'
            if "mousearea" not in lowered or action_marker not in lowered:
                reasons.append(f"{contract.id}:{action.id or action.label}:hitbox")
            command = _action_command_text(action).lower()
            if command and command not in lowered:
                reasons.append(f"{contract.id}:{action.id or action.label}:command")
            states = {state.strip().lower() for state in action.visual_states}
            if {"hover", "pressed"}.issubset(states):
                feedback_tokens = ("containsmouse", "pressed", "behavior on scale")
                if not all(token in lowered for token in feedback_tokens):
                    reasons.append(f"{contract.id}:{action.id or action.label}:visual-feedback")

    digest = _sha256_file(artifact)
    artifacts = (str(artifact), f"sha256:{digest}")
    if reasons:
        return StageResult(
            "artifact-function-validation",
            StageStatus.FAIL,
            "same generated artifact is missing live bindings/hitboxes for " + ", ".join(reasons),
            artifacts=artifacts,
        )
    return StageResult(
        "artifact-function-validation",
        StageStatus.PASS,
        f"same generated artifact carries required semantic bindings for {len(normalized)} contracts",
        artifacts=artifacts,
    )



def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



def _qml_string_fragment(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').lower()


def _action_command_text(action: WidgetAction) -> str:
    if action.command:
        return action.command.strip()
    if action.command_argv:
        return " ".join(action.command_argv).strip()
    return ""


def _is_krunner_power_search(command_lower: str) -> bool:
    return "org.kde.krunner" in command_lower and "org.kde.krunner.app.query" in command_lower and "power" in command_lower


def _workspace_target(command_lower: str) -> int | None:
    token = "org.kde.kwin.setcurrentdesktop"
    if token not in command_lower:
        return None
    parts = command_lower.split()
    for item in reversed(parts):
        try:
            return int(item)
        except ValueError:
            continue
    return None


def _has_workspace_target_precondition(preconditions: Iterable[str], target: int) -> bool:
    target_text = str(target)
    for precondition in preconditions:
        lowered = str(precondition).lower()
        if "virtualdesktopmanager" in lowered and "count" in lowered and target_text in lowered:
            return True
        if "workspace" in lowered and "count" in lowered and target_text in lowered:
            return True
    return False


def _coerce_contract(value: WidgetElementContract | dict[str, Any]) -> WidgetElementContract:
    if isinstance(value, WidgetElementContract):
        return value
    return WidgetElementContract.from_dict(value)
