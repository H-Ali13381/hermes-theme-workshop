"""KDE sub-system materializers: Kvantum, Plasma theme, cursor, icon theme, lock screen."""
import os
import re
from pathlib import Path

from core.constants import HOME
from core.colors import adjust_lightness, is_dark_palette
from core.process import run_cmd, cmd_exists, _get_kwrite, _kread
from core.backup import backup_file
from core.config_parsers import _read_kvantum_theme

# ---------------------------------------------------------------------------
# Kvantum theme generation helpers
# ---------------------------------------------------------------------------

# System directories that ship Kvantum base themes, in search order.
_KVANTUM_SYSTEM_DIRS: list[Path] = [
    Path("/usr/share/Kvantum"),
    Path("/usr/local/share/Kvantum"),
]

# Neutral dark base themes to try when generating an SVG, in preference order.
# Prefer bases with explicit menu assets; otherwise Qt context menus may fall
# back to generic/default-looking popup backgrounds even when global colors are
# palette-correct.
_PREFERRED_BASE_THEMES: list[str] = ["KvArcDark", "KvAdaptaDark", "KvFlat", "KvDark"]


def _find_base_svg() -> Path | None:
    """Return the path to a neutral dark SVG from an installed Kvantum theme, or None."""
    for theme_name in _PREFERRED_BASE_THEMES:
        for system_dir in _KVANTUM_SYSTEM_DIRS:
            candidate = system_dir / theme_name / f"{theme_name}.svg"
            if candidate.exists():
                return candidate
    return None


def _svg_color_map(palette: dict) -> dict[str, str]:
    """Map KvDark's neutral grey ladder to palette-derived equivalents.

    Keys are lowercase 6-digit hex strings (``#rrggbb``); values are the
    palette-derived replacement strings.  The mapping preserves the relative
    luminance ordering of the original greys.
    """
    bg  = palette["background"]
    srf = palette["surface"]
    mut = palette["muted"]
    pri = palette["primary"]
    sec = palette["secondary"]
    acc = palette["accent"]
    fg  = palette["foreground"]
    return {
        "#141414": adjust_lightness(bg,  0.55),  # near-black base
        "#191919": adjust_lightness(bg,  0.65),
        "#1e1e1e": bg,                            # main background
        "#323232": adjust_lightness(srf, 0.80),  # dark surface
        "#3c3c3c": srf,                           # surface
        "#5a5a5a": adjust_lightness(srf, 1.50),  # border / frame
        "#5e5e5e": adjust_lightness(srf, 1.50),
        "#646464": adjust_lightness(mut, 0.85),  # muted-ish
        "#787878": mut,                           # muted
        "#808080": mut,
        "#a0a0a0": adjust_lightness(mut, 1.30),  # lighter muted
        "#b2b2b2": adjust_lightness(mut, 1.60),
        "#cccccc": sec,                           # secondary accent
        "#d2d2d2": pri,                           # primary accent
        "#ffffff": fg,                            # foreground / white text
        # KvArc/KvAdapta accent colors. These bases include full menu assets,
        # but their non-grey blue/purple accents need explicit remapping.
        "#5294e2": pri,
        "#0582ff": pri,
        "#3176bf": adjust_lightness(pri, 0.75),
        "#4693e6": pri,
        "#58acff": adjust_lightness(pri, 1.20),
        "#b74aff": acc,
        "#4d5367": adjust_lightness(srf, 1.20),
        "#474d5d": srf,
        "#505666": adjust_lightness(srf, 1.30),
    }


