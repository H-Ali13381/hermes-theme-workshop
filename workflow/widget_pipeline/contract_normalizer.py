"""Normalize segmented widget regions into stable widget contracts."""

from __future__ import annotations

from typing import Any, Iterable

from .models import WidgetAction, WidgetElementContract


def normalize_regions(regions: Iterable[dict[str, Any]]) -> list[WidgetElementContract]:
    """Convert segmented region dictionaries into ``WidgetElementContract`` objects."""

    return [_normalize_region(region) for region in regions]


def _normalize_region(region: dict[str, Any]) -> WidgetElementContract:
    bbox = tuple(int(item) for item in region.get("bbox", (0, 0, 0, 0)))
    dimensions = tuple(int(item) for item in region.get("dimensions", bbox[2:4] if len(bbox) == 4 else (0, 0)))
    return WidgetElementContract(
        id=str(region.get("id", "")),
        role=str(region.get("role", "")),
        bbox=bbox,
        crop_path=str(region.get("crop_path", "")),
        priority=int(region.get("priority", 0)),
        anchor=str(region.get("anchor", "")),
        dimensions=dimensions,
        visual_traits=_string_tuple(region.get("visual_traits")),
        palette_tokens=_string_tuple(region.get("palette_tokens")),
        expected_text=_string_tuple(region.get("expected_text")),
        data_source=str(region.get("data_source", "") or ""),
        update_interval_ms=int(region.get("update_interval_ms", 0) or 0),
        format=str(region.get("format", "") or ""),
        actions=tuple(_normalize_action(action) for action in (region.get("actions") or ())),
        hard_requirements=_string_tuple(region.get("hard_requirements")),
        non_goals=_string_tuple(region.get("non_goals")),
    )


def _normalize_action(action: WidgetAction | dict[str, Any]) -> WidgetAction:
    if isinstance(action, WidgetAction):
        if action.command or action.command_argv:
            return WidgetAction(
                id=action.id,
                label=action.label,
                command=action.command,
                command_argv=action.command_argv,
                decorative=False,
                action_region=action.action_region,
                visual_states=action.visual_states,
                preconditions=action.preconditions,
                expected_effect=action.expected_effect,
            )
        return action

    command = action.get("command")
    command = None if command in (None, "") else str(command)
    command_argv = tuple(action.get("command_argv", ()) or ())
    action_region = action.get("action_region")
    return WidgetAction(
        id=str(action.get("id", "")),
        label=str(action.get("label", "")),
        command=command,
        command_argv=command_argv,
        decorative=False if command or command_argv else bool(action.get("decorative", False)),
        action_region=tuple(action_region) if action_region is not None else None,
        visual_states=_string_tuple(action.get("visual_states")),
        preconditions=_string_tuple(action.get("preconditions")),
        expected_effect=str(action.get("expected_effect", "") or ""),
    )


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(str(item) for item in (value or ()))
