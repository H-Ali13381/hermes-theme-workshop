"""implement/spec.py — LLM spec generation for one theming element."""
from __future__ import annotations

import json

from ...config import get_llm

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:  # LangGraph not installed (e.g. during unit tests)
    class HumanMessage:  # type: ignore[no-redef]
        def __init__(self, content: str) -> None:
            self.content = content

    class SystemMessage:  # type: ignore[no-redef]
        def __init__(self, content: str) -> None:
            self.content = content

try:
    from pydantic import BaseModel, Field

    class ElementSpec(BaseModel):
        """Structured implementation spec for one desktop theming element."""

        targets: list[str] = Field(default_factory=list, description="Config file paths that will be written")
        palette_keys: list[str] = Field(default_factory=list, description="design.palette slots used by this element")
        font: str = Field(default="N/A", description="Font family and size, or N/A")
        radii: str = Field(default="N/A", description="Border radius in px, or N/A")
        notes: str = Field(default="", description="Non-obvious implementation or reload details")

except ImportError:  # pydantic not installed — lightweight dataclass stand-in
    import dataclasses as _dc

    @_dc.dataclass
    class ElementSpec:  # type: ignore[no-redef]
        """Structured implementation spec for one desktop theming element (dataclass fallback)."""

        targets: list = _dc.field(default_factory=list)
        palette_keys: list = _dc.field(default_factory=list)
        font: str = "N/A"
        radii: str = "N/A"
        notes: str = ""

        def model_dump(self) -> dict:
            return _dc.asdict(self)

        @classmethod
        def model_validate(cls, data: object) -> "ElementSpec":
            if isinstance(data, dict):
                valid = {f.name for f in _dc.fields(cls)}
                return cls(**{k: v for k, v in data.items() if k in valid})
            return data  # type: ignore[return-value]


_SYSTEM = """\
You are writing an implementation spec for one desktop theming element.
Given the element name and the design_system JSON, produce a concise spec.

Fields:
- targets: list of config file paths that will be written
- palette_keys: which design.palette slots are used
- font: family and size (if applicable, else "N/A")
- radii: border radius in px (if applicable, else "N/A")
- notes: any non-obvious detail (e.g. "requires daemon restart")

For element "widgets:eww", targets must include ~/.config/eww/hermes-palette.scss
and ~/.config/eww/hermes-theme.yuck, and notes should mention the generated EWW
overlay/frame windows. EWW is used when the user vision or chrome_strategy calls for
custom widgets, terminal frames, or borders; it is not mandatory decoration.
"""


def write_spec(element: str, design: dict) -> dict:
    """Ask the LLM for a structured implementation spec for this element."""
    try:
        llm = get_llm(0.0)
        structured_llm = llm.with_structured_output(ElementSpec)
        spec = structured_llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=f"Element: {element}\nDesign:\n{json.dumps(design, indent=2)}"),
        ])
        if isinstance(spec, ElementSpec):
            return spec.model_dump()
        return ElementSpec.model_validate(spec).model_dump()
    except Exception as e:
        return {"targets": [], "palette_keys": [], "font": "N/A", "radii": "N/A", "notes": str(e)}