def _build_gray_ladder(palette: dict) -> list[tuple[int, str]]:
    """Return a luminance-sorted list of (luma_0_255, replacement_hex) pairs.

    Used as a fallback after the explicit color map: any remaining neutral grey
    in the SVG (R≈G≈B) is mapped to the nearest entry by luminance, so every
    grey value in the source SVG gets palette-driven treatment regardless of
    whether it appears in the explicit map.
    """
    bg  = palette["background"]
    srf = palette["surface"]
    mut = palette["muted"]
    sec = palette["secondary"]
    pri = palette["primary"]
    fg  = palette["foreground"]
    ladder = [
        (0,   adjust_lightness(bg,  0.40)),
        (12,  adjust_lightness(bg,  0.55)),
        (22,  adjust_lightness(bg,  0.65)),
        (30,  bg),
        (40,  adjust_lightness(srf, 0.70)),
        (52,  adjust_lightness(srf, 0.85)),
        (62,  srf),
        (78,  adjust_lightness(srf, 1.20)),
        (88,  adjust_lightness(srf, 1.50)),
        (100, mut),
        (118, adjust_lightness(mut, 1.20)),
        (138, adjust_lightness(mut, 1.45)),
        (155, adjust_lightness(mut, 1.65)),
        (165, sec),
        (178, pri),
        (205, adjust_lightness(fg,  0.82)),
        (225, adjust_lightness(fg,  0.93)),
        (240, fg),
        (255, fg),
    ]
    return sorted(ladder, key=lambda t: t[0])


def _apply_svg_colors(svg_text: str, color_map: dict[str, str],
                      gray_ladder: list[tuple[int, str]] | None = None) -> str:
    """Apply hex color substitutions to SVG text.

    Pass 1 — explicit map: replaces all colors listed in *color_map*.  Processes
    longest keys first.  Also replaces ``#rgb`` 3-digit shorthand when the
    6-digit form has doubled digits (e.g. ``#ffffff`` → ``#fff``).

    Pass 2 — gray ladder (optional): after the explicit pass, any remaining
    hex color where the R, G and B channels are within 20 of each other (i.e. a
    neutral grey) is replaced by finding the nearest-luminance entry in
    *gray_ladder*.  This ensures every shade of grey in any base SVG gets
    palette-appropriate treatment without needing a hardcoded exhaustive list.
    """
    result = svg_text

    # Pass 1: explicit substitutions
    for old, new in sorted(color_map.items(), key=lambda kv: -len(kv[0])):
        result = re.sub(re.escape(old), new, result, flags=re.IGNORECASE)
        r, g, b = old[1:3], old[3:5], old[5:7]
        if r[0] == r[1] and g[0] == g[1] and b[0] == b[1]:
            short = f"#{r[0]}{g[0]}{b[0]}"
            result = re.sub(re.escape(short), new, result, flags=re.IGNORECASE)

    # Pass 2: dynamic grey mapping using the luminance ladder
    if gray_ladder:
        def _remap_gray(m: re.Match) -> str:
            hx = m.group(0).lstrip("#").lower()
            if len(hx) == 3:
                hx = hx[0] * 2 + hx[1] * 2 + hx[2] * 2
            rv, gv, bv = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
            if max(rv, gv, bv) - min(rv, gv, bv) > 20:
                return m.group(0)  # not a neutral grey — leave it
            luma = (rv * 299 + gv * 587 + bv * 114) // 1000
            best = min(gray_ladder, key=lambda t: abs(t[0] - luma))
            return best[1]

        result = re.sub(
            r"#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}(?![0-9a-fA-F])",
            _remap_gray, result, flags=re.IGNORECASE,
        )

    return result


