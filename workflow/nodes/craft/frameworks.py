"""craft/frameworks.py — Framework knowledge base for the craft agent.

Each entry gives the craft codegen agent: install hints, config paths, key
syntax patterns, a short idiomatic example, and (optionally) a list of
reference templates loaded from ``templates/<framework>/`` at the repo root.

The agent uses these as *grounding* — they are NOT materializer templates.
The actual generated code should be fully original and adapted to the design
system. Reference templates show idiomatic patterns; the craft prompt tells
the LLM to study them but never copy.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...log_setup import get_logger

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TEMPLATES_ROOT = _REPO_ROOT / "templates"
_REFERENCES_ROOT = _REPO_ROOT / "references"


def _load_reference_templates(paths: list[str]) -> list[dict]:
    """Load reference template files relative to the repo's templates/ dir.

    Returns a list of {"name": str, "language": str, "content": str} for each
    file that exists and reads cleanly. Missing or unreadable files are
    skipped silently — the framework reference still functions without them.
    """
    out: list[dict] = []
    for rel in paths:
        fp = _TEMPLATES_ROOT / rel
        try:
            content = fp.read_text(encoding="utf-8")
        except OSError as exc:
            get_logger("craft.frameworks").warning("could not read template %s: %s", fp, exc)
            continue
        out.append({
            "name":     rel,
            "language": fp.suffix.lstrip(".") or "txt",
            "content":  content,
        })
    return out


def _load_reference_docs(paths: list[str]) -> list[dict[str, Any]]:
    """Load pinned framework documentation relative to references/.

    These are source-of-truth docs snapshots, not examples. They should be used
    to constrain codegen/static validation when editing framework config.
    """
    out: list[dict[str, Any]] = []
    for rel in paths:
        fp = _REFERENCES_ROOT / rel
        try:
            if fp.suffix == ".json":
                parsed = json.loads(fp.read_text(encoding="utf-8"))
                out.append({"name": rel, "language": "json", "content": parsed})
            else:
                out.append({"name": rel, "language": fp.suffix.lstrip(".") or "txt", "content": fp.read_text(encoding="utf-8")})
        except (OSError, json.JSONDecodeError) as exc:
            get_logger("craft.frameworks").warning("could not read reference doc %s: %s", fp, exc)
            continue
    return out

# Elements whose provider belongs to the craft pipeline (agentic codegen).
# Providers NOT in this set go through the standard materializer path.
CRAFT_PROVIDERS: frozenset[str] = frozenset({
    "eww", "quickshell", "conky", "ignis",
})

# Also craft-route any bar: element with these providers.
CRAFT_BAR_PROVIDERS: frozenset[str] = frozenset({
    "waybar",   # when paired with a custom design, generate full CSS+JSON from scratch
})


def is_craft_element(element: str) -> bool:
    """Return True when *element* should be handled by craft_node."""
    if ":" not in element:
        return False
    category, provider = element.split(":", 1)
    if category == "widgets" and provider in CRAFT_PROVIDERS:
        return True
    if category == "bar" and provider in CRAFT_BAR_PROVIDERS:
        return True
    return False


def framework_for(element: str) -> str | None:
    """Derive the framework name from an element string."""
    if ":" in element:
        _, provider = element.split(":", 1)
        return provider
    return None


# ── Per-framework knowledge ───────────────────────────────────────────────────

_EWW = {
    "name": "EWW (ElKowars Wacky Widgets)",
    "config_dir": "~/.config/eww",
    "key_files": ["eww.yuck", "eww.scss"],
    "syntax_hint": (
        "EWW uses Yuck (Lisp-like) for structure and SCSS for styling.\n"
        "defwidget defines a reusable component; defwindow places it on screen.\n"
        "Variables come from defvar/deflisten; ${variable} interpolation in strings.\n"
        "box, label, image, button, graph, scale, scroll are the core widgets.\n"
        "Anchors: top-left, top-center, top-right, center-left, center, bottom-right, etc.\n"
        "Windows use :monitor, :geometry, :anchor, :stacking (foreground/background).\n"
        "EWW geometry lengths must be literal values such as \"42px\" or \"80%\"; never use CSS calc() in :geometry.\n"
        "Inside defpoll/deflisten shell commands, avoid awk positional fields like $1/$2/$3 or escape them so EWW does not consume them as variables. Prefer grep/cut/python one-liners.\n"
        "EWW progress/scale :value must always be numeric at first render; avoid binding raw defpoll variables that can start empty, or use a text label/fallback.\n"
        "Keep compositor commands desktop-aware: hyprctl is Hyprland-only; do not use it on KDE/Plasma.\n"
    ),
    "example": """\
