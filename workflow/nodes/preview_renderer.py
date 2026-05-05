"""Deterministic SVG-in-HTML preview renderer for Step 4.

The plan step needs expressive visual range (ornamental RPG frames, HUD panels,
codex/tome chrome) without trusting an LLM to hand-write valid HTML.  This module
turns the validated design JSON into a portable single-file concept sheet.
"""
from __future__ import annotations

import html
import json
import re

DEFAULT_PALETTE = {
    "background": "#12100f", "foreground": "#eadfcf", "primary": "#c57b45",
    "secondary": "#807160", "accent": "#f0a65c", "surface": "#211a16",
    "muted": "#615247", "danger": "#b84a4a", "success": "#7d8c6e", "warning": "#c9a03e",
}

STYLE_KEYWORDS = {
    "sci_fi_hud": ("hud", "cyber", "neon", "signal", "terminal", "scanner", "glitch"),
    "tome_codex": ("tome", "codex", "book", "manuscript", "parchment", "inn", "bonfire"),
    "rpg_menu": ("rpg", "game", "menu", "quest", "inventory", "ember", "fantasy", "gothic"),
}


def render_preview_html(design: dict, feedback_block: str = "") -> str:
    """Return a complete non-empty HTML preview for *design*.

    The output embeds SVG inside a CSS-styled DOM container.  Palette values
    are exposed as CSS custom properties on :root so the surrounding chrome
    (sheet card, notes pane, future ornaments) can be themed without
    re-rendering the SVG, and so the design contract — including
    ``chrome_strategy.rounded_corners`` — is honoured visibly.
    """
    design = design if isinstance(design, dict) else {}
    palette = _palette(design.get("palette", {}))
    name = _text(design.get("name"), "untitled-rice")
    style = _infer_style(design)
    mood = ", ".join(_list_text(design.get("mood_tags"))) or "bespoke desktop ritual"
    description = _text(design.get("description"), "A Linux desktop theme concept.")
    radii = _radius_scale(design)
    notes_html = _feedback_html(feedback_block)
    svg = _render_svg(design, palette, name, style, mood, description, radii)
    design_meta = html.escape(json.dumps(
        {"name": name, "style": style, "rounded": radii["enabled"]}, sort_keys=True,
    ))
    palette_vars = ";".join(f"--{k}:{v}" for k, v in palette.items())
    return f"""<!DOCTYPE html>
<html lang="en" data-preview-engine="svg-v2" data-preview-style="{style}" data-rounded="{str(radii['enabled']).lower()}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="linux-ricing-preview" content="deterministic-svg"><meta name="design-meta" content="{design_meta}">
<title>{html.escape(name)} — Desktop Preview</title><style>
:root{{{palette_vars}}}
html,body{{margin:0;min-height:100%;background:var(--background);color:var(--foreground);font:15px/1.5 Inter,system-ui,sans-serif}}
main{{min-height:100vh;display:grid;place-items:center;padding:28px;box-sizing:border-box}}
/* overflow:hidden lets the SVG rx frame define the card shape */
.sheet{{width:min(1280px,96vw);overflow:hidden;box-shadow:0 28px 80px #000b}}
.sheet>svg{{display:block;width:100%;height:auto}}
.notes{{width:min(1180px,92vw);margin:18px auto 0;padding:14px 18px;border:1px solid var(--muted);background:var(--surface);color:var(--foreground);outline:1px solid var(--surface)}}
.notes b{{color:var(--accent)}}
</style></head><body><main><div class="sheet">{svg}</div>{notes_html}</main></body></html>"""


def _render_svg(design: dict, p: dict[str, str], name: str, style: str, mood: str, description: str, r: dict[str, int]) -> str:
    title = html.escape(name.replace("-", " ").title())
    desc = html.escape(description)
    moves = _non_default_moves(design)[:4]
    widgets = _widgets(design)[:2]
    ornament = _ornament_path(style, r["enabled"])
    frame_label = {"sci_fi_hud": "SIGNAL HUD", "tome_codex": "EMBER CODEX", "rpg_menu": "RPG MENU"}.get(style, "RPG MENU")
    return f"""<svg role="img" aria-label="{title} preview" viewBox="0 0 1280 760" xmlns="http://www.w3.org/2000/svg">
<defs>{_defs(p, style)}</defs>
<rect width="1280" height="760" fill="url(#bg)"/><rect width="1280" height="760" filter="url(#grain)" opacity=".22"/>
<g data-frame-style="{style}">{_frame(38,36,1204,688,p,ornament,r)}</g>
<text x="88" y="92" fill="{p['accent']}" font-size="22" font-family="serif" letter-spacing="5">{frame_label}</text>
<text x="88" y="132" fill="{p['foreground']}" font-size="46" font-weight="800">{title}</text>
<text x="90" y="165" fill="{p['secondary']}" font-size="16">{html.escape(mood)}</text>
<text x="90" y="196" fill="{p['foreground']}" font-size="15">{_clip(desc, 126)}</text>
{_palette_board(p)}{_terminal_panel(p, style, r)}{_launcher_panel(p, moves, style, r)}{_widget_panels(p, widgets, r)}
<path d="M90 620 C245 580, 330 698, 520 646 S790 602, 970 666 S1130 650,1190 608" stroke="{p['accent']}" stroke-width="3" fill="none" opacity=".6" filter="url(#glow)"/>
</svg>"""


