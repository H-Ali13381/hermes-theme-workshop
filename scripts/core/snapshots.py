"""Pre-flight state snapshots — read current desktop state BEFORE touching anything."""
import re

from core.constants import HOME
from core.process import _kread
from core.config_parsers import _read_kvantum_theme, _appletsrc_image


def snapshot_kde_state() -> dict[str, str | None]:
    """Read the currently active KDE colorscheme so we can restore it on undo."""
    scheme      = _kread("kdeglobals", "General", "ColorScheme")
    lookandfeel = _kread("kdeglobals", "KDE",     "LookAndFeelPackage")

    # Fallback: parse kdeglobals directly when kreadconfig isn't available or
    # the keys are absent (e.g. first-time run with no scheme applied yet).
    if not scheme or not lookandfeel:
        kdeglobals = HOME / ".config" / "kdeglobals"
        if kdeglobals.exists():
            text = kdeglobals.read_text(encoding="utf-8", errors="replace")
            if not scheme:
                sec = re.search(r"^\[General\](.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
                if sec:
                    m = re.search(r"^ColorScheme\s*=\s*(.+)$", sec.group(1), re.MULTILINE)
                    if m:
                        scheme = m.group(1).strip()
            if not lookandfeel:
                sec = re.search(r"^\[KDE\](.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
                if sec:
                    m = re.search(r"^LookAndFeelPackage\s*=\s*(.+)$", sec.group(1), re.MULTILINE)
                    if m:
                        lookandfeel = m.group(1).strip()

    kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
    kvantum_theme  = _read_kvantum_theme(kvantum_config) if kvantum_config.exists() else None

    wallpaper = None
    wallpaper_plugin = None
    appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
    if appletsrc.exists():
        _atext = appletsrc.read_text(encoding="utf-8", errors="replace")
        wallpaper = _appletsrc_image(_atext)
        _wp_m = re.search(r"^Wallpaperplugin\s*=\s*(.+)$", _atext, re.MULTILINE)
        wallpaper_plugin = _wp_m.group(1).strip() if _wp_m else None

    return {
        "active_colorscheme": scheme,
        "look_and_feel":      lookandfeel,
        "kvantum_theme":      kvantum_theme,
        "widget_style":       _kread("kdeglobals",   "KDE",   "widgetStyle"),
        "plasma_theme":       _kread("plasmarc",     "Theme", "name"),
        "cursor_theme":       _kread("kcminputrc",   "Mouse", "cursorTheme"),
        "icon_theme":         _kread("kdeglobals",   "Icons", "Theme"),
        "wallpaper":          wallpaper,
        "wallpaper_plugin":   wallpaper_plugin,
    }


def snapshot_konsole_state() -> dict[str, str | None]:
    """Read the currently active Konsole default profile."""
    profile = None
    konsolerc = HOME / ".config" / "konsolerc"
    if konsolerc.exists():
        text = konsolerc.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^DefaultProfile\s*=\s*(.+)", text, re.MULTILINE)
        if m:
            profile = m.group(1).strip()
    return {"default_profile": profile}
