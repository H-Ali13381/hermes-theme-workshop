from __future__ import annotations

import json

ANALYSIS_SYSTEM_PROMPT = """\
You are a visual design analyst. Given a reference image and a creative direction,
extract a coherent color palette and design guidance for a Linux desktop theme.

Return ONLY a JSON object with these exact keys:
{
  "style_description": "<2-3 sentences on the full desktop/theme atmosphere>",
  "atmosphere": "<lighting/texture/depth — e.g. 'soft ember glow through stone'>",
  "extracted_palette": {
    "background": "#rrggbb", "foreground": "#rrggbb", "primary": "#rrggbb",
    "secondary": "#rrggbb", "accent": "#rrggbb", "surface": "#rrggbb",
    "muted": "#rrggbb", "danger": "#cc3333", "success": "#3a7a3a", "warning": "#cc8833"
  },
  "ui_recommendations": "<panel, terminal, launcher, widgets, window borders feel>",
  "composition_notes": "<full-desktop layout/chrome decisions the image suggests>",
  "visual_element_plan": [
    {
      "id": "toolbar_or_panel",
      "source_visual_description": "<what is visible in the image: shape, material, placement>",
      "desktop_element": "panel/widgets/launcher/terminal/window_chrome/wallpaper/icons/notifications/lock_screen",
      "implementation_tool": "<preferred concrete tool/materializer such as widgets:quickshell, widgets:eww, terminal:kitty, look_and_feel:kde>",
      "fallback_tool": "<fallback tool or empty string>",
      "config_targets": ["<expected config paths or materializer targets>"],
      "validation_probe": "<how to verify the planned element exists after implementation>",
      "acceptable_deviation": "<what may differ without violating the concept>"
    }
  ],
  "validation_checklist": [
    "<specific visual-contract check, e.g. non-default toolbar replaces or hides stock KDE panel>",
    "<specific visual-contract check, e.g. wallpaper/background matches overview mood>",
    "<specific visual-contract check, e.g. implementation is more than palette/icon swap>"
  ]
}

All palette values must be valid #rrggbb hex. danger=red, success=green, warning=amber.
Break the generated image into concrete, implementable desktop elements before recommending tools. Prefer Quickshell for KDE/Wayland custom toolbar/widget chrome; use EWW only as an explicit fallback.
"""

PREVIEW_SYSTEM_PROMPT = """\
You are generating the Step 2.5 AI desktop theme preview HTML page for a Linux desktop theme.

The FAL/nano-banana image is the representative desktop overview and must dominate the page.
Do not reinterpret it into a generic HTML dashboard, style guide, or card grid. The page's
job is to present the single generated desktop overview as the primary artifact, then add
supporting palette and terminal/color readouts underneath.

Show:
1. The AI-generated full-desktop theme concept image as a dominant representative overview (<img> with the provided URL)
2. The 10 extracted palette swatches with hex labels
3. Terminal color views and a concise UI breakdown: window borders, terminal, launcher, panel/widgets, icon/menu direction
4. Style description and atmosphere text

Use CSS only to frame and support the hero: animations, gradients, filters, custom properties,
ornamental borders, and mood lighting are welcome, but the generated image remains primary.
The page itself should embody the theme mood — not a generic card layout.
Output ONLY the complete HTML file. No markdown fences, no explanation.
"""


def select_overview_aspect_ratio(profile: dict) -> str:
    """Choose the closest FAL aspect ratio for the intended desktop overview canvas."""
    target = overview_target_geometry(profile)
    if not target:
        return "16:9"
    width, height = target
    if width <= 0 or height <= 0:
        return "16:9"
    ratio = width / height
    choices = {
        "4:3": 4 / 3,
        "3:2": 3 / 2,
        "16:9": 16 / 9,
        "21:9": 21 / 9,
    }
    return min(choices, key=lambda key: abs(choices[key] - ratio))