def _build_hermes_kvconfig(theme_name: str, palette: dict) -> str:
    """Return the text content of a Kvantum .kvconfig that follows the palette."""
    bg      = palette["background"]
    srf     = palette["surface"]
    fg      = palette["foreground"]
    pri     = palette["primary"]
    acc     = palette["accent"]
    mut     = palette["muted"]
    danger  = palette["danger"]
    dark_bg = adjust_lightness(bg, 0.50)   # deeper than background for inputs
    light_bg = adjust_lightness(bg, 1.40)  # raised surface for pressed buttons

    return (
        f"[%General]\n"
        f"author=hermes\n"
        f"comment=Auto-generated from hermes palette\n"
        f"x11drag=all\n"
        f"alt_mnemonic=true\n"
        f"left_tabs=true\n"
        f"attach_active_tab=true\n"
        f"mirror_doc_tabs=true\n"
        f"scroll_width=8\n"
        f"scroll_min_extent=36\n"
        f"transient_scrollbar=true\n"
        f"menu_shadow_depth=6\n"
        f"tooltip_shadow_depth=4\n"
        f"spread_menuitems=false\n"
        f"composite=true\n"
        f"blurring=true\n"
        f"popup_blurring=true\n"
        f"reduce_window_opacity=10\n"
        f"reduce_menu_opacity=5\n"
        f"shadowless_popup=false\n"
        f"\n"
        f"[GeneralColors]\n"
        f"window.color={bg}\n"
        f"base.color={dark_bg}\n"
        f"alt.base.color={srf}\n"
        f"button.color={srf}\n"
        f"light.color={light_bg}\n"
        f"mid.light.color={adjust_lightness(srf, 1.20)}\n"
        f"dark.color={adjust_lightness(bg, 0.75)}\n"
        f"mid.color={adjust_lightness(bg, 0.85)}\n"
        f"highlight.color={acc}\n"
        f"inactive.highlight.color={adjust_lightness(acc, 0.70)}\n"
        f"text.color={fg}\n"
        f"window.text.color={fg}\n"
        f"button.text.color={fg}\n"
        f"disabled.text.color={mut}\n"
        f"tooltip.text.color={fg}\n"
        f"tooltip.base.color={adjust_lightness(srf, 0.80)}\n"
        f"highlight.text.color={bg}\n"
        f"link.color={pri}\n"
        f"link.visited.color={danger}\n"
        f"progress.indicator.text.color={bg}\n"
        f"\n"
        f"[PanelButtonCommand]\n"
        f"frame=true\n"
        f"frame.element=button\n"
        f"interior.element=button\n"
        f"text.normal.color={fg}\n"
        f"text.focus.color={fg}\n"
        f"text.press.color={bg}\n"
        f"text.toggle.color={bg}\n"
        f"text.shadow=false\n"
        f"\n"
        f"[Menu]\n"
        f"inherits=PanelButtonCommand\n"
        f"frame.element=menu\n"
        f"interior.element=menu\n"
        f"text.normal.color={fg}\n"
        f"text.focus.color={fg}\n"
        f"text.press.color={bg}\n"
        f"text.toggle.color={bg}\n"
        f"text.bold=false\n"
        f"text.shadow=false\n"
        f"frame.top=3\n"
        f"frame.bottom=3\n"
        f"frame.left=3\n"
        f"frame.right=3\n"
        f"\n"
        f"[MenuItem]\n"
        f"inherits=PanelButtonCommand\n"
        f"frame=true\n"
        f"frame.element=menuitem\n"
        f"interior.element=menuitem\n"
        f"indicator.element=menuitem\n"
        f"indicator.size=8\n"
        f"text.normal.color={fg}\n"
        f"text.focus.color={bg}\n"
        f"text.press.color={bg}\n"
        f"text.toggle.color={bg}\n"
        f"text.margin.left=10\n"
        f"text.margin.right=8\n"
        f"text.margin.top=2\n"
        f"text.margin.bottom=2\n"
        f"frame.top=3\n"
        f"frame.bottom=3\n"
        f"frame.left=3\n"
        f"frame.right=3\n"
        f"\n"
        f"[MenuBar]\n"
        f"inherits=PanelButtonCommand\n"
        f"frame.element=menubar\n"
        f"interior.element=menubar\n"
        f"text.normal.color={fg}\n"
        f"text.focus.color={fg}\n"
        f"\n"
        f"[MenuBarItem]\n"
        f"inherits=PanelButtonCommand\n"
        f"interior.element=menubaritem\n"
        f"frame.element=menubaritem\n"
        f"text.normal.color={fg}\n"
        f"text.focus.color={bg}\n"
        f"text.press.color={bg}\n"
        f"text.toggle.color={bg}\n"
        f"text.margin.left=5\n"
        f"text.margin.right=5\n"
        f"text.margin.top=3\n"
        f"text.margin.bottom=3\n"
        f"\n"
        f"[Hacks]\n"
        f"respect_darkness=true\n"
        f"transparent_ktitlewidget=true\n"
        f"kcapacitybar_as_progressbar=true\n"
        f"blur_konsole=true\n"
    )


