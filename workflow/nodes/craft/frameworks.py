"""craft/frameworks.py — Framework knowledge base for the craft agent.

Each entry gives the craft codegen agent: install hints, config paths, key
syntax patterns, and a short idiomatic example snippet.  The agent uses this
as *grounding* — it is NOT a template.  The actual generated code should be
fully original and adapted to the design system.
"""
from __future__ import annotations

from pathlib import Path

# Elements whose provider belongs to the craft pipeline (agentic codegen).
# Providers NOT in this set go through the standard materializer path.
CRAFT_PROVIDERS: frozenset[str] = frozenset({
    "eww", "ags", "quickshell", "conky", "ignis",
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
    ),
    "example": """\
(defvar volume 50)
(deflisten workspaces :initial "[]"
  `hyprctl workspaces -j | jq '[.[] | {id, name}]'`)

(defwidget bar []
  (box :class "bar" :orientation "h" :halign "fill"
    (box :class "workspaces" :space-evenly false
      (for ws in workspaces
        (button :class "ws-btn ${ws.id}" :onclick "hyprctl dispatch workspace ${ws.id}"
          (label :text "${ws.name}"))))
    (box :class "center" :halign "center"
      (label :class "time" :text {formattime(EWW_TIME, "%H:%M")}))
    (label :class "vol" :text "Vol: ${volume}%")))

(defwindow main-bar
  :monitor 0
  :geometry (geometry :x "0" :y "0" :width "100%" :height "36px" :anchor "top center")
  :stacking "fg"
  :exclusive true
  (bar))
""",
}

_AGS = {
    "name": "AGS / Astal (GJS)",
    "config_dir": "~/.config/ags",
    "key_files": ["app.ts", "app.js", "style.css"],
    "syntax_hint": (
        "AGS uses GJS (GNOME JavaScript) with TypeScript support via Astal.\n"
        "Widgets are created via Astal/AGS APIs: Widget.Box, Widget.Label, Widget.Button.\n"
        "Services provide reactive data: Battery, Network, Audio, Hyprland, etc.\n"
        "Style with CSS via css property or external .css file.\n"
        "App.start({ main }) is the entry point.\n"
    ),
    "example": """\
import { App, Astal, Gtk, Gdk } from "astal/gtk3"
import { Variable, bind } from "astal"
import Battery from "gi://AstalBattery"

const time = Variable("").poll(1000, "date +'%H:%M'")
const battery = Battery.get_default()

function Bar(monitor: Gdk.Monitor) {
  return <window
    className="bar"
    gdkmonitor={monitor}
    anchor={Astal.WindowAnchor.TOP | Astal.WindowAnchor.LEFT | Astal.WindowAnchor.RIGHT}
    exclusivity={Astal.Exclusivity.EXCLUSIVE}
  >
    <box>
      <label label={bind(time)} />
      <label label={bind(battery, "percentage").as(p => `${Math.round(p * 100)}%`)} />
    </box>
  </window>
}
App.start({ main: () => App.get_monitors().forEach(Bar) })
""",
}

_QUICKSHELL = {
    "name": "Quickshell (QML)",
    "config_dir": "~/.config/quickshell",
    "key_files": ["shell.qml"],
    "syntax_hint": (
        "Quickshell uses QML (Qt Modeling Language).\n"
        "ShellRoot is the entry point; PanelWindow, FloatingWindow create surfaces.\n"
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

FRAMEWORK_REFS: dict[str, dict] = {
    "eww":        _EWW,
    "ags":        _AGS,
    "quickshell": _QUICKSHELL,
    "conky":      _CONKY,
    "waybar":     _WAYBAR,
}


def get_reference(framework: str) -> dict:
    """Return the knowledge-base entry for *framework*, or an empty stub."""
    return FRAMEWORK_REFS.get(framework, {"name": framework, "config_dir": "", "key_files": [], "syntax_hint": "", "example": ""})


def config_dir(framework: str) -> Path | None:
    ref = get_reference(framework)
    cd = ref.get("config_dir", "")
    return Path(cd).expanduser() if cd else None
