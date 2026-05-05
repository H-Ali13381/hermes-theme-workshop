from __future__ import annotations

import json

from workflow.widget_pipeline.models import (
    StageResult,
    StageStatus,
    VisualScorecard,
    WidgetAction,
    WidgetElementContract,
    WidgetSampleReport,
)


def test_stage_result_json_safe_round_trip() -> None:
    result = StageResult(
        name="preview-source",
        status=StageStatus.PASS,
        reason="loaded",
        artifacts=("source.png",),
    )

    payload = result.to_dict()
    encoded = json.dumps(payload)
    restored = StageResult.from_dict(json.loads(encoded))

    assert payload == {
        "name": "preview-source",
        "status": "PASS",
        "reason": "loaded",
        "artifacts": ["source.png"],
    }
    assert restored == result


def test_widget_contract_serializes_nested_actions_json_safely() -> None:
    action = WidgetAction(
        id="open-menu",
        label="Open menu",
        command="launcher",
        command_argv=("qdbus6", "org.kde.KWin"),
        decorative=False,
        action_region=(4, 5, 30, 24),
        visual_states=("default", "hover", "pressed"),
        preconditions=("kde service org.kde.KWin is available",),
        expected_effect="launcher menu opens without KRunner search fallback",
    )
    decorative_action = WidgetAction(id="glow", label="Glow", decorative=True)
    contract = WidgetElementContract(
        id="clock",
        role="time-display",
        bbox=(10, 20, 120, 40),
        crop_path="crops/clock.png",
        priority=10,
        anchor="top-right",
        dimensions=(120, 40),
        visual_traits=("rounded", "pixel-art"),
        palette_tokens=("accent", "shadow"),
        expected_text=("12:34",),
        data_source="system_time",
        update_interval_ms=1000,
        format="HH:mm",
        actions=(action, decorative_action),
        hard_requirements=("must show current time",),
        non_goals=("no live launch in dry-run",),
    )

    payload = contract.to_dict()
    encoded = json.dumps(payload)
    restored = WidgetElementContract.from_dict(json.loads(encoded))

    assert payload["bbox"] == [10, 20, 120, 40]
    assert payload["dimensions"] == [120, 40]
    assert payload["data_source"] == "system_time"
    assert payload["update_interval_ms"] == 1000
    assert payload["format"] == "HH:mm"
    assert payload["actions"][0] == {
        "id": "open-menu",
        "label": "Open menu",
        "command": "launcher",
        "command_argv": ["qdbus6", "org.kde.KWin"],
        "decorative": False,
        "action_region": [4, 5, 30, 24],
        "visual_states": ["default", "hover", "pressed"],
        "preconditions": ["kde service org.kde.KWin is available"],
        "expected_effect": "launcher menu opens without KRunner search fallback",
    }
    assert payload["actions"][1] == {"id": "glow", "label": "Glow", "command": None, "decorative": True}
    assert restored == contract


def test_sample_report_to_dict_contains_nested_model_payloads() -> None:
    contract = WidgetElementContract(
        id="power",
        role="button",
        bbox=(1, 2, 3, 4),
        crop_path="crops/power.png",
        dimensions=(3, 4),
        actions=(WidgetAction(id="shutdown", label="Shutdown", command="systemctl poweroff"),),
    )
    score = VisualScorecard(
        contract_id="power",
        total=0.8,
        loss=0.2,
        passed=True,
        subscores={"shape": 0.9, "color": 0.7},
        comparison_path="comparisons/power.png",
        feedback="close enough",
    )
    report = WidgetSampleReport(
        framework="quickshell",
        dry_run=True,
        image_path="source.png",
        output_dir="out",
        stages=(StageResult("preview-source", StageStatus.PASS), StageResult("runtime-launch", StageStatus.SKIP, "dry-run"),),
        contracts=(contract,),
        visual_scores=(score,),
        generated_at="2026-05-04T00:00:00+00:00",
    )

    payload = report.to_dict()
    encoded = json.dumps(payload)
    restored = WidgetSampleReport.from_dict(json.loads(encoded))

    assert payload["stages"][0]["status"] == "PASS"
    assert payload["stages"][1]["status"] == "SKIP"
    assert payload["contracts"][0]["actions"][0]["command"] == "systemctl poweroff"
    assert payload["visual_scores"][0]["subscores"] == {"shape": 0.9, "color": 0.7}
    assert restored == report
