# Config Templates Reference

## How Templates Work

Every themed application has a Jinja2 template in `templates/<app>/`. When you run `ricer preset` or `ricer apply`, the engine:

1. Loads the design system JSON (10-key palette + metadata)
2. Renders each template with palette variables injected
3. Writes the output to the correct config path (or `/tmp` in `--dry-run`)
4. Backs up originals before overwriting

Templates use standard Jinja2 syntax: `{{ background }}`, `{{ primary }}`, etc.

---

## Available Templates

| Directory | Output File | Format | Description |
|---|---|---|---|
| `kitty/` | `theme.conf` | Kitty conf | Terminal colorscheme — foreground, background, cursor, 16 ANSI colors |
| `waybar/` | `style.css` | GTK CSS | Status bar theme — backgrounds, borders, module colors |
| `rofi/` | `theme.rasi` | Rasi | App launcher theme — window, input, listview, element colors |
| `dunst/` | `dunstrc.fragment` | INI | Notification colors — low/normal/critical urgency sections |
| `gtk/` | `settings.ini` | INI | GTK settings — theme name, icon theme, font, dark preference |
| `alacritty/` | `colors.toml` | TOML | Terminal colorscheme — primary, cursor, normal/bright ANSI |
| `hyprland/` | `theme.conf` | Hyprland conf | Border colors, active/inactive, animation settings |
| `kde/` | `colorscheme.colors` | KDE colors | Full KDE colorscheme — Window, Button, Selection, Tooltip groups |
| `polybar/` | `hermes-colors.ini` | INI | Bar color variables — background, foreground, module colors |
| `wofi/` | `style.css` | CSS | Launcher theme — window, input, entry colors |
| `mako/` | `config` | Mako conf | Notification daemon — background, text, border, urgency colors |
| `swaync/` | `style.css` | GTK CSS | Notification center theme — panel, card, button colors |
| `picom/` | `hermes-picom.conf` | Picom conf | Compositor config — opacity, blur, shadow, animation settings |

---

## Template Variables Reference

### Palette Keys (always available)

Every template receives the 10 palette colors as hex strings:

| Variable | Role | Example |
|---|---|---|
| `{{ background }}` | Main background | `#1e1e2e` |
| `{{ foreground }}` | Main text | `#cdd6f4` |
| `{{ primary }}` | Accent / highlights | `#89b4fa` |
| `{{ secondary }}` | Secondary accent | `#313244` |
| `{{ accent }}` | Tertiary accent / links | `#f9e2af` |
| `{{ surface }}` | Elevated surfaces / cards | `#181825` |
| `{{ muted }}` | Dimmed / inactive text | `#585b70` |
| `{{ danger }}` | Errors / destructive | `#f38ba8` |
| `{{ success }}` | Success / OK states | `#a6e3a1` |
| `{{ warning }}` | Warnings / caution | `#fab387` |

### Metadata Keys

| Variable | Description |
|---|---|
| `{{ name }}` | Theme name (e.g., `catppuccin-mocha`) |
| `{{ description }}` | One-line theme description |
| `{{ kvantum_theme }}` | Kvantum theme name to apply |
| `{{ cursor_theme }}` | Cursor theme name |
| `{{ gtk_theme }}` | GTK theme name |

---

## Adding a New Template

1. Create a directory: `templates/<app-name>/`
2. Add your template file with a `.template` extension
3. Use `{{ variable }}` syntax for any palette or metadata key
4. Register the output path in `scripts/ricer.py` under the app's config mapping

**Example** — a new `foot` terminal template at `templates/foot/foot.ini.template`:

```ini
[colors]
background={{ background | replace('#', '') }}
foreground={{ foreground | replace('#', '') }}
regular0={{ surface | replace('#', '') }}
regular1={{ danger | replace('#', '') }}
regular2={{ success | replace('#', '') }}
regular3={{ warning | replace('#', '') }}
regular4={{ primary | replace('#', '') }}
regular5={{ accent | replace('#', '') }}
regular6={{ secondary | replace('#', '') }}
regular7={{ foreground | replace('#', '') }}
```

Jinja2 filters like `replace`, `lower`, and `upper` work in all templates.