def _ensure_hermes_theme(theme_name: str, palette: dict, kvantum_dir: Path) -> dict:
    """Create or refresh a hermes-* Kvantum theme directory from the palette.

    Returns a dict with generation metadata suitable for merging into a change
    record: ``{"generated": bool, "base_svg": str | None, "theme_dir": str}``.
    """
    theme_dir = kvantum_dir / theme_name
    theme_dir.mkdir(parents=True, exist_ok=True)

    # --- kvconfig ---
    kvconfig_path = theme_dir / f"{theme_name}.kvconfig"
    kvconfig_path.write_text(_build_hermes_kvconfig(theme_name, palette), encoding="utf-8")

    # --- SVG ---
    base_svg_path = _find_base_svg()
    svg_path = theme_dir / f"{theme_name}.svg"
    generated_svg = False
    if base_svg_path is not None:
        svg_text = base_svg_path.read_text(encoding="utf-8")
        color_map = _svg_color_map(palette)
        gray_ladder = _build_gray_ladder(palette)
        svg_text = _apply_svg_colors(svg_text, color_map, gray_ladder)
        svg_path.write_text(svg_text, encoding="utf-8")
        generated_svg = True

    return {
        "generated": True,
        "generated_svg": generated_svg,
        "base_svg": str(base_svg_path) if base_svg_path else None,
        "theme_dir": str(theme_dir),
    }


# Optional icon theme generator
icon_theme_gen = None
try:
    import icon_theme_gen  # type: ignore[import]
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Kvantum
# ---------------------------------------------------------------------------

# Standard locations where distros install the Kvantum Qt style plugin.
_KVANTUM_PLUGIN_PATHS: list[Path] = [
    Path("/usr/lib/qt6/plugins/styles/libkvantum.so"),
    Path("/usr/lib/qt/plugins/styles/libkvantum.so"),
    Path("/usr/lib64/qt6/plugins/styles/libkvantum.so"),
    Path("/usr/local/lib/qt6/plugins/styles/libkvantum.so"),
]


def _kvantum_plugin_exists() -> bool:
    """Return True if the Kvantum Qt style plugin is installed on this system.

    Checks the plugin ``.so`` directly — never invokes ``kvantummanager``
    (the GUI application) which would open a window.
    """
    return any(p.exists() for p in _KVANTUM_PLUGIN_PATHS)


