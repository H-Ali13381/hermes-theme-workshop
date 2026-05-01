"""craft/codegen.py — LLM-driven code generation for advanced desktop elements.

The LLM is given: framework syntax reference, design system context (palette,
mood, strategies), and any existing system configs found during research.  It
returns a JSON array of {path, content} objects — complete, write-ready files.

The agent is explicitly told to be original: no templates, no placeholders,
no generic configs.  Every file must reflect the design palette and intent.
"""
from __future__ import annotations

import json
import re
import sys

from ...config import get_llm


_SYSTEM = """\
You are an elite Linux desktop customization engineer.
Your job is to write COMPLETE, ORIGINAL configuration files for a specific widget/bar framework.

RULES:
1. Every file must be fully working — no placeholders, no TODOs, no template variables.
2. Every color must come from the supplied palette. Never use hardcoded generic colors.
3. Be CREATIVE and SPECIFIC to the design theme. Not generic, not boilerplate.
4. Respect the framework syntax exactly — malformed configs waste the user's time.
5. Return ONLY a JSON array. Each item: {"path": "<relative path inside config dir>", "content": "<full file content>"}.
6. Write every key file the framework needs to run (e.g. eww.yuck + eww.scss for EWW).
7. Do not abbreviate. Write the entire file content in each "content" field.
"""


def _build_prompt(element: str, research: dict) -> str:
    syntax  = research.get("syntax", {})
    system  = research.get("system", {})
    di      = research.get("design_intent", {})

    palette_lines = "\n".join(f"  {k}: {v}" for k, v in di.get("palette", {}).items())

    existing_block = ""
    existing = system.get("existing_files", {})
    if existing:
        parts = []
        for fname, content in list(existing.items())[:4]:   # cap to 4 files to avoid token overload
            parts.append(f"--- {fname} ---\n{content[:800]}")
        existing_block = "\n\nEXISTING SYSTEM CONFIGS (for reference, do NOT copy verbatim):\n" + "\n".join(parts)

    strat_lines = ""
    for key in ("originality_strategy", "chrome_strategy", "panel_layout"):
        val = di.get(key)
        if val:
            strat_lines += f"\n{key}: {json.dumps(val, indent=2)}"

    return f"""Generate configuration files for element: {element}

FRAMEWORK: {syntax.get('framework_name', element)}
CONFIG DIR: {syntax.get('config_dir', 'unknown')}
KEY FILES NEEDED: {', '.join(syntax.get('key_files', []))}

FRAMEWORK SYNTAX REFERENCE:
{syntax.get('syntax_hint', '')}

IDIOMATIC EXAMPLE (study the patterns, do NOT copy):
{syntax.get('example', '')}

DESIGN SYSTEM:
  Theme name: {di.get('theme_name', 'unnamed')}
  Description: {di.get('description', '')}
  Mood tags: {', '.join(di.get('mood_tags', []))}

PALETTE (use ALL of these colors, distributed meaningfully):
{palette_lines}
{strat_lines}{existing_block}

OUTPUT: JSON array of file objects. Example shape:
[
  {{"path": "eww.yuck", "content": "(defwidget ...)\\n(defwindow ...)"}},
  {{"path": "eww.scss", "content": "* {{ font-family: ... }}"}}
]

Write creative, complete, palette-accurate, theme-consistent configs now:"""


def _parse_file_objects(raw: str) -> list[dict]:
    """Extract the JSON array from an LLM response that may have prose around it."""
    # Try the full response first
    try:
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return [f for f in data if isinstance(f, dict) and "path" in f and "content" in f]
    except json.JSONDecodeError:
        pass

    # Fall back to first [...] block
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return [f for f in data if isinstance(f, dict) and "path" in f and "content" in f]
        except json.JSONDecodeError:
            pass

    print("[craft/codegen] Could not parse LLM response as file objects", file=sys.stderr)
    return []


def generate_files(element: str, design: dict, research: dict) -> list[dict]:
    """Call the LLM and return a list of {path, content} dicts.

    Each dict represents one file to write into the framework's config dir.
    Returns an empty list on failure so the craft node can gate gracefully.
    """
    prompt = _build_prompt(element, research)
    try:
        llm = get_llm(temperature=0.85, max_tokens=8192)
        from langchain_core.messages import HumanMessage, SystemMessage  # noqa: PLC0415
        response = llm.invoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
        raw = response.content if hasattr(response, "content") else str(response)
        return _parse_file_objects(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"[craft/codegen] LLM call failed: {exc}", file=sys.stderr)
        return []
