"""craft/codegen.py — LLM-driven code generation for advanced desktop elements.

The LLM is given: framework syntax reference, design system context (palette,
mood, strategies), and any existing system configs found during research.  It
returns a list of {path, content} objects — complete, write-ready files.

The agent is explicitly told to be original: no templates, no placeholders,
no generic configs.  Every file must reflect the design palette and intent.

Robustness pattern (generate → evaluate → retry-with-feedback):
  1. Primary path: ``with_structured_output(GeneratedFiles)`` enforces JSON
     shape at the provider layer (function calling / native JSON mode).
  2. Fallback path: plain ``invoke`` + ``_parse_file_objects`` text regex,
     used only when structured output raises (provider/model lacks support).
  3. Each attempt's output runs through ``evaluate_files`` — a deterministic
     check for required files, palette usage, path safety, content size.
  4. On rejection, the next attempt receives the specific failure reasons
     so it can correct rather than blindly re-roll.

The outer ``craft_node`` retry (MAX_IMPLEMENT_RETRIES) remains as a safety net
for transient API errors; the inner loop here typically converges in ≤2 tries.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ...config import get_llm
from .texture_assets import (
    declared_asset_paths,
    extract_texture_intent,
    generate_texture_bundle,
    needs_texture_assets,
    referenced_borderimage_sources,
    validate_texture_bundle,
)
from ...log_setup import get_logger

try:
    from pydantic import BaseModel, Field

    class GeneratedFile(BaseModel):
        """One config file the LLM has produced."""

        path: str = Field(description="Relative path inside the framework's config dir")
        content: str = Field(description="Full file content; never abbreviated or templated")

    class GeneratedFiles(BaseModel):
        """Container schema for ``with_structured_output`` — providers handle
        a top-level object with a list field more reliably than a raw array."""

        files: list[GeneratedFile] = Field(default_factory=list)

    _PYDANTIC_AVAILABLE = True
except ImportError:  # pydantic not installed — disable structured-output path
    GeneratedFile = GeneratedFiles = None  # type: ignore[assignment,misc]
    _PYDANTIC_AVAILABLE = False

# Maximum LLM attempts inside ``generate_files`` before bubbling up an empty
# list to ``craft_node`` (which has its own MAX_IMPLEMENT_RETRIES safety net).
MAX_CODEGEN_ATTEMPTS = 2


_SYSTEM = """\
You are an elite Linux desktop customization engineer.
Your job is to write COMPLETE, ORIGINAL configuration files for a specific widget/bar framework.

RULES:
1. Every file must be fully working — no placeholders, no TODOs, no template variables.
2. Every color must come from the supplied palette. Never use hardcoded generic colors.
3. Be CREATIVE and SPECIFIC to the design theme. Not generic, not boilerplate.
4. Respect the framework syntax exactly — malformed configs waste the user's time.
5. Return a list of file objects, each with "path" (relative) and "content" (full file).
6. Write every key file the framework needs to run (e.g. eww.yuck + eww.scss for EWW).
7. Do not abbreviate. Write the entire file content in each "content" field.
"""


def _build_prompt(element: str, research: dict) -> str:
    syntax  = research.get("syntax", {})
    system  = research.get("system", {})
    di      = research.get("design_intent", {})
    profile = research.get("device_profile", {}) if isinstance(research, dict) else {}

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

    refs_block = _format_reference_templates(syntax.get("reference_templates", []))
    docs_block = _format_reference_docs(syntax.get("reference_docs", []))
    texture_block = _format_texture_assets(research.get("texture_assets"))

    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "unknown")
    session_type = str(profile.get("session_type") or "unknown")
    desktop_context = (
        f"DESKTOP CONTEXT:\n  WM/session: {wm} / {session_type}\n"
        "  Only use compositor/window-manager-specific commands when they match this context.\n"
        "  Do NOT use hyprctl unless the audited WM is Hyprland. On KDE/Plasma, prefer "
        "desktop-neutral widgets, qdbus/kdotool/wmctrl fallbacks, or static-safe launchers."
    )

    return f"""Generate configuration files for element: {element}

