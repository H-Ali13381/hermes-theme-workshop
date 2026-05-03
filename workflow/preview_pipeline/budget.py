from __future__ import annotations

from dataclasses import dataclass, field

MODEL_COSTS = {
    "fal-ai/nano-banana": 0.04,
    "vision-analysis": 0.0,
    "html-render": 0.0,
}


class PreviewBudgetExceeded(Exception):
    def __init__(self, remaining: float, attempted: float, model: str):
        self.remaining = remaining
        self.attempted = attempted
        self.model = model
        super().__init__(
            f"Preview budget exceeded: ${remaining:.4f} remaining, "
            f"${attempted:.4f} needed for {model}"
        )


@dataclass
class PreviewBudgetGate:
    max_budget: float = 0.08
    spent: float = 0.0
    history: list[dict] = field(default_factory=list)

    def estimate(self, model: str) -> float:
        return MODEL_COSTS.get(model, 0.04)

    def remaining(self) -> float:
        return round(max(0.0, self.max_budget - self.spent), 6)

    def can_spend(self, amount: float) -> bool:
        return self.spent + amount <= self.max_budget

    def can_spend_model(self, model: str) -> bool:
        return self.can_spend(self.estimate(model))

    def record_model(self, model: str, detail: str = "") -> float:
        amount = self.estimate(model)
        if not self.can_spend(amount):
            raise PreviewBudgetExceeded(self.remaining(), amount, model)
        self.spent = round(self.spent + amount, 6)
        self.history.append({
            "model": model,
            "amount": amount,
            "detail": detail,
            "total": self.spent,
        })
        return amount

    def summary(self) -> dict:
        by_model: dict[str, float] = {}
        for item in self.history:
            model = item["model"]
            by_model[model] = round(by_model.get(model, 0.0) + item["amount"], 6)
        return {
            "max_budget": self.max_budget,
            "spent": self.spent,
            "remaining": self.remaining(),
            "num_calls": len(self.history),
            "by_model": by_model,
            "history": list(self.history),
        }
