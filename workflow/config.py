from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
SESSIONS_DIR = Path.home() / ".config" / "rice-sessions"
DB_PATH = str(Path.home() / ".local" / "share" / "linux-ricing" / "sessions.sqlite")
MODEL = "claude-sonnet-4-6"

PALETTE_SLOTS = [
    "background", "foreground", "primary", "secondary",
    "accent", "surface", "muted", "danger", "success", "warning",
]
DESIGN_REQUIRED_KEYS = [
    "name", "description", "palette", "kvantum_theme",
    "cursor_theme", "icon_theme", "gtk_theme", "mood_tags",
]
ELEMENT_QUEUE_DEFAULT = [
    "terminal", "bar", "launcher", "notifications",
    "window_decorations", "gtk_theme", "wallpaper",
    "lock_screen", "shell_prompt", "fastfetch",
    "cursor_icons",
]
SCORE_PASS_THRESHOLD = 8