def materialize_kvantum(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set Kvantum widget style and theme.

    When *kvantum_theme* starts with ``hermes-`` and a ``palette`` is present in
    *design*, the theme files are generated from the palette automatically so the
    theme is reproducible on any machine regardless of which Kvantum packages are
    installed.
    """
    changes = []
    kvantum_dir = HOME / ".config" / "Kvantum"
    kvantum_config = kvantum_dir / "kvantum.kvconfig"

    kvantum_theme = design.get("kvantum_theme")
    if not kvantum_theme:
        return []

    palette = design.get("palette") or {}
    is_hermes = kvantum_theme.startswith("hermes-") and bool(palette)

    if dry_run:
        changes.append({
            "app": "kvantum", "action": "dry-run",
            "theme": kvantum_theme, "config_path": str(kvantum_config),
            "will_generate": is_hermes,
        })
        return changes

    prev_kvantum_theme = _read_kvantum_theme(kvantum_config) if kvantum_config.exists() else None
    prev_widget_style = _kread("kdeglobals", "KDE", "widgetStyle")

    # Generate theme files from palette when the theme name uses the hermes- prefix.
    gen_info: dict = {}
    if is_hermes:
        kvantum_dir.mkdir(parents=True, exist_ok=True)
        gen_info = _ensure_hermes_theme(kvantum_theme, palette, kvantum_dir)

    kvantum_backup = backup_file(kvantum_config, backup_ts, "kvantum/kvantum.kvconfig")
    kvantum_dir.mkdir(parents=True, exist_ok=True)
    kvantum_config.write_text(f"[General]\ntheme={kvantum_theme}\n", encoding="utf-8")

    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", "kvantum"])

    if cmd_exists("qdbus6"):
        run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)

    changes.append({
        "app": "kvantum", "action": "write",
        "theme": kvantum_theme, "config_path": str(kvantum_config),
        "backup": kvantum_backup,
        "previous_kvantum_theme": prev_kvantum_theme,
        "previous_widget_style": prev_widget_style,
        **gen_info,
    })
    return changes


# ---------------------------------------------------------------------------
# Plasma theme
# ---------------------------------------------------------------------------

def materialize_plasma_theme(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the Plasma desktop theme (panel SVGs, task buttons, etc.)."""
    changes = []
    plasma_theme = design.get("plasma_theme")
    if not plasma_theme:
        return changes

    plasmarc = HOME / ".config" / "plasmarc"
    if dry_run:
        changes.append({"app": "plasma_theme", "action": "dry-run", "theme": plasma_theme, "config_path": str(plasmarc)})
        return changes

    prev_theme = _kread("plasmarc", "Theme", "name")

    plasmarc_backup = backup_file(plasmarc, backup_ts, "plasma/plasmarc")
    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "plasmarc", "--group", "Theme", "--key", "name", plasma_theme])
    if cmd_exists("plasma-apply-desktoptheme"):
        run_cmd(["plasma-apply-desktoptheme", plasma_theme])

    changes.append({"app": "plasma_theme", "action": "write", "theme": plasma_theme,
                    "config_path": str(plasmarc), "backup": plasmarc_backup, "previous_theme": prev_theme})
    return changes


# ---------------------------------------------------------------------------
# Cursor
# ---------------------------------------------------------------------------

