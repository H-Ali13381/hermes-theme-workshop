# Desktop Preview Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor linux-ricing Step 2.5 desktop preview generation into a Hermesfy-inspired internal DAG pipeline with explicit paid-generation budget control, stable artifact caching, desktop-specific validation, and edit/re-run semantics.

**Architecture:** Keep `workflow/nodes/visualize.py` as the LangGraph/user approval gate, but move the generation/analysis/rendering internals into a new `workflow/preview_pipeline/` package. The new package models the paid preview flow as explicit nodes: prompt build → FAL desktop overview → multimodal analysis → desktop contract validation → HTML render → artifact persistence. This preserves existing nano-banana behavior and `FAL_KEY` resolution while adding Hermesfy-style budget, events, status, validation, and future variant support.

**Tech Stack:** Python 3.10+, LangGraph node integration, existing `fal-client`, existing LangChain `get_llm()`, JSON/YAML-compatible dataclasses, pytest.

---

## Current context

Existing Step 2.5 lives mostly in:
- `workflow/nodes/visualize.py`
  - `visualize_node()`
  - `_generate_style_image()`
  - `_build_desktop_preview_prompt()`
  - `_analyze_image_multimodal()`
  - `_render_style_html()`
  - `_save_pending_preview()` / `_load_pending_preview()`
- `workflow/state.py`
  - `visualize_image_url`
  - `visualize_html_path`
  - `visual_context`
  - `visualize_route`
- `workflow/nodes/plan.py`
  - `_render_preview(..., visual_context=...)`
- Current focused tests mentioned by the skill:
  - `tests/test_visualize_preview_prompt.py`
  - `tests/test_refine_prompt_handoff.py`
  - `tests/test_preview_renderer.py`
  - `tests/test_resume_control.py`

Non-negotiables to preserve:
- Use `fal-ai/nano-banana`, not Flux, for the full-desktop overview.
- Use `FAL_KEY` resolution via `resolve_env_secret("FAL_KEY")`.
- Generate at most one paid hero image by default.
- Preserve `visualize.pending.json` re-entry safety.
- Do not let HTML replace the generated hero image; HTML frames it.
- Approval caveat behavior stays exact: `approve` means approve, freeform feedback regenerates.
- No manual checkpoint or `design.json` mutation.

---

## Proposed file structure

Create:
- `workflow/preview_pipeline/__init__.py`
  - Public exports for pipeline types and `run_desktop_preview_pipeline()`.

- `workflow/preview_pipeline/types.py`
  - Small dataclasses/enums: `PreviewNodeType`, `PreviewNode`, `PreviewEdge`, `PreviewWorkflow`, `PreviewEvent`, `PreviewArtifact`, `PreviewRunResult`, `PreviewRunOptions`.

- `workflow/preview_pipeline/budget.py`
  - `PreviewBudgetGate`, `PreviewBudgetExceeded`, model cost estimates, and session budget summary serialization.

- `workflow/preview_pipeline/cache.py`
  - Load/save/clear `visualize.pending.json` and future `preview_pipeline.history.jsonl`.

- `workflow/preview_pipeline/prompts.py`
  - Move `_select_overview_aspect_ratio()`, `_build_desktop_preview_prompt()`, and analysis/HTML system prompts out of `visualize.py`.

- `workflow/preview_pipeline/providers.py`
  - Thin wrapper around `fal_client.subscribe("fal-ai/nano-banana", ...)`.
  - Keeps the exact nano-banana argument schema.

- `workflow/preview_pipeline/validators.py`
  - Deterministic validation for prompt invariants, FAL call schema, visual context shape, and generated preview contract.
  - Optional LLM/vision validation hook later.

- `workflow/preview_pipeline/executor.py`
  - Hermesfy-style topological executor for preview nodes.
  - Handles node reference resolution, events, budget, cache reuse, and failure reporting.

- `workflow/preview_pipeline/templates.py`
  - Programmatic builders for default desktop overview pipeline and future variant pipelines.

Modify:
- `workflow/nodes/visualize.py`
  - Keep only LangGraph interrupt/routing logic plus compatibility wrappers if needed by tests.
  - Delegate generation/analysis/rendering/cache persistence to `run_desktop_preview_pipeline()`.

- `workflow/state.py`
  - Add optional `preview_pipeline_status: dict` and `preview_budget: dict`.
  - Keep existing fields for compatibility.

- `references/desktop-preview-generation.md`
  - Document the new module layout, budget gate, validation responsibilities, and test commands.

Add tests:
- `tests/test_preview_pipeline_budget.py`
- `tests/test_preview_pipeline_executor.py`
- `tests/test_preview_pipeline_cache.py`
- `tests/test_preview_pipeline_validators.py`
- Extend `tests/test_visualize_preview_prompt.py`
- Extend `tests/test_resume_control.py`

---

## Task 1: Introduce preview pipeline data types

**Files:**
- Create: `workflow/preview_pipeline/__init__.py`
- Create: `workflow/preview_pipeline/types.py`
- Test: `tests/test_preview_pipeline_executor.py`

- [ ] **Step 1: Write failing tests for basic graph/type construction**

Create `tests/test_preview_pipeline_executor.py` with:

```python
from workflow.preview_pipeline.types import (
    PreviewEdge,
    PreviewNode,
    PreviewNodeType,
    PreviewWorkflow,
)


def test_preview_workflow_accepts_desktop_nodes():
    wf = PreviewWorkflow(
        id="preview-1",
        name="desktop-overview",
        nodes=[
            PreviewNode(id="prompt", type=PreviewNodeType.DESKTOP_PROMPT, config={"direction": {}}),
            PreviewNode(id="image", type=PreviewNodeType.FAL_DESKTOP_CONCEPT, config={"prompt": "{{prompt.prompt}}"}),
        ],
        edges=[PreviewEdge(source="prompt", target="image")],
    )

    assert wf.id == "preview-1"
    assert wf.nodes[0].type is PreviewNodeType.DESKTOP_PROMPT
    assert wf.edges[0].source == "prompt"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python -m pytest tests/test_preview_pipeline_executor.py::test_preview_workflow_accepts_desktop_nodes -q
```

