"""Shared path constants and design-system schema used across all ricer modules."""
from pathlib import Path
import sys

# Resolve to scripts/ regardless of how this module is imported (symlink-safe).
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # scripts/core/ -> scripts/
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

HOME = Path.home()
CACHE_DIR = HOME / ".cache" / "linux-ricing"
BACKUP_DIR = CACHE_DIR / "backups"
CURRENT_DIR = CACHE_DIR / "current"
SKILL_DIR = _SCRIPTS_DIR.parent  # scripts/ -> skill root
TEMPLATES_DIR = SKILL_DIR / "templates"

# ---------------------------------------------------------------------------
# DESIGN SYSTEM SCHEMA
# ---------------------------------------------------------------------------

REQUIRED_PALETTE_KEYS = [
    "background", "foreground", "primary", "secondary", "accent",
    "surface", "muted", "danger", "success", "warning",
]

DEFAULT_DESIGN_SYSTEM = {
    "name": "default",
    "description": "A subtle dark theme with blue accents.",
    "palette": {
        "background": "#1e1e2e",
        "foreground": "#cdd6f4",
        "primary": "#89b4fa",
        "secondary": "#f5c2e7",
        "accent": "#fab387",
        "surface": "#313244",
        "muted": "#6c7086",
        "danger": "#f38ba8",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
    },
    "kvantum_theme": "catppuccin-mocha-blue",
    "cursor_theme": "catppuccin-macchiato-blue-cursors",
    "icon_theme": "Papirus-Dark",
    "gtk_theme": "Adwaita-dark",
    "mood_tags": ["dark", "blue", "subtle"],
    "typography": {"monospace": "JetBrainsMono Nerd Font", "ui_font": "Inter"},
}