def _defs(p: dict[str, str], style: str) -> str:
    angle = "0" if style == "sci_fi_hud" else "90"
    return f"""<linearGradient id="bg" x1="0" x2="1" y1="0" y2="1"><stop stop-color="{p['background']}"/><stop offset="1" stop-color="{p['surface']}"/></linearGradient>
<linearGradient id="metal" gradientTransform="rotate({angle})"><stop stop-color="{p['muted']}"/><stop offset=".45" stop-color="{p['primary']}"/><stop offset="1" stop-color="{p['accent']}"/></linearGradient>
<filter id="glow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="table" tableValues="0 .2"/></feComponentTransfer></filter>"""


def _frame(x: int, y: int, w: int, h: int, p: dict[str, str], ornament: str, r: dict[str, int]) -> str:
    outer_rx = r["frame"]
    inner_rx = max(0, outer_rx - 8)
    corners = "".join(
        f"<path d='{ornament}' transform='translate({cx} {cy}) rotate({rot})' fill='{p['accent']}' opacity='.85'/>"
        for cx, cy, rot in (
            (x+30, y+30, 0), (x+w-30, y+30, 90),
            (x+w-30, y+h-30, 180), (x+30, y+h-30, 270),
        )
    )
    rivets = "".join(
        f"<circle cx='{x+i*96}' cy='{y+16}' r='4' fill='{p['warning']}' opacity='.75'/>"
        for i in range(1, 12)
    )
    return (
        f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{outer_rx}'"
        f" fill='{p['surface']}' stroke='url(#metal)' stroke-width='8'/>"
        f"<rect x='{x+22}' y='{y+22}' width='{w-44}' height='{h-44}' rx='{inner_rx}'"
        f" fill='none' stroke='{p['primary']}' stroke-width='2' opacity='.75'/>"
        f"{corners}{rivets}"
    )


def _terminal_panel(p: dict[str, str], style: str, r: dict[str, int]) -> str:
    prompt = "❯" if style != "sci_fi_hud" else "λ"
    rows = ["palette.sync --accent", "materialize ornamental frame", "launch preview.energy++"]
    text = "".join(
        f"<text x='150' y='{342+i*34}' fill='{p['foreground']}'"
        f" font-size='18' font-family='monospace'>{prompt} {html.escape(row)}</text>"
        for i, row in enumerate(rows)
    )
    panel_rx = r["panel"]
    return (
        f"<g data-panel='terminal'>"
        f"<rect x='112' y='278' width='565' height='190' rx='{panel_rx}'"
        f" fill='{p['background']}' stroke='{p['accent']}' stroke-width='3'/>"
        f"<path d='M125 306 H664' stroke='url(#metal)' stroke-width='8' opacity='.9'/>"
        f"{text}"
        f"<rect x='133' y='435' width='514' height='10' fill='{p['primary']}' opacity='.35'/>"
        f"</g>"
    )


def _launcher_panel(p: dict[str, str], moves: list[str], style: str, r: dict[str, int]) -> str:
    labels = moves or ["ornamental panel chrome", "palette-bound terminal", "custom launcher menu", "diegetic widgets"]
    row_rx = r["row"]
    rows = []
    for i, item in enumerate(labels[:4]):
        y = 300 + i * 54
        rows.append(
            f"<rect x='742' y='{y}' width='390' height='38' rx='{row_rx}'"
            f" fill='{p['surface']}' stroke='{p['muted']}'/>"
            f"<text x='760' y='{y+25}' fill='{p['foreground']}' font-size='15'>"
            f"◆ {_clip(html.escape(item), 58)}</text>"
        )
    glyph = "◇" if style == "sci_fi_hud" else "✦"
    return (
        f"<g data-panel='launcher'>"
        f"<text x='740' y='258' fill='{p['accent']}' font-size='25'>"
        f"{glyph} Launcher Ritual</text>"
        f"{''.join(rows)}</g>"
    )


