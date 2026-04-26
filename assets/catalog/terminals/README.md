# Terminal Options

Terminal choice affects font rendering, transparency, ligatures, config format, startup speed, and how easy it is to theme.

## Common Picks

| Terminal | Best for | Notes |
|----------|----------|-------|
| kitty | Most balanced default | Fast, feature-rich, easy config |
| Konsole | Best KDE-native choice | Integrates with Plasma, profiles |
| Alacritty | Speed / minimalism | GPU-accelerated, simple YAML/TOML |
| WezTerm | Power users | Lua config, multiplexing, ligatures |
| foot | Wayland minimal | Lightweight |
| st | Suckless minimalism | Patch-driven, compile-time config |

## Recommendation Flow

- KDE desktop and want native integration? → Konsole
- Want best default with rich config? → kitty
- Want minimal + fast? → Alacritty
- Want advanced scripting / Lua? → WezTerm

## Current ricer support

- Supported: kitty, Konsole
- Not yet implemented: Alacritty, WezTerm, foot

## What users usually customize

- Font + size
- Background opacity
- Cursor shape
- Color scheme
- Padding / window margins
- Tab bar appearance
