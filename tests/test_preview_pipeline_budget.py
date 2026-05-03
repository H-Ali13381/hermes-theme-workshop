import pytest

from workflow.preview_pipeline.budget import PreviewBudgetExceeded, PreviewBudgetGate


def test_budget_gate_records_nano_banana_spend():
    gate = PreviewBudgetGate(max_budget=0.08)

    assert gate.can_spend_model("fal-ai/nano-banana")
    gate.record_model("fal-ai/nano-banana", detail="hero")

    summary = gate.summary()
    assert summary["spent"] > 0
    assert summary["num_calls"] == 1
    assert summary["by_model"]["fal-ai/nano-banana"] == summary["spent"]


def test_budget_gate_blocks_second_generation_when_limit_too_low():
    gate = PreviewBudgetGate(max_budget=0.05)
    gate.record_model("fal-ai/nano-banana", detail="hero")

    with pytest.raises(PreviewBudgetExceeded):
        gate.record_model("fal-ai/nano-banana", detail="regenerate")