FRAMEWORK: {syntax.get('framework_name', element)}
CONFIG DIR: {syntax.get('config_dir', 'unknown')}
KEY FILES NEEDED: {', '.join(syntax.get('key_files', []))}

{desktop_context}

FRAMEWORK SYNTAX REFERENCE:
{syntax.get('syntax_hint', '')}

IDIOMATIC EXAMPLE (study the patterns, do NOT copy):
{syntax.get('example', '')}
{refs_block}{docs_block}
DESIGN SYSTEM:
  Theme name: {di.get('theme_name', 'unnamed')}
  Description: {di.get('description', '')}
  Mood tags: {', '.join(di.get('mood_tags', []))}

PALETTE (use ALL of these colors, distributed meaningfully):
{palette_lines}
{strat_lines}{texture_block}{existing_block}

OUTPUT: JSON array of file objects. Example shape:
[
  {{"path": "eww.yuck", "content": "(defwidget ...)\\n(defwindow ...)"}},
  {{"path": "eww.scss", "content": "* {{ font-family: ... }}"}}
]

Write creative, complete, palette-accurate, theme-consistent configs now:"""


def _format_texture_assets(texture_assets: dict | None) -> str:
    """Render generated texture bundle metadata as a prompt contract."""

    if not isinstance(texture_assets, dict) or not texture_assets.get("assets"):
        return ""
    return (
        "\n\nGENERATED ORNATE TEXTURE ASSETS (must be used exactly; do not invent paths):\n"
        f"{json.dumps(texture_assets, indent=2, sort_keys=True)}\n"
        "QML requirement: for ornate panels/buttons/slots, use BorderImage.source set to one of "
        "the asset paths above, border.* set to that asset's slice_px, and BorderImage.Repeat "
        "for tiled edge segments. Plain Rectangle borders are only inner shading, not the frame.\n"
    )


def _format_reference_docs(docs: list[dict]) -> str:
    """Render pinned framework docs as a compact source-of-truth prompt block."""
    if not docs:
        return ""
    parts = [
        "",
        "FRAMEWORK SOURCE-OF-TRUTH DOCS (authoritative; prefer these types/properties over memory):",
    ]
    for doc in docs:
        name = doc.get("name", "reference-doc")
        language = doc.get("language", "")
        content = doc.get("content", "")
        if isinstance(content, dict):
            if content.get("source") == "quickshell-docs-types":
                critical = set(content.get("critical_types", []))
                type_lines = []
                for entry in content.get("types", []):
                    rel = f"{entry.get('module')}/{entry.get('name')}"
                    if rel not in critical:
                        continue
                    props = ", ".join(prop.get("name", "") for prop in entry.get("properties", [])[:10] if prop.get("name"))
                    variants = ", ".join(str(value) for value in entry.get("variants", [])[:10])
                    suffix = f" properties=[{props}]" if props else ""
                    if variants:
                        suffix += f" variants=[{variants}]"
                    type_lines.append(
                        f"- {rel}: import {entry.get('import', '')}; {entry.get('description', '')}{suffix}"
                    )
                rendered = "\n".join([
                    f"Quickshell docs snapshot {content.get('version')} from {content.get('index_url')}",
                    f"Types indexed: {content.get('type_count')} across {content.get('module_count')} modules.",
                    "Critical generation types:",
                    *type_lines,
                ])
                parts.append(f"\n--- {name} ---\n{rendered}")
            else:
                rendered = json.dumps(content, indent=2, sort_keys=True)[:4000]
                parts.append(f"\n--- {name} ---\n```json\n{rendered}\n```")
        elif isinstance(content, str) and content.strip():
            parts.append(f"\n--- {name} ---\n```{language}\n{content[:5000]}\n```")
    return "\n".join(parts) + "\n"


def _format_reference_templates(templates: list[dict]) -> str:
    """Render reference template files as a labeled prompt block.

    Each template is shown as a fenced code block tagged with its language so
    the LLM treats it as study material — not output to copy. Returns the
    empty string when no templates are supplied (older frameworks, conky, etc.).
    """
    if not templates:
        return ""
    parts = [
        "",
        "REFERENCE TEMPLATES (idiomatic, complete, palette-neutral — study the structure",
        "and patterns; do NOT copy verbatim, replace every literal with palette-driven values):",
    ]
    for tmpl in templates:
        name     = tmpl.get("name", "reference")
        language = tmpl.get("language", "")
        content  = tmpl.get("content", "")
        if not content:
            continue
        parts.append(f"\n--- {name} ---\n```{language}\n{content}\n```")
    return "\n".join(parts) + "\n"


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

    get_logger("craft.codegen").warning("could not parse LLM response as file objects")
    return []


def evaluate_files(
    files: list[dict], research: dict, design: dict,
) -> tuple[bool, list[str]]:
    """Deterministic post-generation gate for ``generate_files`` output.

    Returns ``(True, [])`` when the file set is acceptable; ``(False, reasons)``
    listing every defect found.  Reasons are short imperative sentences fed
    back to the LLM on retry so it can correct specific issues.

    Checks (cheap, all deterministic):
      - non-empty result
      - every required ``key_files`` entry from research syntax is produced
      - at least one palette hex value appears in the generated text
      - paths are relative and contain no ``..`` segments
      - each file content is non-trivially sized (≥50 chars)
    """
    reasons: list[str] = []
    if not files:
        return False, ["no files produced"]

    syntax = research.get("syntax", {}) if isinstance(research, dict) else {}
    required = {str(k).strip() for k in syntax.get("key_files", []) if str(k).strip()}
    produced = {str(f.get("path", "")).strip() for f in files if isinstance(f, dict)}
    missing = sorted(required - produced)
    if missing:
        reasons.append(f"missing required files: {missing}")

    palette = design.get("palette", {}) if isinstance(design, dict) else {}
    hexes = {str(v).lower() for v in palette.values() if isinstance(v, str) and v.startswith("#")}
    blob = "\n".join(str(f.get("content", "")) for f in files if isinstance(f, dict)).lower()
    if hexes and not any(h in blob for h in hexes):
        reasons.append("no palette hex values appear in generated files; "
                       "use the supplied palette colours, not hardcoded ones")

    for obj in files:
        if not isinstance(obj, dict):
            reasons.append(f"non-object file entry: {type(obj).__name__}")
            continue
        path = str(obj.get("path", "")).strip()
        content = str(obj.get("content", ""))
        if not path:
            reasons.append("file with empty path")
        elif path.startswith("/") or any(seg == ".." for seg in path.split("/")):
            reasons.append(f"unsafe path (must be relative, no '..'): {path!r}")
        if len(content) < 50:
            reasons.append(f"file {path!r} content too short ({len(content)} chars); "
                           "write the full file, do not abbreviate")
        if path.endswith(".yuck"):
            reasons.extend(_validate_yuck_content(path, content))
        if path.endswith(".qml"):
            reasons.extend(_validate_quickshell_qml_content(path, content, design, research))
    return (not reasons), reasons


def _validate_quickshell_qml_content(
    path: str,
    content: str,
    design: dict | None = None,
    research: dict | None = None,
) -> list[str]:
    """Cheap static guardrails for generated Quickshell/QML configs."""
    reasons: list[str] = []
    if re.search(r"\bIconImage\s*\{", content):
        reasons.append(
            f"file {path!r} uses IconImage, which is not available in the current Quickshell/QML runtime; "
            "use Text glyphs or QtQuick Image with a known URL instead"
        )
    promised = _promised_quickshell_widget_surfaces(design or {})
    panel_surfaces = len(re.findall(r"\bPanelWindow\s*\{", content))
    floating_surfaces = len(re.findall(r"\bFloatingWindow\s*\{", content))
    if promised and floating_surfaces:
        reasons.append(
            f"file {path!r} uses FloatingWindow for promised shell/widget chrome; "
            "on KDE/Wayland this can create normal decorated app windows with titlebars. "
            "Use PanelWindow for bars, launchers, menus, notification/quest cards, and corner widgets; "
            "anchor/margin them with exclusionMode Ignore when they should float visually."
        )
    if promised >= 3 and panel_surfaces < 3:
        reasons.append(
            f"file {path!r} defines only {panel_surfaces} PanelWindow shell surfaces for {promised} promised widget/panel surfaces; "
            "create visible top/bottom bars plus inventory/menu/log surfaces as PanelWindow, not token configs or FloatingWindow app chrome"
        )
    if promised >= 2:
        lower = content.lower()
        required_words = ("inventory", "rest", "ember", "launcher", "menu", "log")
        if sum(1 for word in required_words if word in lower) < 3:
            reasons.append(
                f"file {path!r} does not visibly implement the RPG widget grammar; include labelled inventory/rest/ember/menu/launcher surfaces"
            )
    if promised >= 2 and _quickshell_ornate_border_promised(design or {}):
        has_border_image = re.search(r"\bBorderImage\s*\{", content) is not None
        has_slice_or_tile = bool(re.search(r"\bborder\.(?:left|right|top|bottom)\s*:", content)) or "TileMode" in content
        if not (has_border_image and has_slice_or_tile):
            reasons.append(
                f"file {path!r} promises ornate/thorn/RPG menu chrome but does not use Quickshell/QtQuick BorderImage 9-slice/tiled borders; "
                "plain Rectangle border lines are not ornate enough for Diablo-style widget menus"
            )
        else:
            declared = declared_asset_paths((research or {}).get("texture_assets") if isinstance(research, dict) else None)
            referenced = referenced_borderimage_sources(content)
            if not declared:
                reasons.append(
                    f"file {path!r} uses ornate BorderImage chrome but no generated texture_assets metadata was provided; "
                    "run the texture subprocess before QML generation so preview/plan assets cannot drift from implementation"
                )
            missing = sorted(src for src in referenced if src.startswith("assets/") and src not in declared)
            if missing:
                reasons.append(
                    f"file {path!r} references undeclared BorderImage texture assets: {missing}; "
                    "use only generated texture_assets paths"
                )
        physical_cues = _quickshell_physical_rpg_menu_cues(content)
        if len(physical_cues) < 3:
            reasons.append(
                f"file {path!r} promises ornate Diablo/RPG menu chrome but only implements {sorted(physical_cues)} physical RPG cues; "
                "include at least three of: resource orbs/meters, recessed inventory ItemSlot/GridLayout, relic/quickslot belt, "
                "equipment/gear altar, selected item detail/stat pane. A palette/icon swap or flat dashboard labels are not enough."
            )
        flat_fills = _quickshell_flat_rectangle_fills(content)
        if flat_fills:
            reasons.append(
                f"file {path!r} promises ornate RPG menu chrome but still uses flat Rectangle fills as major interiors: {flat_fills[:5]}; "
                "use tiled Image texture fills and/or BorderImage-backed components for panel/button/slot interiors, leaving Rectangle only for transparent borders, shadows, masks, or tiny highlights."
            )
    return reasons


def _quickshell_physical_rpg_menu_cues(content: str) -> set[str]:
    """Detect non-trivial physical RPG menu structures beyond palette/icon swaps."""

    lower = content.lower()
    cues: set[str] = set()
    if "resourceorb" in lower or re.search(r"\borb\b|\bmeter\b|\bhealth\b|\bmana\b|\bsoul\b", lower):
        cues.add("resource_orb")
    if "itemslot" in lower or ("gridlayout" in lower and "inventory" in lower):
        cues.add("inventory_slots")
    if re.search(r"relic\s+belt|quickslot|beltsocket|launcher\s+menu", lower):
        cues.add("relic_belt")
    if re.search(r"gear\s+altar|equipment|helm|armor|mail|weapon|ring", lower):
        cues.add("equipment_gear")
    if re.search(r"item\s+detail|selected\s+relic|damage|statrow|durability|attunement", lower):
        cues.add("item_detail")
    return cues


def _quickshell_flat_rectangle_fills(content: str) -> list[str]:
    """Find likely flat QML Rectangle interior fills in ornate Quickshell output."""

    offenders: list[str] = []
    for match in re.finditer(r"Rectangle\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, flags=re.DOTALL):
        block = re.sub(r"\s+", " ", match.group(0)).strip()
        lower = block.lower()
        if 'color: "transparent"' in lower or "color: 'transparent'" in lower:
            continue
        # Borders, shadows, masks, meter fills, and tiny glints are allowed; the
        # failure mode is full/interior plates with solid dark gray/brown fills.
        if not any(anchor in lower for anchor in ("anchors.fill", "layout.fillwidth", "layout.fillheight")):
            continue
        if any(texture in lower for texture in ("borderimage", "image {", "soottexture", "slottexture", "embertexture")):
            continue
        if re.search(r"color\s*:\s*(?:qt\.rgba\([^)]*\)|['\"]#[0-9a-fA-F]{6,8}['\"])", block):
            offenders.append(block[:160])
    return offenders


def _quickshell_ornate_border_promised(design: dict) -> bool:
    """Return True when the design explicitly asks for ornate RPG/thorn chrome."""
    blob = json.dumps(design, sort_keys=True).lower()
    terms = (
        "ornate", "thorn", "thorns", "diablo", "rpg menu", "inventory frame",
        "carved border", "carved", "filigree", "9-slice", "tiled border",
        "borderimage", "relic", "blackiron", "bonfire",
    )
    return any(term in blob for term in terms)


def _promised_quickshell_widget_surfaces(design: dict) -> int:
    plan = design.get("visual_element_plan") if isinstance(design, dict) else []
    if not isinstance(plan, list):
        return 0
    count = 0
    for item in plan:
        if not isinstance(item, dict):
            continue
        tool = " ".join(str(item.get(k, "")).lower() for k in ("implementation_tool", "fallback_tool"))
        elem = str(item.get("desktop_element", "")).lower()
        if "quickshell" in tool and any(term in elem for term in ("widget", "panel", "launcher", "notification")):
            count += 1
    return count


def _validate_yuck_content(path: str, content: str) -> list[str]:
    """Cheap static guardrails for generated EWW/Yuck configs."""
    reasons: list[str] = []
    if re.search(r":geometry\s*\([^\n)]*calc\s*\(", content, flags=re.IGNORECASE | re.DOTALL):
        reasons.append(
            f"file {path!r} uses CSS calc() in EWW :geometry; use literal px or percent lengths"
        )
    if re.search(r"\$(?:[0-9]+|[A-Za-z_][A-Za-z0-9_]*)", content) and re.search(r"\b(awk|sed|sh\s+-c)\b", content):
        reasons.append(
            f"file {path!r} contains shell-style $ variables in EWW command strings; "
            "avoid awk positional fields or escape them so EWW interpolation does not blank them"
        )
    if re.search(r"\((?:progress|scale)\b[^)]*:value\s+[A-Za-z_][A-Za-z0-9_-]*", content):
        reasons.append(
            f"file {path!r} binds a raw variable to progress/scale :value; "
            "EWW requires a numeric value on first render, so provide a numeric fallback or use a label"
        )
    return reasons


def _structured_invoke(prompt: str, prior_reasons: list[str]) -> list[dict] | None:
    """Primary path: provider-enforced JSON via ``with_structured_output``.

    Returns the parsed file list, or ``None`` if structured output is
    unavailable on this stack (so the caller can fall back to text parsing).
    Raises only on genuine API/network errors so the outer loop can decide.
    """
    if not _PYDANTIC_AVAILABLE:
        return None
    from langchain_core.messages import HumanMessage, SystemMessage  # noqa: PLC0415
    llm = get_llm(temperature=0.85, max_tokens=8192)
    user = prompt + _retry_addendum(prior_reasons)
    try:
        structured = llm.with_structured_output(GeneratedFiles)
    except (NotImplementedError, AttributeError):
        return None  # provider/model can't bind a schema
    result = structured.invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=user),
    ])
    if isinstance(result, GeneratedFiles):
        return [{"path": f.path, "content": f.content} for f in result.files]
    if isinstance(result, dict) and isinstance(result.get("files"), list):
        return [
            {"path": str(f.get("path", "")), "content": str(f.get("content", ""))}
            for f in result["files"] if isinstance(f, dict)
        ]
    return []


def _text_invoke(prompt: str, prior_reasons: list[str]) -> list[dict]:
    """Fallback path: plain invoke + ``_parse_file_objects`` regex extraction."""
    from langchain_core.messages import HumanMessage, SystemMessage  # noqa: PLC0415
    llm = get_llm(temperature=0.85, max_tokens=8192)
    user = prompt + _retry_addendum(prior_reasons)
    response = llm.invoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=user),
    ])
    raw = response.content if hasattr(response, "content") else str(response)
    return _parse_file_objects(raw)


def _retry_addendum(prior_reasons: list[str]) -> str:
    """Format prior failure reasons as a corrective addendum to the prompt."""
    if not prior_reasons:
        return ""
    bullets = "\n".join(f"- {r}" for r in prior_reasons)
    return (
        "\n\nYour previous attempt was rejected for these specific reasons:\n"
        f"{bullets}\n\n"
        "Produce a new attempt that addresses every reason above. "
        "Do not repeat the same mistakes."
    )


def prepare_texture_assets(element: str, design: dict, research: dict) -> dict | None:
    """Generate and attach texture assets before Quickshell codegen when needed."""

    if not needs_texture_assets(element, design):
        return None
    session_dir = research.get("session_dir") or research.get("output_dir") or "."
    root = Path(session_dir) / "generated" / "quickshell"
    intent = extract_texture_intent(design)
    bundle = generate_texture_bundle(intent, root)
    reasons = validate_texture_bundle(bundle)
    if reasons:
        raise ValueError("texture asset validation failed: " + "; ".join(reasons))
    return json.loads(bundle.as_prompt_context())


def generate_files(element: str, design: dict, research: dict) -> list[dict]:
    """Generate config files via LLM with deterministic eval and retry.

    Returns a list of ``{path, content}`` dicts that have passed
    ``evaluate_files``.  Returns ``[]`` when every attempt fails so the craft
    node's outer retry/skip logic stays in control.
    """
    log = get_logger("craft.codegen")
    texture_assets = prepare_texture_assets(element, design, research)
    if texture_assets:
        research["texture_assets"] = texture_assets
    prompt = _build_prompt(element, research)
    prior_reasons: list[str] = []

    for attempt in range(1, MAX_CODEGEN_ATTEMPTS + 1):
        files: list[dict] | None = None
        try:
            files = _structured_invoke(prompt, prior_reasons)
        except Exception as exc:  # noqa: BLE001 — provider/schema-parse quirks
            log.warning("codegen attempt %d structured path raised: %s; "
                        "falling back to text-parse path", attempt, exc)
            files = None

        if files is None:  # unavailable or raised → text-parse fallback
            try:
                files = _text_invoke(prompt, prior_reasons)
            except Exception as exc:  # noqa: BLE001 — genuine API/network error
                log.warning("codegen attempt %d text path failed: %s", attempt, exc)
                files = []

        ok, reasons = evaluate_files(files, research, design)
        if ok:
            log.info("codegen attempt %d passed evaluator (%d files)", attempt, len(files))
            return files
        log.warning("codegen attempt %d rejected: %s", attempt, "; ".join(reasons))
        prior_reasons = reasons

    log.warning("codegen exhausted %d attempts; returning empty", MAX_CODEGEN_ATTEMPTS)
    return []