Expected: import failure because `workflow.preview_pipeline` does not exist.

- [ ] **Step 3: Implement types**

Create `workflow/preview_pipeline/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PreviewNodeType(str, Enum):
    DESKTOP_PROMPT = "desktop_prompt"
    FAL_DESKTOP_CONCEPT = "fal_desktop_concept"
    MULTIMODAL_ANALYSIS = "multimodal_analysis"
    CONTRACT_VALIDATE = "contract_validate"
    STYLE_HTML_RENDER = "style_html_render"
    CACHE_ARTIFACTS = "cache_artifacts"


@dataclass(frozen=True)
class PreviewEdge:
    source: str
    target: str


@dataclass
class PreviewNode:
    id: str
    type: PreviewNodeType
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreviewWorkflow:
    id: str
    name: str
    nodes: list[PreviewNode]
    edges: list[PreviewEdge]


@dataclass
class PreviewEvent:
    node_id: str
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreviewArtifact:
    kind: str
    path: str = ""
    url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreviewRunOptions:
    session_dir: str
    fal_key: str = ""
    use_cache: bool = True
    budget_limit: float | None = 0.08
    allow_paid_generation: bool = True
    regenerate: bool = False


@dataclass
class PreviewRunResult:
    image_url: str = ""
    html_path: str = ""
    visual_context: dict[str, Any] = field(default_factory=dict)
    artifacts: list[PreviewArtifact] = field(default_factory=list)
    events: list[PreviewEvent] = field(default_factory=list)
    budget: dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    error: str = ""
```

Create `workflow/preview_pipeline/__init__.py`:

```python
from .types import (
    PreviewArtifact,
    PreviewEdge,
    PreviewEvent,
    PreviewNode,
    PreviewNodeType,
    PreviewRunOptions,
    PreviewRunResult,
    PreviewWorkflow,
)

__all__ = [
    "PreviewArtifact",
    "PreviewEdge",
    "PreviewEvent",
    "PreviewNode",
    "PreviewNodeType",
    "PreviewRunOptions",
    "PreviewRunResult",
    "PreviewWorkflow",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python -m pytest tests/test_preview_pipeline_executor.py::test_preview_workflow_accepts_desktop_nodes -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add workflow/preview_pipeline/__init__.py workflow/preview_pipeline/types.py tests/test_preview_pipeline_executor.py
git commit -m "feat: add desktop preview pipeline types"
```

---

## Task 2: Add budget gate for paid preview generation

**Files:**
- Create: `workflow/preview_pipeline/budget.py`
- Test: `tests/test_preview_pipeline_budget.py`

- [ ] **Step 1: Write failing budget tests**

Create `tests/test_preview_pipeline_budget.py`:

```python
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
```

- [ ] **Step 2: Run test to verify failure**

```bash
python -m pytest tests/test_preview_pipeline_budget.py -q
```

Expected: import failure.

- [ ] **Step 3: Implement budget gate**

Create `workflow/preview_pipeline/budget.py`:

```python
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
```

- [ ] **Step 4: Run budget tests**

```bash
python -m pytest tests/test_preview_pipeline_budget.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add workflow/preview_pipeline/budget.py tests/test_preview_pipeline_budget.py
git commit -m "feat: add paid preview budget gate"
```

---

## Task 3: Move preview prompt logic into pipeline module

**Files:**
- Create: `workflow/preview_pipeline/prompts.py`
- Modify: `workflow/nodes/visualize.py`
- Test: `tests/test_visualize_preview_prompt.py`

- [ ] **Step 1: Add tests proving exported prompt invariants**

Extend `tests/test_visualize_preview_prompt.py` with:

```python
from workflow.preview_pipeline.prompts import build_desktop_preview_prompt


def test_pipeline_prompt_preserves_desktop_overview_invariants():
    prompt = build_desktop_preview_prompt(
        {
            "name": "bonfire-hollow",
            "aesthetic": "Dark Souls campfire in a ruined RPG menu",
            "mood_tags": ["soot", "ember", "thin thorn borders"],
        },
        aspect_ratio="16:9",
    )

    required = [
        "full Linux desktop theme concept preview",
        "single representative overview image",
        "entire desktop UI",
        "screenshot-style mockup",
        "ornate window borders",
        "themed terminal window",
        "launcher/menu panel",
        "widget menus",
        "icon style",
        "edge-to-edge",
        "no cinematic letterbox bars",
    ]
    for phrase in required:
        assert phrase.lower() in prompt.lower()

    forbidden = ["no UI chrome", "landscape-only", "environment only", "mood painting only"]
    for phrase in forbidden:
        assert phrase.lower() not in prompt.lower()
```

- [ ] **Step 2: Run test to verify failure**

```bash
python -m pytest tests/test_visualize_preview_prompt.py::test_pipeline_prompt_preserves_desktop_overview_invariants -q
```

Expected: import failure.

- [ ] **Step 3: Implement `prompts.py` by moving logic from `visualize.py`**

Create `workflow/preview_pipeline/prompts.py` with:

```python
from __future__ import annotations

import json

ANALYSIS_SYSTEM_PROMPT = """\
You are a visual design analyst. Given a reference image and a creative direction,
extract a coherent color palette and design guidance for a Linux desktop theme.

Return JSON only with:
- extracted_palette: object with background, foreground, accent, accent2, muted, border, danger, success, warning, shadow
- style_description: concise visual summary
- ui_chrome_guidance: concrete guidance for window borders, terminal, launcher, panel/widgets, icons, menu surfaces
- visual_element_plan: list of implementable visible elements, each with id, source_visual_description, desktop_element, implementation_tool, fallback_tool, config_targets, validation_probe, acceptable_deviation
- validation_checklist: list of concrete visual checks for later plan/implementation verification

All palette values must be valid #rrggbb hex. danger=red, success=green, warning=amber.
Break the generated image into concrete, implementable desktop elements before recommending tools.
Prefer Quickshell for KDE/Wayland custom toolbar/widget chrome; use EWW only as an explicit fallback.
"""

PREVIEW_SYSTEM_PROMPT = """\
You are generating the Step 2.5 AI desktop theme preview HTML page for a Linux desktop theme.

The FAL/nano-banana image is the representative desktop overview and must dominate the page.
Do not reinterpret it into a generic HTML dashboard, style guide, or card grid. The page's
job is to present the single generated desktop overview as the primary artifact, then add
supporting palette and terminal/color readouts underneath.

Show:
1. The AI-generated full-desktop theme concept image as a dominant representative overview (<img> with the provided URL)
2. The 10 extracted palette swatches with hex labels
3. Terminal color views and a concise UI breakdown: window borders, terminal, launcher, panel/widgets, icon/menu direction
4. Style description and atmosphere text

Use CSS only to frame and support the hero: animations, gradients, filters, custom properties,
ornamental borders, and mood lighting are welcome, but the generated image remains primary.
The page itself should embody the theme mood — not a generic card layout.
Output ONLY the complete HTML file. No markdown fences, no explanation.
"""


def select_overview_aspect_ratio(profile: dict | None) -> str:
    profile = profile or {}
    width, height = _primary_screen_size(profile) or (1920, 1080)
    if width <= 0 or height <= 0:
        return "16:9"
    ratio = width / height
    if ratio >= 2.1:
        return "21:9"
    if ratio <= 1.45:
        return "4:3"
    if 1.45 < ratio < 1.7:
        return "3:2"
    return "16:9"


def _primary_screen_size(profile: dict) -> tuple[int, int] | None:
    primary = profile.get("primary_screen")
    if isinstance(primary, dict):
        try:
            return int(primary.get("width", 0)), int(primary.get("height", 0))
        except (TypeError, ValueError):
            return None
    screens = profile.get("screens")
    if isinstance(screens, list) and screens:
        first = screens[0]
        if isinstance(first, dict):
            try:
                return int(first.get("width", 0)), int(first.get("height", 0))
            except (TypeError, ValueError):
                return None
    return None


def aspect_prompt_phrase(aspect_ratio: str) -> str:
    if aspect_ratio == "21:9":
        return "ultrawide/multi-monitor desktop overview around 21:9, composed across the full visible layout"
    if aspect_ratio == "4:3":
        return "classic 4:3 desktop overview"
    if aspect_ratio == "3:2":
        return "3:2 desktop overview"
    return "16:9 primary-monitor desktop overview"


def build_desktop_preview_prompt(direction: dict, aspect_ratio: str = "16:9") -> str:
    direction_json = json.dumps(direction or {}, ensure_ascii=False, indent=2)
    aspect = aspect_prompt_phrase(aspect_ratio)
    return f"""
Full Linux desktop theme concept preview. Generate one single representative overview image: a complete desktop screenshot-style mockup that becomes the centerpiece of the design system.

Target composition: {aspect}. Fill the canvas edge-to-edge with the desktop overview; no cinematic letterbox bars, no black bands above or below, no framed movie-still presentation.

Show the entire desktop UI as a coherent screenshot-style mockup: ornate window borders, themed terminal window, launcher/menu panel, top or bottom system panel, widget menus, icon style, wallpaper background, and custom application chrome all designed as one unified theme.

For dark RPG/game-menu styling, include thin thorn-like borders, soot/ash/worn-metal/parchment surfaces where appropriate, ember/campfire lighting, readable UI labels, terminal/menu affordances, glyph-like original icons, and high-contrast usable regions. The result must read as an operating system desktop, not a landscape-only painting, environment only, mood painting only, generic dashboard, or default desktop chrome.

Creative direction JSON:
{direction_json}
""".strip()
```

- [ ] **Step 4: Modify `visualize.py` imports without changing behavior**

In `workflow/nodes/visualize.py`, import from `workflow.preview_pipeline.prompts` and keep compatibility aliases:

```python
from ..preview_pipeline.prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    PREVIEW_SYSTEM_PROMPT,
    aspect_prompt_phrase as _aspect_prompt_phrase,
    build_desktop_preview_prompt as _build_desktop_preview_prompt,
    select_overview_aspect_ratio as _select_overview_aspect_ratio,
)
```

Then delete the duplicate local prompt constants/functions only after tests pass.

- [ ] **Step 5: Run prompt tests**

```bash
python -m pytest tests/test_visualize_preview_prompt.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add workflow/preview_pipeline/prompts.py workflow/nodes/visualize.py tests/test_visualize_preview_prompt.py
git commit -m "refactor: move desktop preview prompts into pipeline"
```

---

## Task 4: Extract stable preview cache handling

**Files:**
- Create: `workflow/preview_pipeline/cache.py`
- Modify: `workflow/nodes/visualize.py`
- Test: `tests/test_preview_pipeline_cache.py`
- Extend: `tests/test_resume_control.py`

- [ ] **Step 1: Write cache tests**

Create `tests/test_preview_pipeline_cache.py`:

```python
from workflow.preview_pipeline.cache import (
    clear_pending_preview,
    load_pending_preview,
    save_pending_preview,
)


def test_pending_preview_round_trip(tmp_path):
    html_path = tmp_path / "visualize.html"
    html_path.write_text("<html></html>")
    visual_context = {"reference_image_url": "https://example.com/hero.png", "extracted_palette": {}}

    save_pending_preview(str(tmp_path), "https://example.com/hero.png", html_path, visual_context)
    loaded = load_pending_preview(str(tmp_path))

    assert loaded["image_url"] == "https://example.com/hero.png"
    assert loaded["html_path"] == str(html_path)
    assert loaded["visual_context"] == visual_context


def test_pending_preview_malformed_json_returns_empty(tmp_path):
    (tmp_path / "visualize.pending.json").write_text("not json")
    assert load_pending_preview(str(tmp_path)) == {}


def test_clear_pending_preview_removes_file(tmp_path):
    save_pending_preview(str(tmp_path), "url", tmp_path / "visualize.html", {})
    clear_pending_preview(str(tmp_path))
    assert load_pending_preview(str(tmp_path)) == {}
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_preview_pipeline_cache.py -q
```