def materialize_cursor(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the cursor theme.

    Writes the theme to every consumer surface so KDE, GTK, and XCursor-aware
    Wayland/X11 clients all agree:
      - ``kcminputrc[Mouse].cursorTheme``      (KDE settings module)
      - ``kdeglobals[General].cursorTheme``    (Plasma shell, kwin_wayland)
      - ``~/.icons/default/index.theme``       (libXcursor inheritance)
      - ``gsettings org.gnome.desktop.interface cursor-theme`` (GTK / XDG portal)

    Defeats Plasma's "already set" cache by toggling to ``breeze_cursors`` first
    when ``plasma-apply-cursortheme`` reports the requested theme is current.
    Note: on Wayland, already-running clients keep their cached cursor until
    relaunch; this is a compositor limitation, not a config issue.
    """
    changes = []
    cursor_theme = design.get("cursor_theme")
    if not cursor_theme:
        return changes

    kcminputrc = HOME / ".config" / "kcminputrc"
    kdeglobals = HOME / ".config" / "kdeglobals"
    icons_default = HOME / ".icons" / "default" / "index.theme"

    if dry_run:
        changes.append({"app": "cursor", "action": "dry-run", "theme": cursor_theme, "config_path": str(kcminputrc)})
        return changes

    prev_cursor = _kread("kcminputrc", "Mouse", "cursorTheme")

    cursor_backup = backup_file(kcminputrc, backup_ts, "cursor/kcminputrc")
    kdeglobals_backup = backup_file(kdeglobals, backup_ts, "cursor/kdeglobals")
    icons_default_backup = backup_file(icons_default, backup_ts, "cursor/icons-default-index.theme")

    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", cursor_theme])
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "General", "--key", "cursorTheme", cursor_theme])

    icons_default.parent.mkdir(parents=True, exist_ok=True)
    icons_default.write_text(
        f"[Icon Theme]\nName=Default\nComment=Default Cursor Theme\nInherits={cursor_theme}\n",
        encoding="utf-8",
    )

    if cmd_exists("gsettings"):
        run_cmd(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", cursor_theme], timeout=5)

    if cmd_exists("plasma-apply-cursortheme"):
        rc_pre, out_pre, err_pre = run_cmd(["plasma-apply-cursortheme", cursor_theme], timeout=10)
        if "already set" in (out_pre or "") or "already set" in (err_pre or ""):
            kick = "breeze_cursors" if cursor_theme != "breeze_cursors" else "Adwaita"
            run_cmd(["plasma-apply-cursortheme", kick], timeout=5)
            run_cmd(["plasma-apply-cursortheme", cursor_theme], timeout=10)

    # Force kwin to re-read cursor theme so already-running Wayland clients
    # refresh in place rather than waiting for relaunch.
    if cmd_exists("qdbus6"):
        run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)
    if cmd_exists("gdbus"):
        run_cmd(["gdbus", "emit", "--session", "--object-path", "/KGlobalSettings",
                 "--signal", "org.kde.KGlobalSettings.notifyChange", "5", "0"], timeout=5)

    changes.append({"app": "cursor", "action": "write", "theme": cursor_theme,
                    "config_path": str(kcminputrc), "backup": cursor_backup,
                    "kdeglobals_backup": kdeglobals_backup,
                    "icons_default_backup": icons_default_backup,
                    "previous_cursor": prev_cursor})
    return changes


# ---------------------------------------------------------------------------
# Icon theme
# ---------------------------------------------------------------------------

def materialize_icon_theme(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the KDE icon theme, generating one via recolor or fal.ai if not installed."""
    changes = []
    icon_theme = design.get("icon_theme")
    if not icon_theme:
        return changes

    if dry_run:
        changes.append({"app": "icon_theme", "action": "dry-run", "theme": icon_theme, "generated": False,
                        "papirus_folder_color": design.get("papirus_folder_color")})
        return changes

    generated = False
    if icon_theme_gen is not None and not icon_theme_gen.is_installed(icon_theme):
        palette = design.get("palette", {})
        is_dark = is_dark_palette(palette)
        base = "breeze-dark" if is_dark else "breeze"
        new_theme = icon_theme_gen.create_palette_icon_theme(design, base_theme=base)
        if new_theme:
            icon_theme = new_theme
            generated = True
            changes.append({"app": "icon_theme", "action": "generated-recolor", "base_theme": base, "theme": icon_theme})
        else:
            fal_key = os.environ.get("FAL_KEY", "").strip()
            if fal_key:
                theme_name = f"{design.get('name', 'rice')}-icons"
                icon_dir = HOME / ".local" / "share" / "icons" / theme_name / "apps"
                ok = icon_theme_gen.generate_icon_via_fal(design, fal_key, icon_dir)
                if ok:
                    out_root = HOME / ".local" / "share" / "icons" / theme_name
                    icon_theme_gen._write_index_theme(
                        out_root, theme_name, f"{base},hicolor",
                        [s for s in (22, 48) if (icon_dir / str(s)).exists()],
                    )
                    icon_theme_gen._update_icon_cache(out_root)
                    icon_theme = theme_name
                    generated = True
                    changes.append({"app": "icon_theme", "action": "generated-fal", "theme": icon_theme})

    prev_icon_theme = _kread("kdeglobals", "Icons", "Theme")

    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", icon_theme])
    if cmd_exists("qdbus6"):
        run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)

    # Apply Papirus folder color if requested and the theme is Papirus-based.
    papirus_folder_color = design.get("papirus_folder_color")
    if papirus_folder_color and icon_theme.lower().startswith("papirus") and cmd_exists("papirus-folders"):
        rc, _, _ = run_cmd(["papirus-folders", "-C", papirus_folder_color, "--theme", icon_theme])
        changes.append({"app": "icon_theme", "action": "papirus-folders",
                        "color": papirus_folder_color, "success": rc == 0})

    changes.append({"app": "icon_theme", "action": "write", "theme": icon_theme,
                    "generated": generated, "previous_icon_theme": prev_icon_theme})
    return changes


# ---------------------------------------------------------------------------
# Look and Feel (Global Theme)
# ---------------------------------------------------------------------------

import json as _json