(defvar volume 50)
(defvar launcher_items '["Terminal", "Files", "Browser", "Settings", "Lock"]')
(defpoll active_title :interval "2s" "xdotool getactivewindow getwindowname 2>/dev/null || echo Desktop")

(defwidget action-menu []
  (box :class "relic-menu" :orientation "v" :space-evenly false
    (label :class "title" :text "${active_title}")
    (for item in launcher_items
      (button :class "menu-row" :onclick "printf '%s\\n' '${item}'"
        (label :text "${item}")))))

(defwindow shrine-menu
  :monitor 0
  :geometry (geometry :x "24px" :y "72px" :width "260px" :height "360px" :anchor "top right")
  :stacking "fg"
  :exclusive false
  (action-menu))
""",
}

_QUICKSHELL = {
    "name": "Quickshell (QML)",
    "config_dir": "~/.config/quickshell",
    "key_files": ["shell.qml"],
    "syntax_hint": (
        "Quickshell uses QML (Qt Modeling Language).\n"
        "ShellRoot is the entry point; use PanelWindow for shell chrome surfaces.\n"
        "Do NOT use FloatingWindow for bars, launchers, menus, notification cards, or desktop widgets; "
        "on KDE/Wayland it may appear as a normal decorated app window with a titlebar.\n"
        "For visually floating widgets, still use PanelWindow with edge/corner anchors, margins, and exclusionMode Ignore.\n"
        "When the design asks for ornate, thorned, carved, Diablo/RPG, relic, or inventory-frame chrome, use QtQuick BorderImage 9-slice/tiled borders for panels/buttons/slots; plain Rectangle border lines are not ornate enough.\n"
        "If GENERATED ORNATE TEXTURE ASSETS are present in the prompt, BorderImage.source must use those exact relative paths (for example assets/<theme>/panel_ornate_9slice.png), border.left/right/top/bottom must use the listed slice_px, and horizontal/vertical tile modes should repeat edge segments.\n"
        "Use Quickshell.io APIs: SystemTray, Brightness, Audio, Hyprland.\n"
        "Layouts: RowLayout, ColumnLayout, Item, Rectangle, Text.\n"
        "Anchors: anchors.fill, anchors.top, anchors.horizontalCenter.\n"
        "Colors via Qt.rgba() or hex strings; font.pixelSize for sizing.\n"
    ),
    "example": """\
import Quickshell
import QtQuick
import QtQuick.Layouts

ShellRoot {
  PanelWindow {
    id: bar
    anchors { top: true; left: true; right: true }
    height: 36
    color: "#1e1e2e"

    RowLayout {
      anchors.fill: parent
      anchors.margins: 8

      Text {
        text: Qt.formatTime(new Date(), "hh:mm")
        color: "#cdd6f4"
        font.pixelSize: 14
        Timer { interval: 1000; running: true; repeat: true; onTriggered: parent.text = Qt.formatTime(new Date(), "hh:mm") }
      }
      Item { Layout.fillWidth: true }
    }
  }
}
""",
}

_CONKY = {
    "name": "Conky",
    "config_dir": "~/.config/conky",
    "key_files": ["conky.conf"],
    "syntax_hint": (
        "Conky uses a Lua config table (conky.config) + conky.text template string.\n"
        "Key config keys: alignment, gap_x, gap_y, own_window, own_window_type (desktop/panel),\n"
        "own_window_argb_value (transparency), font, color0-9, default_color.\n"
        "Template variables: ${cpu}, ${mem}, ${time}, ${fs_used_perc /}, ${battery_percent}.\n"
        "Use ${color #rrggbb} mid-template to switch colors.\n"
        "own_window_type = 'desktop' renders behind icons; 'panel' claims a strut.\n"
    ),
    "example": """\