def overview_target_geometry(profile: dict) -> tuple[int, int] | None:
    geometries = profile.get("screen_geometries") if isinstance(profile, dict) else None
    if isinstance(geometries, list) and geometries:
        rects = []
        for item in geometries:
            if not isinstance(item, dict):
                continue
            try:
                x = int(item.get("x", 0)); y = int(item.get("y", 0))
                w = int(item.get("width", 0)); h = int(item.get("height", 0))
            except (TypeError, ValueError):
                continue
            if w > 0 and h > 0:
                rects.append((x, y, w, h))
        if len(rects) > 1:
            min_x = min(x for x, _, _, _ in rects)
            min_y = min(y for _, y, _, _ in rects)
            max_x = max(x + w for x, _, w, _ in rects)
            max_y = max(y + h for _, y, _, h in rects)
            return max_x - min_x, max_y - min_y
        if len(rects) == 1:
            _, _, w, h = rects[0]
            return w, h

    primary = profile.get("primary_screen") if isinstance(profile, dict) else None
    if isinstance(primary, dict):
        try:
            return int(primary.get("width", 0)), int(primary.get("height", 0))
        except (TypeError, ValueError):
            return None
    screens = profile.get("screens") if isinstance(profile, dict) else None
    if isinstance(screens, list) and screens:
        first = screens[0]
        if isinstance(first, dict):
            try:
                return int(first.get("width", 0)), int(first.get("height", 0))
            except (TypeError, ValueError):
                return None
    return None


def aspect_prompt_phrase(aspect_ratio: str) -> str:
    if aspect_ratio == "21:9":
        return "ultrawide/multi-monitor desktop overview around 21:9, composed across the full visible layout"
    if aspect_ratio == "4:3":
        return "classic 4:3 desktop overview"
    if aspect_ratio == "3:2":
        return "3:2 desktop overview"
    return "16:9 primary-monitor desktop overview"


def build_desktop_preview_prompt(direction: dict, aspect_ratio: str = "16:9") -> str:
    """Build the FAL prompt for a full desktop-theme concept image."""
    direction = direction or {}
    stance = direction.get("stance", direction.get("aesthetic", ""))
    mood_raw = direction.get("mood", direction.get("mood_tags", []))
    mood = " ".join(mood_raw) if isinstance(mood_raw, list) else str(mood_raw)
    anchor = direction.get("reference_anchor", "")
    grammar = direction.get("reference_grammar", {})
    grammar_text = json.dumps(grammar, ensure_ascii=False) if isinstance(grammar, dict) and grammar else str(grammar or "")
    name = direction.get("name_hypothesis", direction.get("name", ""))
    direction_json = json.dumps(direction, ensure_ascii=False, indent=2)

    target_phrase = aspect_prompt_phrase(aspect_ratio)

    return (
        f"Full Linux desktop theme concept preview for {name or anchor}. "
        f"Reference anchor: {anchor}. Reference grammar: {grammar_text}. Mood: {mood}. Aesthetic stance: {stance}. "
        f"Creative direction JSON: {direction_json}. "
        f"Target canvas: {target_phrase}. "
        "Generate one single representative overview image: a complete desktop screenshot-style overview that becomes the centerpiece of the design system. "
        "Fill the canvas edge-to-edge with the desktop overview; no cinematic letterbox bars, no black bands above or below, no framed movie-still presentation. "
        "Show the entire desktop UI as a coherent screenshot-style mockup: "
        "ornate window borders, themed terminal window, launcher/menu panel, "
        "top or bottom system panel, widget menus, icon style, wallpaper background, "
        "and custom application chrome all designed as one unified theme. "
        "Let the visual model invent bold desktop composition, original spatial hierarchy, strange but usable surfaces, "
        "signature chrome silhouettes, and theme-specific icon/menu language; avoid safe template layouts. "
        "The UI should be inspired by concrete fantasy RPG game-menu references while remaining a modern Linux desktop. "
        "Treat reference images as design-language inputs for surfaces, borders, icon silhouettes, menu hierarchy, materials, and mood — not as wallpaper candidates. "
        "Use carved frames, thorn-like ornamental borders, rune/glyph button silhouettes, "
        "emberlit materials, dark surfaces, layered panels, and high-contrast readable regions. "
        "Desktop overview, high originality, dense handcrafted detail, cohesive OS shell, "
        "readable UI labels where useful, terminal/menu/panel text affordances, original glyph marks and icon emblems, "
        "no copied proprietary logos or trademarks, no default desktop chrome, not a landscape-only painting, do not turn reference art into the wallpaper."
    )