def _lnf_id(design: dict) -> str:
    """Return the Look-and-Feel package ID for this design."""
    return f"hermes-{design.get('name', 'ricer')}.desktop"


def _build_lnf_package(lnf_id: str, design: dict, lnf_root: Path) -> None:
    """Write the minimal Look-and-Feel package files to *lnf_root*."""
    colorscheme_name = f"hermes-{design.get('name', 'ricer')}"
    palette = design.get("palette", {})
    icon_theme = design.get("icon_theme", "breeze-dark" if is_dark_palette(palette) else "breeze")
    cursor_theme = design.get("cursor_theme", "breeze_cursors")
    plasma_theme = design.get("plasma_theme", "default")
    kvantum_theme = design.get("kvantum_theme", "")

    # Decide widget style: use kvantum when a kvantum_theme is specified and
    # the Kvantum Qt style plugin (.so) is installed.  We check the plugin
    # directly rather than kvantummanager, which is the GUI application and
    # must never be invoked as it pops up a window.
    widget_style = "kvantum" if kvantum_theme and _kvantum_plugin_exists() else "Breeze"

    metadata = {
        "KPackageStructure": "Plasma/LookAndFeel",
        "KPlugin": {
            "Authors": [{"Name": "Hermes Ricer"}],
            "Description": f"Hermes generated theme: {design.get('name', 'ricer')}",
            "Id": lnf_id,
            "License": "MIT",
            "Name": colorscheme_name,
            "Website": "",
        },
    }

    defaults_content = (
        f"[kdeglobals][KDE]\n"
        f"widgetStyle={widget_style}\n"
        f"\n"
        f"[kdeglobals][General]\n"
        f"ColorScheme={colorscheme_name}\n"
        f"\n"
        f"[kdeglobals][Icons]\n"
        f"Theme={icon_theme}\n"
        f"\n"
        f"[plasmarc][Theme]\n"
        f"name={plasma_theme}\n"
        f"\n"
        f"[kcminputrc][Mouse]\n"
        f"cursorTheme={cursor_theme}\n"
        f"\n"
        f"[kwinrc][org.kde.kdecoration2]\n"
        f"library=org.kde.breeze\n"
        f"theme=Breeze\n"
    )

    contents_dir = lnf_root / "contents"
    contents_dir.mkdir(parents=True, exist_ok=True)

    (lnf_root / "metadata.json").write_text(_json.dumps(metadata, indent=4), encoding="utf-8")
    (contents_dir / "defaults").write_text(defaults_content, encoding="utf-8")