def _palette_board(p: dict[str, str]) -> str:
    keys = list(DEFAULT_PALETTE)
    cells = []
    for i, k in enumerate(keys):
        x, y = 90 + (i % 5) * 112, 676 + (i // 5) * 32
        cells.append(f"<rect x='{x}' y='{y}' width='26' height='20' fill='{p[k]}' stroke='#000'/><text x='{x+34}' y='{y+15}' fill='{p['foreground']}' font-size='10'>{k}</text>")
    return f"<g data-panel='palette'>{''.join(cells)}</g>"


def _widget_panels(p: dict[str, str], widgets: list[dict], r: dict[str, int]) -> str:
    if not widgets:
        widgets = [{"name": "focus-glyph", "visual_concept": "ambient system state as a glowing emblem"}]
    widget_rx = r["widget"]
    out = []
    for i, widget in enumerate(widgets):
        y = 500 + i * 74
        name = html.escape(_text(widget.get("name"), f"widget-{i+1}").replace("-", " ").title())
        concept = html.escape(_clip(_text(widget.get("visual_concept"), "custom themed widget"), 74))
        out.append(
            f"<g data-panel='widget'>"
            f"<rect x='738' y='{y}' width='402' height='54' rx='{widget_rx}'"
            f" fill='{p['background']}' stroke='{p['primary']}'/>"
            f"<circle cx='765' cy='{y+27}' r='14' fill='{p['accent']}' filter='url(#glow)'/>"
            f"<text x='790' y='{y+23}' fill='{p['foreground']}' font-size='15'>{name}</text>"
            f"<text x='790' y='{y+42}' fill='{p['secondary']}' font-size='11'>{concept}</text>"
            f"</g>"
        )
    return "".join(out)


def _radius_scale(design: dict) -> dict[str, int]:
    """Return SVG rx/ry values for each panel type based on chrome_strategy.

    When ``chrome_strategy.rounded_corners`` is explicitly *false* (any
    falsy spelling: ``false``, ``"false"``, ``"none"``, ``"no"``, ``"off"``,
    ``"disabled"``, or ``{"enabled": false}``), all radii are zeroed so the
    preview renders sharp, angular geometry that matches the design intent.

    When rounded corners are allowed (the default when the key is absent or
    truthy), scaled defaults are used.  A dict value with a ``"radius_px"``
    key is interpreted as an explicit pixel hint.
    """
    chrome = design.get("chrome_strategy", {}) if isinstance(design, dict) else {}
    rounded = chrome.get("rounded_corners") if isinstance(chrome, dict) else None

    # Explicit opt-out
    explicitly_off = (
        rounded is False
        or (isinstance(rounded, str) and rounded.strip().lower() in ("false", "none", "no", "off", "disabled"))
        or (isinstance(rounded, dict) and rounded.get("enabled") is False)
    )
    if explicitly_off:
        return {"enabled": False, "card": 0, "frame": 0, "panel": 0, "row": 0, "widget": 0}

    # Explicit radius hint
    hint = (rounded.get("radius_px") if isinstance(rounded, dict) else None) or 0
    try:
        hint = max(0, int(hint))
    except (TypeError, ValueError):
        hint = 0

    base = hint if hint else 26
    return {
        "enabled": True,
        "card": base,
        "frame": base,
        "panel": max(0, base - 8),
        "row": max(0, base - 20),
        "widget": max(0, base - 12),
    }


def _feedback_html(feedback: str) -> str:
    if not feedback.strip():
        return ""
    return f"<aside class='notes'><b>Revision notes shaping this render:</b><br>{html.escape(feedback)}</aside>"


def _palette(raw: dict) -> dict[str, str]:
    return {k: v if isinstance(v := raw.get(k), str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v) else DEFAULT_PALETTE[k] for k in DEFAULT_PALETTE}


def _infer_style(design: dict) -> str:
    haystack = json.dumps(design or {}, default=str).lower()
    explicit = str((design or {}).get("preview_style", "")).lower().replace("-", "_")
    if explicit in STYLE_KEYWORDS:
        return explicit
    scores = {style: sum(word in haystack for word in words) for style, words in STYLE_KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "rpg_menu"


def _non_default_moves(design: dict) -> list[str]:
    strategy = design.get("originality_strategy", {}) if isinstance(design, dict) else {}
    return _list_text(strategy.get("non_default_moves") if isinstance(strategy, dict) else [])


def _widgets(design: dict) -> list[dict]:
    widgets = design.get("widget_layout", []) if isinstance(design, dict) else []
    return [w for w in widgets if isinstance(w, dict)]


def _list_text(values) -> list[str]:
    return [str(v) for v in values] if isinstance(values, list) else []


def _text(value, fallback: str) -> str:
    return str(value).strip() if value else fallback


def _clip(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _ornament_path(style: str, rounded: bool = True) -> str:
    """Return an SVG path for corner ornaments.

    When *rounded* is False (sharp geometry requested) the angular paths are
    preferred for all styles so the ornaments reinforce the no-rounded-corners
    intent instead of introducing soft shapes at the corners.
    """
    if not rounded:
        # Tight cross / bracket mark — all sharp
        return "M-24,0 L0,-6 L24,0 L0,6 Z"
    if style == "sci_fi_hud":
        return "M0,-24 L24,0 L0,24 L-8,8 L-24,0 L-8,-8 Z"
    if style == "tome_codex":
        return "M0,-28 C18,-18 28,0 0,28 C-28,0 -18,-18 0,-28 Z"
    return "M0,-30 L10,-10 L30,0 L10,10 L0,30 L-10,10 L-30,0 L-10,-10 Z"