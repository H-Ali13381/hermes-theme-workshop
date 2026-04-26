"""implement/spec.py — LLM spec generation for one theming element."""
from __future__ import annotations

import json
import re

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from ...config import MODEL

_SYSTEM = """\
You are writing an implementation spec for one desktop theming element.
Given the element name and the design_system JSON, produce a concise spec:

targets: list of config file paths that will be written
palette_keys: which design.palette slots are used
font: family and size (if applicable, else "N/A")
radii: border radius in px (if applicable, else "N/A")
notes: any non-obvious detail (e.g. "requires daemon restart")

Output ONLY a JSON object, no explanation.
Example:
{
  "targets": ["~/.config/kitty/theme.conf"],
  "palette_keys": ["background","foreground","primary","accent"],
  "font": "FiraCode Nerd Font 12",
  "radii": "8",
  "notes": "Requires kitty reload (ctrl+shift+F5)"
}
"""


def write_spec(element: str, design: dict) -> dict:
    """Ask the LLM for a structured implementation spec for this element."""
    try:
        llm = ChatAnthropic(model=MODEL, temperature=0)
        resp = llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=f"Element: {element}\nDesign:\n{json.dumps(design, indent=2)}"),
        ])
        text = resp.content.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text.strip())
        return json.loads(text)
    except Exception as e:
        return {"targets": [], "palette_keys": [], "font": "N/A", "radii": "N/A", "notes": str(e)}