conky.config = {
  alignment = 'top_right',
  gap_x = 24, gap_y = 48,
  own_window = true,
  own_window_type = 'desktop',
  own_window_argb_visual = true,
  own_window_argb_value = 180,
  font = 'JetBrainsMono Nerd Font:size=10',
  default_color = 'cdd6f4',
  color1 = '89b4fa',
  use_xft = true,
  update_interval = 2,
}
conky.text = [[
${color1}CPU  ${color}${cpu cpu0}%  ${cpubar cpu0 6,120}
${color1}MEM  ${color}${mem} / ${memmax}  ${membar 6,120}
${color1}TIME ${color}${time %H:%M:%S}
]]
""",
}

_WAYBAR = {
    "name": "Waybar",
    "config_dir": "~/.config/waybar",
    "key_files": ["config.jsonc", "style.css"],
    "syntax_hint": (
        "Waybar uses a JSONC config and a CSS stylesheet.\n"
        "Top-level keys: layer, position, height, modules-left/center/right.\n"
        "Each module key references a built-in (e.g. 'clock', 'hyprland/workspaces') or custom module.\n"
        "Modules have label-format, tooltip-format, on-click, interval settings.\n"
        "CSS: #clock, #workspaces button, .modules-left etc. — use full CSS3 including gradients.\n"
        "Custom scripts via custom/name: exec, interval, return-type (json/text).\n"
    ),
    "example": """\
// config.jsonc
{
  "layer": "top", "position": "top", "height": 36,
  "modules-left": ["hyprland/workspaces"],
  "modules-center": ["clock"],
  "modules-right": ["pulseaudio", "battery"],
  "clock": {"format": "{:%H:%M}", "tooltip-format": "{:%A %d %B}"},
  "battery": {"format": "{capacity}% {icon}", "format-icons": ["","","","",""]}
}

/* style.css */
* { font-family: "JetBrainsMono Nerd Font"; font-size: 13px; }
window#waybar { background: rgba(30,30,46,0.9); color: #cdd6f4; }
#clock { padding: 0 12px; color: #89b4fa; }
""",
}

# Reference-template paths, relative to <repo>/templates/. Loaded lazily by
# get_reference() so the disk read happens only when a craft element actually
# fires (and so import of this module stays cheap).
_REFERENCE_TEMPLATE_PATHS: dict[str, list[str]] = {
    "eww": [
        "eww/_reference/bar.yuck",
        "eww/_reference/bar.scss",
    ],
    "quickshell": [
        "quickshell/bar.qml",
        "quickshell/floating-widget.qml",
    ],
    "conky":   [],
    "waybar":  [],
}

# Source-of-truth documentation paths, relative to <repo>/references/.
# These are docs snapshots/schemas used to constrain framework config editing.
_REFERENCE_DOC_PATHS: dict[str, list[str]] = {
    "quickshell": [
        "quickshell-v0.3.0-types/index.json",
        "quickshell-v0.3.0-types/summary.md",
    ],
}


FRAMEWORK_REFS: dict[str, dict] = {
    "eww":        _EWW,
    "quickshell": _QUICKSHELL,
    "conky":      _CONKY,
    "waybar":     _WAYBAR,
}


def get_reference(framework: str) -> dict:
    """Return the knowledge-base entry for *framework*, or an empty stub.

    Adds a ``reference_templates`` key with file-backed exemplars (loaded from
    ``<repo>/templates/<framework>/``) so the craft prompt can show the LLM
    multiple complete reference files alongside the inline ``example`` snippet.
    """
    ref = FRAMEWORK_REFS.get(framework)
    if ref is None:
        return {
            "name": framework, "config_dir": "", "key_files": [],
            "syntax_hint": "", "example": "", "reference_templates": [], "reference_docs": [],
        }
    paths = _REFERENCE_TEMPLATE_PATHS.get(framework, [])
    docs = _REFERENCE_DOC_PATHS.get(framework, [])
    return {**ref, "reference_templates": _load_reference_templates(paths), "reference_docs": _load_reference_docs(docs)}


def config_dir(framework: str) -> Path | None:
    ref = get_reference(framework)
    cd = ref.get("config_dir", "")
    return Path(cd).expanduser() if cd else None
