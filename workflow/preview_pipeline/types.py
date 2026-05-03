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
