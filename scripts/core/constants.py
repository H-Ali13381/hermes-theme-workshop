"""Shared path constants and design-system schema used across all ricer modules."""
from pathlib import Path
import sys

# ---------------------------------------------------------------------------
# PLATFORM GUARD
# ---------------------------------------------------------------------------

_PLATFORM_NAMES = {
    "darwin": "macOS",
    "win32": "Windows",
    "cygwin": "Windows (Cygwin)",
    "msys": "Windows (MSYS2)",
    "android": "Android",
    "ios": "iOS",
    "freebsd": "FreeBSD",
}


def require_linux() -> None:
    """Exit immediately with a clear message on non-Linux platforms.

    Call this at the top of every user-facing entry point (ricer.py,
    session_manager.py, workflow/run.py) so Windows/macOS users get an
    explanation instead of cryptic import errors or missing-file tracebacks.
    """
    if sys.platform.startswith("linux"):
        return
    # Exact match first, then prefix match (handles e.g. 'freebsd13').
    os_name = _PLATFORM_NAMES.get(sys.platform)
    if os_name is None:
        for prefix, name in _PLATFORM_NAMES.items():
            if sys.platform.startswith(prefix):
                os_name = name
                break
        else:
            os_name = sys.platform
    print(
        f"ERROR: linux-ricing requires a Linux desktop environment.\n"
        f"Detected platform: {os_name}\n\n"
        f"This skill customises Linux window managers (KDE Plasma, GNOME,\n"
        f"Hyprland) and depends on Linux-specific tools and config paths.\n"
        f"It cannot run on {os_name}.",
        file=sys.stderr,
    )
    sys.exit(1)

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