Expected: import failure.

- [ ] **Step 3: Implement cache module**

Create `workflow/preview_pipeline/cache.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def pending_preview_path(session_dir: str) -> Path:
    return Path(session_dir).expanduser() / "visualize.pending.json"


def load_pending_preview(session_dir: str) -> dict[str, Any]:
    path = pending_preview_path(session_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    if not isinstance(data.get("image_url"), str):
        return {}
    if not isinstance(data.get("visual_context"), dict):
        data["visual_context"] = {}
    return data


def save_pending_preview(session_dir: str, image_url: str, html_path: Path, visual_context: dict) -> None:
    path = pending_preview_path(session_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "image_url": image_url,
        "html_path": str(html_path),
        "visual_context": visual_context if isinstance(visual_context, dict) else {},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def clear_pending_preview(session_dir: str) -> None:
    pending_preview_path(session_dir).unlink(missing_ok=True)
```

- [ ] **Step 4: Modify `visualize.py` to use cache wrappers**

Replace local `_pending_preview_path`, `_load_pending_preview`, `_save_pending_preview` with compatibility aliases:

```python
from ..preview_pipeline.cache import (
    clear_pending_preview as _clear_pending_preview,
    load_pending_preview as _load_pending_preview,
    pending_preview_path as _pending_preview_path,
    save_pending_preview as _save_pending_preview,
)
```

Update clear sites:

```python
_clear_pending_preview(session_dir)
```

instead of:

```python
_pending_preview_path(session_dir).unlink(missing_ok=True)
```

- [ ] **Step 5: Run resume/cache tests**

```bash
python -m pytest tests/test_preview_pipeline_cache.py tests/test_resume_control.py tests/test_visualize_preview_prompt.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add workflow/preview_pipeline/cache.py workflow/nodes/visualize.py tests/test_preview_pipeline_cache.py tests/test_resume_control.py
git commit -m "refactor: extract preview pending cache"
```

---

## Task 5: Add FAL provider wrapper with nano-banana schema validation

**Files:**
- Create: `workflow/preview_pipeline/providers.py`
- Create/extend: `tests/test_preview_pipeline_validators.py`

- [ ] **Step 1: Write tests for FAL argument schema without network calls**

Create `tests/test_preview_pipeline_validators.py`:

```python
from workflow.preview_pipeline.providers import build_nano_banana_arguments


def test_nano_banana_arguments_use_required_schema():
    args = build_nano_banana_arguments("desktop prompt", aspect_ratio="16:9")

    assert args == {
        "prompt": "desktop prompt",
        "aspect_ratio": "16:9",
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "6",
        "limit_generations": True,
    }

    forbidden = {"guidance_scale", "num_inference_steps", "image_size", "width", "height"}
    assert forbidden.isdisjoint(args)
```

- [ ] **Step 2: Run test to verify failure**

```bash
python -m pytest tests/test_preview_pipeline_validators.py::test_nano_banana_arguments_use_required_schema -q
```

Expected: import failure.

- [ ] **Step 3: Implement provider wrapper**

Create `workflow/preview_pipeline/providers.py`:

```python
from __future__ import annotations

import os
from typing import Any

try:
    import fal_client  # type: ignore
except Exception:  # pragma: no cover - dependency may be absent in unit tests
    fal_client = None

NANO_BANANA_ENDPOINT = "fal-ai/nano-banana"


def build_nano_banana_arguments(prompt: str, aspect_ratio: str) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "num_images": 1,
        "output_format": "png",
        "safety_tolerance": "6",
        "limit_generations": True,
    }


def generate_desktop_concept(prompt: str, aspect_ratio: str, fal_key: str, log) -> str:
    if fal_client is None:
        log.warning("fal_client not installed — image generation unavailable")
        return ""
    os.environ.setdefault("FAL_KEY", fal_key)
    try:
        result = fal_client.subscribe(
            NANO_BANANA_ENDPOINT,
            arguments=build_nano_banana_arguments(prompt, aspect_ratio),
            with_logs=False,
        )
        url = result["images"][0]["url"]
        log.info("FAL image generated: %s", url[:80])
        return url
    except Exception as e:
        log.warning("FAL image generation failed: %s", e)
        return ""
```

- [ ] **Step 4: Modify `visualize.py` `_generate_style_image()` to call provider wrapper**

Change `_generate_style_image()` to keep its public behavior but delegate:

```python
from ..preview_pipeline.providers import generate_desktop_concept


def _generate_style_image(direction: dict, fal_key: str, log, profile: dict | None = None) -> str:
    aspect_ratio = _select_overview_aspect_ratio(profile or {})
    prompt = _build_desktop_preview_prompt(direction, aspect_ratio=aspect_ratio)
    log.info("generating FAL nano-banana image — aspect=%s prompt: %s", aspect_ratio, prompt[:120])
    return generate_desktop_concept(prompt, aspect_ratio, fal_key, log)
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_preview_pipeline_validators.py tests/test_visualize_preview_prompt.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add workflow/preview_pipeline/providers.py workflow/nodes/visualize.py tests/test_preview_pipeline_validators.py
git commit -m "refactor: isolate nano-banana provider wrapper"
```

---

## Task 6: Add deterministic desktop contract validators

**Files:**
- Create: `workflow/preview_pipeline/validators.py`
- Extend: `tests/test_preview_pipeline_validators.py`

- [ ] **Step 1: Write validator tests**

Extend `tests/test_preview_pipeline_validators.py`:

```python
from workflow.preview_pipeline.validators import (
    validate_desktop_prompt_contract,
    validate_visual_context_contract,
)


def test_prompt_contract_rejects_wallpaper_only_prompt():
    errors = validate_desktop_prompt_contract("cinematic landscape, no UI chrome")
    assert any("entire desktop UI" in e or "forbidden" in e for e in errors)


def test_prompt_contract_accepts_full_desktop_prompt():
    prompt = "full Linux desktop theme concept preview, entire desktop UI, screenshot-style mockup, themed terminal window, launcher/menu panel, widget menus, edge-to-edge, no cinematic letterbox bars"
    assert validate_desktop_prompt_contract(prompt) == []


def test_visual_context_contract_requires_reference_and_elements():
    errors = validate_visual_context_contract({"style_description": "dark"})
    assert "missing reference_image_url" in errors
    assert "missing visual_element_plan" in errors


def test_visual_context_contract_accepts_minimal_valid_context():
    ctx = {
        "reference_image_url": "https://example.com/image.png",
        "extracted_palette": {"background": "#000000", "foreground": "#ffffff"},
        "style_description": "dark RPG menu",
        "ui_chrome_guidance": "thin borders, terminal, launcher",
        "visual_element_plan": [{"id": "terminal", "implementation_tool": "terminal:kitty"}],
        "validation_checklist": ["terminal visible"],
    }
    assert validate_visual_context_contract(ctx) == []
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_preview_pipeline_validators.py -q
```

Expected: import failure for validators.

- [ ] **Step 3: Implement validators**

Create `workflow/preview_pipeline/validators.py`:

```python
from __future__ import annotations

REQUIRED_PROMPT_PHRASES = [
    "full linux desktop theme concept preview",
    "entire desktop ui",
    "screenshot-style mockup",
    "themed terminal window",
    "launcher/menu panel",
    "widget menus",
    "edge-to-edge",
    "no cinematic letterbox bars",
]

FORBIDDEN_PROMPT_PHRASES = [
    "no ui chrome",
    "landscape-only",
    "environment only",
    "mood painting only",
]

REQUIRED_VISUAL_CONTEXT_KEYS = [
    "reference_image_url",
    "extracted_palette",
    "style_description",
    "ui_chrome_guidance",
    "visual_element_plan",
    "validation_checklist",
]


def validate_desktop_prompt_contract(prompt: str) -> list[str]:
    text = (prompt or "").lower()
    errors: list[str] = []
    for phrase in REQUIRED_PROMPT_PHRASES:
        if phrase not in text:
            errors.append(f"missing required prompt phrase: {phrase}")
    for phrase in FORBIDDEN_PROMPT_PHRASES:
        if phrase in text:
            errors.append(f"forbidden prompt phrase present: {phrase}")
    return errors


def validate_visual_context_contract(visual_context: dict) -> list[str]:
    ctx = visual_context if isinstance(visual_context, dict) else {}
    errors: list[str] = []
    for key in REQUIRED_VISUAL_CONTEXT_KEYS:
        if key not in ctx:
            errors.append(f"missing {key}")
    if "visual_element_plan" in ctx and not isinstance(ctx.get("visual_element_plan"), list):
        errors.append("visual_element_plan must be a list")
    if "validation_checklist" in ctx and not isinstance(ctx.get("validation_checklist"), list):
        errors.append("validation_checklist must be a list")
    return errors
```

- [ ] **Step 4: Add non-fatal validation calls to `visualize.py`**

Inside `_generate_style_image()` after prompt construction:

```python
from ..preview_pipeline.validators import validate_desktop_prompt_contract

prompt_errors = validate_desktop_prompt_contract(prompt)
if prompt_errors:
    log.warning("desktop preview prompt contract warnings: %s", prompt_errors)
```

Inside `visualize_node()` after `_analyze_image_multimodal()`:

```python
from ..preview_pipeline.validators import validate_visual_context_contract

context_errors = validate_visual_context_contract(visual_context)
if context_errors:
    log.warning("visual context contract warnings: %s", context_errors)
```

Do not hard-fail yet; first land observability.

- [ ] **Step 5: Run validator and visualize tests**

```bash
python -m pytest tests/test_preview_pipeline_validators.py tests/test_visualize_preview_prompt.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add workflow/preview_pipeline/validators.py workflow/nodes/visualize.py tests/test_preview_pipeline_validators.py
git commit -m "feat: validate desktop preview contracts"
```

---

## Task 7: Implement pipeline executor skeleton

**Files:**
- Create: `workflow/preview_pipeline/executor.py`
- Create: `workflow/preview_pipeline/templates.py`
- Extend: `tests/test_preview_pipeline_executor.py`

- [ ] **Step 1: Write executor tests with fake handlers**

Extend `tests/test_preview_pipeline_executor.py`:

```python
from workflow.preview_pipeline.executor import execute_preview_workflow
from workflow.preview_pipeline.templates import build_default_desktop_preview_workflow
from workflow.preview_pipeline.types import PreviewRunOptions


def test_default_template_has_expected_node_order():
    wf = build_default_desktop_preview_workflow()
    assert [node.id for node in wf.nodes] == [
        "prompt",
        "image",
        "analysis",
        "validate",
        "html",
        "cache",
    ]


def test_executor_reuses_cached_preview_without_paid_generation(tmp_path):
    from workflow.preview_pipeline.cache import save_pending_preview

    html_path = tmp_path / "visualize.html"
    html_path.write_text("<html>cached</html>")
    save_pending_preview(
        str(tmp_path),
        "https://example.com/cached.png",
        html_path,
        {"reference_image_url": "https://example.com/cached.png"},
    )

    result = execute_preview_workflow(
        direction={"name": "cached"},
        profile={},
        html_path=html_path,
        options=PreviewRunOptions(session_dir=str(tmp_path), fal_key="", use_cache=True),
        log=None,
        analyze_image=lambda image_url, direction, log: {"reference_image_url": image_url},
        render_html=lambda path, image_url, visual_context, direction, log: path.write_text("<html>new</html>"),
        generate_image=lambda prompt, aspect_ratio, fal_key, log: (_ for _ in ()).throw(AssertionError("should not generate")),
    )

    assert result.image_url == "https://example.com/cached.png"
    assert result.visual_context["reference_image_url"] == "https://example.com/cached.png"
    assert result.budget["num_calls"] == 0
```

- [ ] **Step 2: Run tests to verify failure**