def materialize_lnf(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Generate and apply a hermes Look-and-Feel package.

    Creates ``~/.local/share/plasma/look-and-feel/<id>/`` with a ``metadata.json``
    and ``contents/defaults`` that set ``widgetStyle``, ``ColorScheme``, icons,
    cursor, and plasma theme.  Applies it via ``plasma-apply-lookandfeel``.
    """
    changes = []
    lnf_id = _lnf_id(design)
    lnf_root = HOME / ".local" / "share" / "plasma" / "look-and-feel" / lnf_id

    if dry_run:
        changes.append({
            "app": "lnf", "action": "dry-run",
            "lnf_id": lnf_id, "lnf_path": str(lnf_root),
        })
        return changes

    prev_lnf = _kread("kdeglobals", "KDE", "LookAndFeelPackage")

    _build_lnf_package(lnf_id, design, lnf_root)

    if cmd_exists("plasma-apply-lookandfeel"):
        rc, out, err = run_cmd(["plasma-apply-lookandfeel", "--apply", lnf_id], timeout=30)
    else:
        rc, out, err = 1, "", "plasma-apply-lookandfeel not found"

    # plasma-apply-lookandfeel writes through the KConfig D-Bus layer and may not
    # flush widgetStyle to the on-disk kdeglobals immediately.  Explicitly persist
    # it via kwriteconfig6 so that plasmashell reads the correct value at startup.
    kvantum_theme = design.get("kvantum_theme", "")
    widget_style = "kvantum" if kvantum_theme and _kvantum_plugin_exists() else "Breeze"
    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", widget_style])

    changes.append({
        "app": "lnf", "action": "write",
        "lnf_id": lnf_id, "lnf_path": str(lnf_root),
        "previous_lnf": prev_lnf,
        "apply_exit_code": rc,
        "widget_style": widget_style,
    })
    return changes


# ---------------------------------------------------------------------------
# KDE lock screen
# ---------------------------------------------------------------------------

def _lockscreen_lnf_for_palette(palette: dict) -> str:
    """Return breezedark or breeze LnF ID based on palette background brightness."""
    return "org.kde.breezedark.desktop" if is_dark_palette(palette) else "org.kde.breeze.desktop"


def _resolve_lockscreen_wallpaper(design: dict) -> str | None:
    """Return an absolute filesystem path for the lock-screen wallpaper, or None.

    Resolution order:
      1. ``design["lockscreen_wallpaper"]`` (explicit override)
      2. ``design["wallpaper"]`` (reuse desktop wallpaper)
      3. Current live desktop wallpaper (via wallpaper materializer's snapshot)
    """
    for key in ("lockscreen_wallpaper", "wallpaper"):
        val = design.get(key)
        if val:
            return str(val)
    try:
        from materializers.wallpaper import _snapshot_current_wallpaper
        from desktop_utils import discover_desktop
        path, _method = _snapshot_current_wallpaper(discover_desktop())
        return path
    except Exception:
        return None


def materialize_kde_lockscreen(design: dict, backup_ts: str, dry_run: bool = False) -> list[dict]:
    """Set the kscreenlocker greeter LnF and wallpaper to match the rice."""
    palette = design["palette"]
    kscreenlockerrc = HOME / ".config" / "kscreenlockerrc"
    changes = []

    greeter_theme = _lockscreen_lnf_for_palette(palette)
    wallpaper_path = _resolve_lockscreen_wallpaper(design)
    fill_mode = str(design.get("lockscreen_fill_mode", design.get("wallpaper_fill_mode", 2)))

    if dry_run:
        changes.append({"app": "kde_lockscreen", "action": "dry-run",
                        "greeter_theme": greeter_theme, "config_path": str(kscreenlockerrc),
                        "wallpaper": wallpaper_path, "fill_mode": fill_mode})
        return changes

    prev_theme = _kread("kscreenlockerrc", "Greeter", "Theme")
    prev_wallpaper = _kread("kscreenlockerrc", "Greeter][Wallpaper][org.kde.image][General",
                            "Image")

    kscreenlockerrc_backup = backup_file(kscreenlockerrc, backup_ts, "kscreenlocker/kscreenlockerrc")
    kwrite = _get_kwrite()
    if kwrite:
        run_cmd([kwrite, "--file", "kscreenlockerrc", "--group", "Greeter",
                 "--key", "Theme", greeter_theme])
        if wallpaper_path:
            wp_uri = wallpaper_path if wallpaper_path.startswith("file://") else f"file://{wallpaper_path}"
            run_cmd([kwrite, "--file", "kscreenlockerrc", "--group", "Greeter",
                     "--key", "WallpaperPlugin", "org.kde.image"])
            run_cmd([kwrite, "--file", "kscreenlockerrc",
                     "--group", "Greeter", "--group", "Wallpaper",
                     "--group", "org.kde.image", "--group", "General",
                     "--key", "Image", wp_uri])
            run_cmd([kwrite, "--file", "kscreenlockerrc",
                     "--group", "Greeter", "--group", "Wallpaper",
                     "--group", "org.kde.image", "--group", "General",
                     "--key", "FillMode", fill_mode])

    changes.append({"app": "kde_lockscreen", "action": "write",
                    "greeter_theme": greeter_theme, "config_path": str(kscreenlockerrc),
                    "backup": kscreenlockerrc_backup, "previous_theme": prev_theme,
                    "wallpaper": wallpaper_path, "previous_wallpaper": prev_wallpaper,
                    "fill_mode": fill_mode})
    return changes
