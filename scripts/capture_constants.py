"""capture_constants.py — Shared constants for the capture_theme_references system.

Extracted from scripts/capture_theme_references.py to allow helper modules to
share the same canonical values without circular imports.
"""
from pathlib import Path

HOME = Path.home()
SKILL_DIR = Path(__file__).resolve().parent.parent
CATALOG_DIR = SKILL_DIR / "assets" / "catalog"
CACHE_DIR = HOME / ".cache" / "linux-ricing" / "capture_theme_references"
REFERENCE_WINDOW_SCRIPT = SKILL_DIR / "scripts" / "reference_capture_window.py"
DESKTOP_DIR = HOME / "Desktop"

KDE_CAPTURE_BASELINE = {
    "colorscheme": "BreezeDark",
    "look_and_feel": "org.kde.breezedark.desktop",
    "plasma_theme": "default",
    "cursor_theme": "breeze_cursors",
    "icon_theme": "breeze-dark",
    "widget_style": "Breeze",
    "wallpaper": "/usr/share/wallpapers/Next/contents/images_dark/5120x2880.png",
    "capture_output": "DP-1",
}

DEFAULT_KVANTUM_OPTIONS = [
    "catppuccin-mocha-teal",
    "catppuccin-mocha-mauve",
    "catppuccin-mocha-peach",
    "catppuccin-mocha-yellow",
]

DEFAULT_CURSOR_OPTIONS = [
    "catppuccin-macchiato-teal-cursors",
    "catppuccin-macchiato-mauve-cursors",
    "catppuccin-macchiato-yellow-cursors",
    "catppuccin-macchiato-red-cursors",
]

REFERENCE_PANEL_LAUNCHERS = (
    "applications:firefox.desktop,"
    "applications:org.kde.dolphin.desktop,"
    "applications:systemsettings.desktop,"
    "applications:org.kde.discover.desktop,"
    "applications:org.kde.konsole.desktop"
)

REFERENCE_PANEL_APPS = ["Firefox", "Dolphin", "System Settings", "Discover", "Konsole"]

REFERENCE_DESKTOP_ITEMS = [
    "Home.desktop", "Trash.desktop", "Firefox.desktop",
    "Dolphin.desktop", "System Settings.desktop", "Discover.desktop",
]

REFERENCE_DESKTOP_SHORTCUTS = {
    "Home.desktop":           {"Name": "Home",           "Icon": "user-home",          "Type": "Link",        "URL": f"file://{HOME}"},
    "Trash.desktop":          {"Name": "Trash",          "Icon": "user-trash",         "Type": "Link",        "URL": "trash:/"},
    "Firefox.desktop":        {"Name": "Firefox",        "Icon": "firefox",            "Type": "Application", "Exec": "firefox"},
    "Dolphin.desktop":        {"Name": "Dolphin",        "Icon": "system-file-manager","Type": "Application", "Exec": "dolphin"},
    "System Settings.desktop":{"Name": "System Settings","Icon": "preferences-system", "Type": "Application", "Exec": "systemsettings"},
    "Discover.desktop":       {"Name": "Discover",       "Icon": "plasmadiscover",     "Type": "Application", "Exec": "plasma-discover"},
}

SCENE_NOTES = """Reference baseline intent:
- Breeze Dark colorscheme
- default Plasma theme
- Breeze cursor and Breeze dark icons
- standard KDE wallpaper
- simplified panel launchers representing a basic KDE PC
- showcase standard app icons in the panel and on the desktop
- desktop kept on a neutral default-like state while captures focus on the active reference window
- capture uses active reference window instead of whole-screen shot
"""