```bash
python -m pytest tests/test_preview_pipeline_executor.py -q
```

Expected: import failure for executor/templates.

- [ ] **Step 3: Implement default template**

Create `workflow/preview_pipeline/templates.py`:

```python
from __future__ import annotations

from .types import PreviewEdge, PreviewNode, PreviewNodeType, PreviewWorkflow


def build_default_desktop_preview_workflow() -> PreviewWorkflow:
    return PreviewWorkflow(
        id="desktop-preview-default",
        name="Desktop Preview Default",
        nodes=[
            PreviewNode("prompt", PreviewNodeType.DESKTOP_PROMPT, {}),
            PreviewNode("image", PreviewNodeType.FAL_DESKTOP_CONCEPT, {"prompt": "{{prompt.prompt}}"}),
            PreviewNode("analysis", PreviewNodeType.MULTIMODAL_ANALYSIS, {"image_url": "{{image.image_url}}"}),
            PreviewNode("validate", PreviewNodeType.CONTRACT_VALIDATE, {"visual_context": "{{analysis.visual_context}}"}),
            PreviewNode("html", PreviewNodeType.STYLE_HTML_RENDER, {"visual_context": "{{analysis.visual_context}}"}),
            PreviewNode("cache", PreviewNodeType.CACHE_ARTIFACTS, {"image_url": "{{image.image_url}}"}),
        ],
        edges=[
            PreviewEdge("prompt", "image"),
            PreviewEdge("image", "analysis"),
            PreviewEdge("analysis", "validate"),
            PreviewEdge("validate", "html"),
            PreviewEdge("html", "cache"),
        ],
    )
```

- [ ] **Step 4: Implement minimal executor with cache fast-path**

Create `workflow/preview_pipeline/executor.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Callable

from .budget import PreviewBudgetGate, PreviewBudgetExceeded
from .cache import load_pending_preview, save_pending_preview
from .prompts import build_desktop_preview_prompt, select_overview_aspect_ratio
from .types import PreviewEvent, PreviewRunOptions, PreviewRunResult
from .validators import validate_desktop_prompt_contract, validate_visual_context_contract


def _null_log():
    class Log:
        def info(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
    return Log()


def execute_preview_workflow(
    *,
    direction: dict,
    profile: dict,
    html_path: Path,
    options: PreviewRunOptions,
    log,
    analyze_image: Callable,
    render_html: Callable,
    generate_image: Callable,
) -> PreviewRunResult:
    log = log or _null_log()
    events: list[PreviewEvent] = []
    gate = PreviewBudgetGate(max_budget=options.budget_limit or 0.08)

    cached = load_pending_preview(options.session_dir) if options.use_cache and not options.regenerate else {}
    if cached.get("image_url"):
        visual_context = dict(cached.get("visual_context") or {})
        return PreviewRunResult(
            image_url=cached["image_url"],
            html_path=cached.get("html_path", str(html_path)),
            visual_context=visual_context,
            events=[PreviewEvent("cache", "cache_hit", {"image_url": cached["image_url"]})],
            budget=gate.summary(),
        )

    aspect_ratio = select_overview_aspect_ratio(profile)
    prompt = build_desktop_preview_prompt(direction, aspect_ratio=aspect_ratio)
    prompt_errors = validate_desktop_prompt_contract(prompt)
    if prompt_errors:
        log.warning("desktop preview prompt contract warnings: %s", prompt_errors)
    events.append(PreviewEvent("prompt", "node_complete", {"aspect_ratio": aspect_ratio, "errors": prompt_errors}))

    if not options.allow_paid_generation:
        return PreviewRunResult(status="error", error="paid generation disabled", events=events, budget=gate.summary())

    try:
        gate.record_model("fal-ai/nano-banana", detail="desktop-preview")
    except PreviewBudgetExceeded as e:
        return PreviewRunResult(status="error", error=str(e), events=events, budget=gate.summary())

    image_url = generate_image(prompt, aspect_ratio, options.fal_key, log)
    events.append(PreviewEvent("image", "node_complete" if image_url else "node_error", {"image_url": image_url}))
    if not image_url:
        return PreviewRunResult(status="error", error="image generation failed", events=events, budget=gate.summary())

    visual_context = analyze_image(image_url, direction, log)
    visual_context["reference_image_url"] = image_url
    context_errors = validate_visual_context_contract(visual_context)
    if context_errors:
        log.warning("visual context contract warnings: %s", context_errors)
    events.append(PreviewEvent("analysis", "node_complete", {"errors": context_errors}))

    if not html_path.exists() or html_path.stat().st_size < 200:
        render_html(html_path, image_url, visual_context, direction, log)
    events.append(PreviewEvent("html", "node_complete", {"html_path": str(html_path)}))

    save_pending_preview(options.session_dir, image_url, html_path, visual_context)
    events.append(PreviewEvent("cache", "node_complete", {"session_dir": options.session_dir}))

    return PreviewRunResult(
        image_url=image_url,
        html_path=str(html_path),
        visual_context=visual_context,
        events=events,
        budget=gate.summary(),
    )
```

- [ ] **Step 5: Run executor tests**

```bash
python -m pytest tests/test_preview_pipeline_executor.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add workflow/preview_pipeline/executor.py workflow/preview_pipeline/templates.py tests/test_preview_pipeline_executor.py
git commit -m "feat: add desktop preview pipeline executor"
```

---

## Task 8: Integrate executor into `visualize_node()`

**Files:**
- Modify: `workflow/nodes/visualize.py`
- Modify: `workflow/state.py`
- Extend: `tests/test_visualize_preview_prompt.py`
- Extend: `tests/test_resume_control.py`

- [ ] **Step 1: Add state fields**

Modify `workflow/state.py`:

```python
    # Step 2.5 pipeline diagnostics — non-authoritative metadata for debugging/cost control.
    preview_pipeline_status: dict
    preview_budget: dict
```

Place after existing Step 2.5 fields.

- [ ] **Step 2: Replace internals in `visualize_node()` with executor call**

In `workflow/nodes/visualize.py`, import:

```python
from ..preview_pipeline.executor import execute_preview_workflow
from ..preview_pipeline.providers import generate_desktop_concept
from ..preview_pipeline.types import PreviewRunOptions
```

Replace the block that loads cache, generates image, analyzes, renders HTML, and saves pending preview with:

```python
    html_path = _get_html_path(session_dir)
    result = execute_preview_workflow(
        direction=direction,
        profile=state.get("device_profile", {}),
        html_path=html_path,
        options=PreviewRunOptions(
            session_dir=session_dir,
            fal_key=fal_key,
            use_cache=True,
            budget_limit=0.08,
            allow_paid_generation=True,
            regenerate=False,
        ),
        log=log,
        analyze_image=_analyze_image_multimodal,
        render_html=_render_style_html,
        generate_image=generate_desktop_concept,
    )

    image_url = result.image_url
    visual_context = result.visual_context
```

Keep existing failure interrupt semantics:

```python
    if not image_url:
        log.warning("FAL image generation failed — skipping AI desktop preview")
        msg = "⚠  Image generation failed. Proceeding without AI desktop preview.\nCheck your FAL_KEY and account credits."
        user_reply = interrupt({"step": "2.5", "type": "conversation", "message": msg})
        return {
            "messages": [AIMessage(content=msg), HumanMessage(content=str(user_reply))],
            "visual_context": {},
            "visualize_route": "skip",
            "loop_counts": loop_counts,
            "preview_pipeline_status": {"status": result.status, "error": result.error},
            "preview_budget": result.budget,
        }
```

On approve, include diagnostics:

```python
        return {
            "visualize_image_url": image_url,
            "visualize_html_path": str(html_path),
            "visual_context": visual_context,
            "visualize_route": "approve",
            "current_step": 3,
            "loop_counts": loop_counts,
            "preview_pipeline_status": {"status": result.status, "events": [e.__dict__ for e in result.events]},
            "preview_budget": result.budget,
        }
```

- [ ] **Step 3: Preserve regenerate/back cache clear behavior**

When decision is `back` or freeform regenerate, call:

```python
_clear_pending_preview(session_dir)
```

and keep existing route values:
- `visualize_route: "explore"`
- `visualize_route: "regenerate"`

- [ ] **Step 4: Run focused tests**

```bash
python -m pytest tests/test_visualize_preview_prompt.py tests/test_resume_control.py tests/test_preview_pipeline_executor.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add workflow/nodes/visualize.py workflow/state.py tests/test_visualize_preview_prompt.py tests/test_resume_control.py
git commit -m "refactor: route visualize through preview pipeline executor"
```

---

## Task 9: Add controlled variant pipeline design without enabling by default

**Files:**
- Modify: `workflow/preview_pipeline/templates.py`
- Modify: `workflow/preview_pipeline/types.py`
- Test: `tests/test_preview_pipeline_executor.py`
- Docs: `references/desktop-preview-generation.md`

- [ ] **Step 1: Add tests for variant template only**

Extend `tests/test_preview_pipeline_executor.py`:

```python
from workflow.preview_pipeline.templates import build_variant_desktop_preview_workflow


def test_variant_template_is_opt_in_and_has_three_paid_image_nodes():
    wf = build_variant_desktop_preview_workflow(variant_count=3)
    image_nodes = [node for node in wf.nodes if node.type.value == "fal_desktop_concept"]

    assert len(image_nodes) == 3
    assert [node.id for node in image_nodes] == ["image_1", "image_2", "image_3"]
```

- [ ] **Step 2: Implement template builder**

Add to `workflow/preview_pipeline/templates.py`:

```python
def build_variant_desktop_preview_workflow(variant_count: int = 3) -> PreviewWorkflow:
    count = max(1, min(variant_count, 4))
    nodes = [PreviewNode("prompt", PreviewNodeType.DESKTOP_PROMPT, {})]
    edges = []
    for idx in range(1, count + 1):
        image_id = f"image_{idx}"
        nodes.append(PreviewNode(image_id, PreviewNodeType.FAL_DESKTOP_CONCEPT, {
            "prompt": f"{{{{prompt.prompt}}}}\nVariant {idx}: preserve the same theme, vary composition and UI emphasis.",
        }))
        edges.append(PreviewEdge("prompt", image_id))
    return PreviewWorkflow(
        id="desktop-preview-variants",
        name="Desktop Preview Variants",
        nodes=nodes,
        edges=edges,
    )
```

- [ ] **Step 3: Document disabled-by-default policy**

Update `references/desktop-preview-generation.md` with:

```markdown
## Variant generation policy

Variant generation is supported only as an explicit opt-in pipeline. The default Step 2.5 flow runs one paid `fal-ai/nano-banana` hero generation. A variant pipeline may create 2-4 paid concept images, but must show/record a budget estimate first and must not run because of ambiguous approval text such as "looks good, but...".
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_preview_pipeline_executor.py tests/test_preview_pipeline_budget.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add workflow/preview_pipeline/templates.py references/desktop-preview-generation.md tests/test_preview_pipeline_executor.py
git commit -m "feat: define opt-in desktop preview variants"
```

---

## Task 10: Add status/history artifact logging

**Files:**
- Modify: `workflow/preview_pipeline/cache.py`
- Modify: `workflow/preview_pipeline/executor.py`
- Test: `tests/test_preview_pipeline_cache.py`

- [ ] **Step 1: Write history test**

Extend `tests/test_preview_pipeline_cache.py`:

```python
from workflow.preview_pipeline.cache import append_preview_history, load_preview_history


def test_preview_history_appends_jsonl(tmp_path):
    append_preview_history(str(tmp_path), {"status": "success", "image_url": "url-1"})
    append_preview_history(str(tmp_path), {"status": "error", "error": "boom"})

    history = load_preview_history(str(tmp_path))
    assert history == [
        {"status": "success", "image_url": "url-1"},
        {"status": "error", "error": "boom"},
    ]
```

- [ ] **Step 2: Implement history helpers**

Add to `workflow/preview_pipeline/cache.py`:

```python
def preview_history_path(session_dir: str) -> Path:
    return Path(session_dir).expanduser() / "preview_pipeline.history.jsonl"


def append_preview_history(session_dir: str, entry: dict) -> None:
    path = preview_history_path(session_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_preview_history(session_dir: str) -> list[dict]:
    path = preview_history_path(session_dir)
    rows: list[dict] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    except Exception:
        return []
    return rows
```

- [ ] **Step 3: Append history at executor finish**

In `execute_preview_workflow()`, before each return, append a compact entry:

```python
from .cache import append_preview_history

append_preview_history(options.session_dir, {
    "status": result.status,
    "image_url": result.image_url,
    "html_path": result.html_path,
    "budget": result.budget,
    "error": result.error,
})
```

Implement with a small local `_finish(result)` helper to avoid duplicating returns.

- [ ] **Step 4: Run cache/executor tests**

```bash
python -m pytest tests/test_preview_pipeline_cache.py tests/test_preview_pipeline_executor.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add workflow/preview_pipeline/cache.py workflow/preview_pipeline/executor.py tests/test_preview_pipeline_cache.py
git commit -m "feat: persist desktop preview pipeline history"
```

---

## Task 11: Full regression and docs update

**Files:**
- Modify: `references/desktop-preview-generation.md`
- Modify if needed: `references/hermesfy-studio-preview-pipeline-research.md`

- [ ] **Step 1: Update docs with architecture summary**

Add to `references/desktop-preview-generation.md`:

```markdown
## Internal DesktopPreviewPipeline

Step 2.5 uses `workflow/preview_pipeline/` for the paid AI preview flow:

- `prompts.py` owns desktop-overview prompt invariants and LLM prompt text.
- `providers.py` owns the `fal-ai/nano-banana` call schema.
- `budget.py` records paid generation estimates and blocks over-budget flows.
- `cache.py` owns `visualize.pending.json` and `preview_pipeline.history.jsonl`.
- `validators.py` owns deterministic prompt/context contract checks.
- `executor.py` coordinates the pipeline and returns `PreviewRunResult`.

`workflow/nodes/visualize.py` remains the LangGraph approval gate. It must not reimplement pipeline internals.
```

- [ ] **Step 2: Run focused preview tests**

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python -m pytest tests/test_preview_pipeline_budget.py tests/test_preview_pipeline_cache.py tests/test_preview_pipeline_executor.py tests/test_preview_pipeline_validators.py -q
python -m pytest tests/test_visualize_preview_prompt.py tests/test_refine_prompt_handoff.py tests/test_preview_renderer.py tests/test_resume_control.py -q
```

Expected: all PASS.

- [ ] **Step 3: Run broader workflow tests if fast enough**

```bash
python -m pytest tests/test_refine_prompt_handoff.py tests/test_preview_renderer.py tests/test_resume_control.py tests/test_visualize_preview_prompt.py tests/test_kde_materializers.py -q
```

Expected: all PASS or existing unrelated failures documented verbatim.

- [ ] **Step 4: Commit**

```bash
git add references/desktop-preview-generation.md references/hermesfy-studio-preview-pipeline-research.md
if git diff --cached --quiet; then echo "No doc changes to commit"; else git commit -m "docs: document desktop preview pipeline"; fi
```

---

## Risks and tradeoffs

1. **Over-engineering risk**
   - Mitigation: first pipeline is a thin extraction around existing behavior. Do not add generic Hermesfy plugin compatibility until the desktop-specific path is stable.

2. **Paid generation accidental reruns**
   - Mitigation: cache fast-path lands before full executor integration. Regenerate/back must explicitly clear cache.

3. **Budget estimates may be wrong**
   - Mitigation: label as estimates in status/history. Use the budget gate for safety bounds, not accounting precision.

4. **Validation too strict**
   - Mitigation: deterministic validators log warnings first. Hard-fail only after observing real sessions.

5. **State migration issues**
   - Mitigation: add only optional `TypedDict total=False` fields. Keep existing state field names unchanged.

6. **HTML preview regression**
   - Mitigation: keep existing `_render_style_html()` and `plan.py` behavior initially; pipeline only orchestrates it.

---

## Open questions

1. Should variant generation be exposed as a user command in the workflow UI immediately, or stay as internal API until after one stable session?
   - Recommendation: keep internal only for first implementation.

2. Should budget gate count LLM vision calls?
   - Recommendation: record them as zero-cost metadata initially because the major risk is FAL spend. Add model-aware LLM accounting later only if useful.

3. Should invalid visual context hard-fail Step 2.5?
   - Recommendation: no at first. Log warnings and surface in `preview_pipeline_status`; hard-fail after we know false-positive rate.

4. Should Hermesfy Studio be added as a git submodule/dependency?
   - Recommendation: no. Borrow architecture internally. Avoid dependency churn and product-photo bias.

---

## Verification checklist before claiming complete

- [ ] `workflow/nodes/visualize.py` still uses `fal-ai/nano-banana` via provider wrapper.
- [ ] No Flux parameters appear in nano-banana calls: no `guidance_scale`, `num_inference_steps`, `image_size`.
- [ ] `visualize.pending.json` is still written before the approval interrupt.
- [ ] Read-only status checks with pending interrupts do not trigger another generation.
- [ ] `visual_context.reference_image_url` reaches `plan.py` and `refine.py` unchanged.
- [ ] `plan.html` still frames the approved hero image instead of inventing a generic dashboard.
- [ ] Default flow performs at most one paid image generation.
- [ ] Freeform feedback/regenerate clears cache deliberately.
- [ ] `approve` preserves the exact cached target.
- [ ] Focused tests pass.

---

## Suggested execution strategy

Use subagent-driven development with one task per subagent, in order. After each task:

```bash
git diff --stat
git diff -- workflow/preview_pipeline workflow/nodes/visualize.py workflow/state.py tests references/desktop-preview-generation.md
python -m pytest <task-specific-tests> -q
```

Only proceed to the next task after reviewing the diff and test output.
