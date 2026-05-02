"""craft/research.py — Parallel research subagents for the craft pipeline.

Three independent threads gather information before codegen:
  1. system  — scan the user's existing framework config dir
  2. syntax  — pull the framework reference from the knowledge base
  3. design  — extract what the design system needs from this element

Results are merged into a single research dict passed to codegen.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ...logging import get_logger
from .frameworks import get_reference, config_dir


# Maximum bytes to read from any single existing config file (avoid flooding LLM context).
_MAX_FILE_BYTES = 4096


def _scan_system(framework: str) -> dict:
    """Read files already present in the framework's config directory."""
    cd = config_dir(framework)
    findings: dict[str, str] = {}
    if cd is None or not cd.exists():
        return {"existing_files": {}, "note": f"No existing {framework} config dir found."}

    for fp in cd.iterdir():
        if fp.is_file() and fp.suffix in {".yuck", ".scss", ".css", ".json", ".jsonc", ".lua", ".conf", ".qml", ".ts", ".js"}:
            try:
                raw = fp.read_bytes()[:_MAX_FILE_BYTES]
                findings[fp.name] = raw.decode("utf-8", errors="replace")
            except OSError:
                pass

    return {"existing_files": findings, "config_dir": str(cd)}


def _read_syntax(framework: str) -> dict:
    """Pull syntax hints, inline example, and reference templates from the KB."""
    ref = get_reference(framework)
    return {
        "framework_name":      ref.get("name", framework),
        "syntax_hint":         ref.get("syntax_hint", ""),
        "example":             ref.get("example", ""),
        "key_files":           ref.get("key_files", []),
        "config_dir":          ref.get("config_dir", ""),
        "reference_templates": ref.get("reference_templates", []),
    }


def _summarize_design(element: str, design: dict) -> dict:
    """Extract design intent fields relevant to this element."""
    palette   = design.get("palette", {})
    mood_tags = design.get("mood_tags", [])
    desc      = design.get("description", "")
    name      = design.get("name", "unnamed")

    # Pull specialised fields when present
    extra: dict = {}
    for key in ("originality_strategy", "chrome_strategy", "panel_layout", "widget_layout"):
        val = design.get(key)
        if val:
            extra[key] = val

    return {
        "element":   element,
        "theme_name": name,
        "description": desc,
        "mood_tags":  mood_tags,
        "palette":    palette,
        **extra,
    }


def gather_research(element: str, design: dict) -> dict:
    """Run three subagent threads concurrently and merge their findings.

    Returns a dict with keys: system, syntax, design_intent.
    Errors from individual threads are caught and logged — a failed subagent
    should not abort the whole craft pipeline.
    """
    framework = element.split(":", 1)[1] if ":" in element else element

    tasks = {
        "system":       (_scan_system,     framework),
        "syntax":       (_read_syntax,     framework),
        "design_intent": (_summarize_design, element, design),
    }

    results: dict = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(fn, *args): label
            for label, (fn, *args) in tasks.items()
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                results[label] = future.result()
            except Exception as exc:  # noqa: BLE001
                get_logger("craft.research").warning("%s subagent failed: %s", label, exc)
                results[label] = {"error": str(exc)}

    return results
