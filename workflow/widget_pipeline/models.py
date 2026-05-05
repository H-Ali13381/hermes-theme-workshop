"""Small JSON-safe data models for the widget pipeline.

These models intentionally use only the Python standard library so the first
widget-pipeline slice can run in narrow test environments without adding a
runtime dependency on Pydantic or LangGraph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StageStatus(str, Enum):
    """Status for a pipeline stage in reports."""

    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True)
class StageResult:
    name: str
    status: StageStatus
    reason: str = ""
    artifacts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "reason": self.reason,
            "artifacts": list(self.artifacts),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StageResult":
        return cls(
            name=str(data.get("name", "")),
            status=_stage_status(data.get("status", StageStatus.SKIP)),
            reason=str(data.get("reason", "")),
            artifacts=tuple(str(item) for item in data.get("artifacts", ()) or ()),
        )


@dataclass(frozen=True)
class WidgetAction:
    id: str
    label: str
    command: str | None = None
    command_argv: tuple[str, ...] = ()
    decorative: bool = False
    action_region: tuple[int, int, int, int] | None = None
    visual_states: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    expected_effect: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "command_argv", _str_tuple(self.command_argv))
        object.__setattr__(self, "visual_states", _str_tuple(self.visual_states))
        object.__setattr__(self, "preconditions", _str_tuple(self.preconditions))
        object.__setattr__(self, "expected_effect", str(self.expected_effect or ""))
        if self.action_region is not None:
            object.__setattr__(self, "action_region", _int_tuple(self.action_region, 4, "action_region"))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "label": self.label,
            "command": self.command,
            "decorative": self.decorative,
        }
        if self.command_argv:
            payload["command_argv"] = list(self.command_argv)
        if self.action_region is not None:
            payload["action_region"] = list(self.action_region)
        if self.visual_states:
            payload["visual_states"] = list(self.visual_states)
        if self.preconditions:
            payload["preconditions"] = list(self.preconditions)
        if self.expected_effect:
            payload["expected_effect"] = self.expected_effect
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WidgetAction":
        action_region = data.get("action_region")
        return cls(
            id=str(data.get("id", "")),
            label=str(data.get("label", "")),
            command=_optional_str(data.get("command")),
            command_argv=tuple(data.get("command_argv", ()) or ()),
            decorative=bool(data.get("decorative", False)),
            action_region=tuple(action_region) if action_region is not None else None,
            visual_states=tuple(data.get("visual_states", ()) or ()),
            preconditions=tuple(data.get("preconditions", ()) or ()),
            expected_effect=str(data.get("expected_effect", "") or ""),
        )


@dataclass(frozen=True)
class WidgetElementContract:
    id: str
    role: str
    bbox: tuple[int, int, int, int]
    crop_path: str
    priority: int = 0
    anchor: str = ""
    dimensions: tuple[int, int] = (0, 0)
    visual_traits: tuple[str, ...] = ()
    palette_tokens: tuple[str, ...] = ()
    expected_text: tuple[str, ...] = ()
    data_source: str = ""
    update_interval_ms: int = 0
    format: str = ""
    actions: tuple[WidgetAction, ...] = ()
    hard_requirements: tuple[str, ...] = ()
    non_goals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "bbox", _int_tuple(self.bbox, 4, "bbox"))
        object.__setattr__(self, "dimensions", _int_tuple(self.dimensions, 2, "dimensions"))
        object.__setattr__(self, "visual_traits", _str_tuple(self.visual_traits))
        object.__setattr__(self, "palette_tokens", _str_tuple(self.palette_tokens))
        object.__setattr__(self, "expected_text", _str_tuple(self.expected_text))
        object.__setattr__(self, "data_source", str(self.data_source or ""))
        object.__setattr__(self, "update_interval_ms", max(0, int(self.update_interval_ms or 0)))
        object.__setattr__(self, "format", str(self.format or ""))
        object.__setattr__(self, "actions", tuple(_coerce_action(action) for action in self.actions))
        object.__setattr__(self, "hard_requirements", _str_tuple(self.hard_requirements))
        object.__setattr__(self, "non_goals", _str_tuple(self.non_goals))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "bbox": list(self.bbox),
            "crop_path": self.crop_path,
            "priority": self.priority,
            "anchor": self.anchor,
            "dimensions": list(self.dimensions),
            "visual_traits": list(self.visual_traits),
            "palette_tokens": list(self.palette_tokens),
            "expected_text": list(self.expected_text),
            "data_source": self.data_source,
            "update_interval_ms": self.update_interval_ms,
            "format": self.format,
            "actions": [action.to_dict() for action in self.actions],
            "hard_requirements": list(self.hard_requirements),
            "non_goals": list(self.non_goals),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WidgetElementContract":
        return cls(
            id=str(data.get("id", "")),
            role=str(data.get("role", "")),
            bbox=tuple(data.get("bbox", (0, 0, 0, 0))),
            crop_path=str(data.get("crop_path", "")),
            priority=int(data.get("priority", 0)),
            anchor=str(data.get("anchor", "")),
            dimensions=tuple(data.get("dimensions", (0, 0))),
            visual_traits=tuple(data.get("visual_traits", ()) or ()),
            palette_tokens=tuple(data.get("palette_tokens", ()) or ()),
            expected_text=tuple(data.get("expected_text", ()) or ()),
            data_source=str(data.get("data_source", "") or ""),
            update_interval_ms=int(data.get("update_interval_ms", 0) or 0),
            format=str(data.get("format", "") or ""),
            actions=tuple(WidgetAction.from_dict(item) for item in data.get("actions", ()) or ()),
            hard_requirements=tuple(data.get("hard_requirements", ()) or ()),
            non_goals=tuple(data.get("non_goals", ()) or ()),
        )


@dataclass(frozen=True)
class VisualScorecard:
    contract_id: str
    total: float
    loss: float
    passed: bool
    subscores: dict[str, float] = field(default_factory=dict)
    comparison_path: str = ""
    feedback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "total": self.total,
            "loss": self.loss,
            "passed": self.passed,
            "subscores": dict(self.subscores),
            "comparison_path": self.comparison_path,
            "feedback": self.feedback,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VisualScorecard":
        return cls(
            contract_id=str(data.get("contract_id", "")),
            total=float(data.get("total", 0.0)),
            loss=float(data.get("loss", 0.0)),
            passed=bool(data.get("passed", False)),
            subscores={str(k): float(v) for k, v in dict(data.get("subscores", {}) or {}).items()},
            comparison_path=str(data.get("comparison_path", "")),
            feedback=str(data.get("feedback", "")),
        )


@dataclass(frozen=True)
class WidgetSampleReport:
    framework: str
    dry_run: bool
    image_path: str
    output_dir: str
    stages: tuple[StageResult, ...]
    contracts: tuple[WidgetElementContract, ...]
    visual_scores: tuple[VisualScorecard, ...]
    generated_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "stages", tuple(_coerce_stage(stage) for stage in self.stages))
        object.__setattr__(self, "contracts", tuple(_coerce_contract(contract) for contract in self.contracts))
        object.__setattr__(self, "visual_scores", tuple(_coerce_score(score) for score in self.visual_scores))

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework": self.framework,
            "dry_run": self.dry_run,
            "image_path": self.image_path,
            "output_dir": self.output_dir,
            "stages": [stage.to_dict() for stage in self.stages],
            "contracts": [contract.to_dict() for contract in self.contracts],
            "visual_scores": [score.to_dict() for score in self.visual_scores],
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WidgetSampleReport":
        return cls(
            framework=str(data.get("framework", "")),
            dry_run=bool(data.get("dry_run", False)),
            image_path=str(data.get("image_path", "")),
            output_dir=str(data.get("output_dir", "")),
            stages=tuple(StageResult.from_dict(item) for item in data.get("stages", ()) or ()),
            contracts=tuple(WidgetElementContract.from_dict(item) for item in data.get("contracts", ()) or ()),
            visual_scores=tuple(VisualScorecard.from_dict(item) for item in data.get("visual_scores", ()) or ()),
            generated_at=str(data.get("generated_at", "")),
        )


def _stage_status(value: Any) -> StageStatus:
    if isinstance(value, StageStatus):
        return value
    return StageStatus(str(value))


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _int_tuple(value: Any, length: int, name: str) -> tuple[int, ...]:
    items = tuple(int(item) for item in value)
    if len(items) != length:
        raise ValueError(f"{name} must contain {length} integers")
    return items


def _str_tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in (value or ()))


def _coerce_action(value: WidgetAction | dict[str, Any]) -> WidgetAction:
    if isinstance(value, WidgetAction):
        return value
    return WidgetAction.from_dict(value)


def _coerce_stage(value: StageResult | dict[str, Any]) -> StageResult:
    if isinstance(value, StageResult):
        return value
    return StageResult.from_dict(value)


def _coerce_contract(value: WidgetElementContract | dict[str, Any]) -> WidgetElementContract:
    if isinstance(value, WidgetElementContract):
        return value
    return WidgetElementContract.from_dict(value)


def _coerce_score(value: VisualScorecard | dict[str, Any]) -> VisualScorecard:
    if isinstance(value, VisualScorecard):
        return value
    return VisualScorecard.from_dict(value)
