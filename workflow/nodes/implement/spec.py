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

For element "window_decorations:kde", the current materializer writes KDE color
scheme and KWin/Breeze decoration settings only: ~/.config/kwinrc, ~/.config/kdeglobals,
and ~/.local/share/color-schemes/hermes-<design-name>.colors. Do NOT target
~/.local/share/aurorae/themes/* or claim an Aurorae package unless a dedicated Aurorae
materializer has been implemented.

For element "lock_screen:kde", the current materializer writes only
~/.config/kscreenlockerrc. It sets the greeter theme to Breeze/BreezeDark based on the
palette and may set a wallpaper image/fill mode when the design has a resolvable
wallpaper. It does NOT generate a custom Plasma look-and-feel package, does NOT write
~/.local/share/plasma/look-and-feel/*/contents/lockscreen/*, and does NOT write palette
hex colors directly into kscreenlockerrc. Therefore targets must be ["~/.config/kscreenlockerrc"],
palette_keys must be [], and notes should honestly describe the supported BreezeDark +
wallpaper lock-screen styling rather than claiming custom parchment prompt QML.
"""


def write_spec(element: str, design: dict) -> dict:
    """Ask the LLM for an implementation spec for this element.

    Prefer LangChain structured output when the provider supports it. Hermes'
    OpenAI Codex OAuth shim is intentionally lightweight and only provides
    invoke(), so fall back to a plain JSON prompt before returning a safe empty
    spec.
    """
    errors: list[str] = []
    llm = None
    try:
        llm = get_llm(0.0)
        structured_llm = llm.with_structured_output(ElementSpec)
        spec = structured_llm.invoke(_messages(element, design, structured=True))
        return _coerce_spec(spec)
    except (AttributeError, NotImplementedError) as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(str(e))

    try:
        if llm is None:
            llm = get_llm(0.0)
        response = llm.invoke(_messages(element, design, structured=False))
        return _coerce_spec(_extract_json(getattr(response, "content", response)))
    except Exception as e:
        errors.append(str(e))
        return {
            "targets": [],
            "palette_keys": [],
            "font": "N/A",
            "radii": "N/A",
            "notes": "; ".join(error for error in errors if error),
        }


def _messages(element: str, design: dict, *, structured: bool) -> list:
    if structured:
        system = _SYSTEM
    else:
        system = _SYSTEM + """

Return ONLY JSON with this exact object shape, no markdown and no explanation:
{
  "targets": ["~/.config/example.conf"],
  "palette_keys": ["background", "foreground"],
  "font": "Font Name 12 or N/A",
  "radii": "8px or N/A",
  "notes": "concise implementation/reload notes"
}
"""
    return [
        SystemMessage(content=system),
        HumanMessage(content=f"Element: {element}\nDesign:\n{json.dumps(design, indent=2)}"),
    ]


def _coerce_spec(spec: object) -> dict:
    if isinstance(spec, ElementSpec):
        return spec.model_dump()
    return ElementSpec.model_validate(spec).model_dump()


def _extract_json(content: object) -> dict:
    text = str(content).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start:end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("spec response JSON was not an object")
    return parsed
