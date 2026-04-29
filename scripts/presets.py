"""scripts/presets.py — Built-in design presets for Hermes Ricer.

Each preset is a fully-specified design dict ready to pass to materialize().
"""

PRESETS: dict[str, dict] = {
    "catppuccin-mocha": {
        "name": "catppuccin-mocha",
        "description": "Soothing pastel dark theme.",
        "palette": {
            "background": "#1e1e2e", "foreground": "#cdd6f4", "primary": "#89b4fa",
            "secondary": "#f5c2e7", "accent": "#fab387", "surface": "#313244",
            "muted": "#6c7086", "danger": "#f38ba8", "success": "#a6e3a1", "warning": "#f9e2af",
        },
        "kvantum_theme": "catppuccin-mocha-blue",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-blue-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["pastel", "dark", "cozy"],
    },
    "nord": {
        "name": "nord",
        "description": "Arctic, north-bluish color palette.",
        "palette": {
            "background": "#2e3440", "foreground": "#d8dee9", "primary": "#88c0d0",
            "secondary": "#81a1c1", "accent": "#ebcb8b", "surface": "#3b4252",
            "muted": "#4c566a", "danger": "#bf616a", "success": "#a3be8c", "warning": "#ebcb8b",
        },
        # Nord primary is a teal-blue; catppuccin-mocha-teal is the closest Kvantum match.
        "kvantum_theme": "catppuccin-mocha-teal",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-teal-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["arctic", "blue", "flat"],
    },
    "gruvbox-dark": {
        "name": "gruvbox-dark",
        "description": "Retro groove dark colors.",
        "palette": {
            "background": "#282828", "foreground": "#ebdbb2", "primary": "#458588",
            "secondary": "#b16286", "accent": "#d79921", "surface": "#3c3836",
            "muted": "#928374", "danger": "#cc241d", "success": "#98971a", "warning": "#d79921",
        },
        # KvDark: neutral fallback; no Kvantum theme closely matches gruvbox warm tones.
        "kvantum_theme": "KvDark",
        "plasma_theme": "default",
        "cursor_theme": "Adwaita",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["retro", "warm", "sepia"],
    },
    "dracula": {
        "name": "dracula",
        "description": "Dark theme with vibrant colors.",
        "palette": {
            "background": "#282a36", "foreground": "#f8f8f2", "primary": "#bd93f9",
            "secondary": "#ff79c6", "accent": "#ffb86c", "surface": "#44475a",
            "muted": "#6272a4", "danger": "#ff5555", "success": "#50fa7b", "warning": "#f1fa8c",
        },
        "kvantum_theme": "catppuccin-mocha-mauve",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-mauve-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["dark", "neon", "purple"],
    },
    "tokyo-night": {
        "name": "tokyo-night",
        "description": "A dark and clean theme inspired by the lights of Tokyo at night.",
        "palette": {
            "background": "#1a1b26", "foreground": "#a9b1d6", "primary": "#7aa2f7",
            "secondary": "#bb9af7", "accent": "#ff9e64", "surface": "#24283b",
            "muted": "#565f89", "danger": "#f7768e", "success": "#9ece6a", "warning": "#e0af68",
        },
        "kvantum_theme": "catppuccin-mocha-blue",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-blue-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["cyberpunk", "blue", "neon"],
    },
    "rose-pine": {
        "name": "rose-pine",
        "description": "All natural pine, faux fur and a bit of soho vibes.",
        "palette": {
            "background": "#191724", "foreground": "#e0def4", "primary": "#9ccfd8",
            "secondary": "#f6c177", "accent": "#ebbcba", "surface": "#1f1d2e",
            "muted": "#6e6a86", "danger": "#eb6f92", "success": "#31748f", "warning": "#f6c177",
        },
        # Primary is a soft teal; catppuccin-mocha-teal is the closest available accent.
        "kvantum_theme": "catppuccin-mocha-teal",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-teal-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["soft", "pastel", "nature"],
    },
    "solarized-dark": {
        "name": "solarized-dark",
        "description": "Precision colors for machines and people.",
        "palette": {
            "background": "#002b36", "foreground": "#839496", "primary": "#268bd2",
            "secondary": "#2aa198", "accent": "#b58900", "surface": "#073642",
            "muted": "#586e75", "danger": "#dc322f", "success": "#859900", "warning": "#b58900",
        },
        "kvantum_theme": "catppuccin-mocha-sapphire",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-sapphire-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["low-contrast", "warm", "readable"],
    },
    "doom-knight": {
        "name": "doom-knight",
        "description": "DragonFable DoomKnight — deep purples, battered gold, dark crimson.",
        "palette": {
            "background": "#0d0b14", "foreground": "#d4c5a9", "primary": "#c9a227",
            "secondary": "#7b2d8b", "accent": "#e8d5a3", "surface": "#1a1625",
            "muted": "#4a3f5c", "danger": "#8b1a1a", "success": "#4a7c59", "warning": "#c9a227",
        },
        # Primary is gold; catppuccin-mocha-yellow is the closest Kvantum accent.
        "kvantum_theme": "catppuccin-mocha-yellow",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-yellow-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["dark", "gothic", "gold", "dragonfable"],
    },

    "void-dragon": {
        "name": "void-dragon",
        "description": "Deep void sky, cyan soul blade, gold filigree, dark teal dragon aura.",
        "palette": {
            "background": "#0c1220",
            "foreground": "#e4f0ff",
            "primary":    "#7ad4f0",
            "secondary":  "#0d2e32",
            "accent":     "#d4a012",
            "surface":    "#1c1e2a",
            "muted":      "#3d2214",
            "danger":     "#cc3090",
            "success":    "#2a8060",
            "warning":    "#c87820",
        },
        # catppuccin-mocha-teal (balanced), -sky (brighter), -sapphire (deeper blue).
        "kvantum_theme": "catppuccin-mocha-teal",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-teal-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["void", "dragon", "cyan", "gold", "dark-fantasy"],
    },
    "shiva-temple": {
        "name": "shiva-temple",
        "description": "Lord Shiva's haunted temple — cosmic void, third-eye indigo, vermillion sindoor, temple gold.",
        "palette": {
            "background": "#0a0b1a", "foreground": "#d8d0c8", "primary": "#5b4fcf",
            "secondary": "#1a1824", "accent": "#c44820", "surface": "#151320",
            "muted": "#3a3040", "danger": "#b81830", "success": "#387048", "warning": "#c89020",
        },
        "kvantum_theme": "catppuccin-mocha-mauve",
        "plasma_theme": "default",
        "cursor_theme": "catppuccin-macchiato-mauve-cursors",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["shiva", "temple", "cosmic", "indigo", "vermillion", "dark", "sacred"],
    },
    "bareblood": {
        "name": "bareblood",
        "description": "Gothic maximalist dark fantasy. Blood reds, wine blacks, muted rose-grey. Zero blues — amber fills the cyan role.",
        "palette": {
            "background": "#140607",
            "foreground": "#685259",
            "primary":    "#cc1133",
            "secondary":  "#3d2130",
            "accent":     "#e8a766",
            "surface":    "#3b0d10",
            "muted":      "#180000",
            "danger":     "#c5245c",
            "success":    "#579523",
            "warning":    "#aa301b",
        },
        # KvDark is the canonical built-in dark Kvantum theme present on most installs.
        # BreezeDark is a native Qt/KDE style, NOT a Kvantum theme — do not use it here.
        "kvantum_theme": "KvDark",
        "plasma_theme": "default",
        "cursor_theme": "default",
        "icon_theme": "Papirus-Dark",
        "gtk_theme": "Adwaita-dark",
        "mood_tags": ["gothic", "maximalist", "blood", "wine", "fantasy", "bareblood"],
    },
}


def load_preset(name: str) -> dict | None:
    """Return a named preset dict, or None if not found."""
    return PRESETS.get(name)
