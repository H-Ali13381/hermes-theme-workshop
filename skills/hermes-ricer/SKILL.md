---
name: hermes-ricer
description: "AI-Native Linux Desktop Theming Engine. Use whenever the user wants to theme, rice, customize, or beautify their Linux desktop environment — whether they mention 'ricing', 'theme my desktop', 'make my terminal pretty', 'customize my WM', 'dotfiles', 'color scheme', or any desktop aesthetic modification. Also use when the user wants to generate a design system from an image or text prompt and apply it across multiple applications. This skill is the orchestrator — it describes the architecture and tells you which subskill to load per task."
---

# Hermes Ricer — AI-Native Desktop Theming Engine

## Philosophy

Linux ricing is currently a manual, fragmented craft spread across a dozen config formats.
This skill turns a single natural-language prompt or image into a coherent, system-wide
design system and materializes it live across your desktop.

One prompt. One command. One desktop transformed.

## Subskill Index

Load the appropriate subskill(s) alongside this one:

| Task | Load |
|------|------|
| KDE colorscheme, Kvantum, cursor, Plasma theme, panel SVG | `ricer-kde` |
| GTK apps (Firefox, Nautilus, GIMP) theming | `ricer-gtk` |
| Terminal (kitty, Konsole), bar (waybar), launcher (rofi), notifications (dunst) | `ricer-apps` |
| Wallpaper generation, style transfer, image-to-palette extraction | `ricer-wallpaper` |
| Backup setup, session protocol, undo, presets, void-dragon palette | `ricer-rollback` |

For a full desktop ricing session, load all five subskills.

## Capabilities

| Input | What Happens |
|-------|-------------|
| Text prompt | Generate a design system (palette, mood, typography) → Hermes materializes configs |
| Image/Wallpaper | Extract dominant colors via vision subagent → Generate palette → Apply everywhere |
| Named theme | Load a preset (Catppuccin, Nord, Gruvbox, Tokyo Night, Rose Pine, Dracula, Doom Knight, Void Dragon) |
| Undo | Restore previous desktop state from backup manifest |

## Supported Targets

Desktop Environments / WMs:
- KDE Plasma (primary) — colorscheme, Kvantum widgets, cursor, splash, wallpaper, Konsole
- Hyprland — config includes, border/gradient colors, animations
- Sway / i3 — config includes, bar colors, gaps
- bspwm — bspc theme commands

Applications:
- Terminal: kitty, alacritty, konsole
- Bar: waybar, polybar
- Launcher: rofi, wofi
- Notifications: dunst, mako, swaync
- Wallpaper: awww/swww, mpvpaper, feh, nitrogen, plasma-apply-wallpaperimage (hyprpaper v0.8.3 silently fails — use awww)
- Compositor FX: picom, Hyprland built-in
- GTK/Qt: direct settings.ini writes (kde-gtk-config not required)

---

## Architecture

```
Input (prompt / image / preset)
    |
[Design System Generator] -> design_system.json (10-key palette)
    |
[Discovery Layer] — detect WM, bar, terminal, launcher, wallpaper daemon
    |
[Template Engine] — render app config fragments from palette
    |
[Materialization Layer] — backup old state, write fragments, inject includes
    |
[Activation Layer] — signal/reload apps (KWin reconfigure, etc.)
    |
Rollback manifest saved to ~/.cache/linux-ricing/current/manifest.json
```

---

## ricer CLI

    ricer discover              # detect desktop stack and installed apps
    ricer status                # show active theme + detected stack
    ricer presets               # list built-in presets
    ricer preset <name>         # apply a named preset
    ricer preset <name> --dry-run  # preview without writing anything
    ricer simulate-undo         # show exactly what undo would restore
    ricer undo                  # restore previous state
    ricer apply --design <path> # apply a design_system.json file

---

## First-Time Setup

Run once after install or after pulling updates:

    bash ~/.hermes/skills/creative/linux-ricing/scripts/setup.sh

This: installs jinja2 + pillow (non-fatal if pip fails), chmod +x ricer.py,
creates `~/.cache/linux-ricing/{backups,current/history}`, symlinks
`ricer` into `~/.local/bin`.

Verify with: `ricer status` — should show WM/DE and detected apps.

---

## File Locations

| Purpose | Path |
|---------|------|
| Skill root | `~/.hermes/skills/creative/linux-ricing/` |
| Python driver | `~/.hermes/skills/creative/linux-ricing/scripts/ricer.py` |
| Deterministic session | `~/.hermes/skills/creative/linux-ricing/scripts/deterministic_ricing_session.py` |
| Desktop state audit | `~/.hermes/skills/creative/linux-ricing/scripts/desktop_state_audit.py` |
| Setup script | `~/.hermes/skills/creative/linux-ricing/scripts/setup.sh` |
| Templates | `~/.hermes/skills/creative/linux-ricing/templates/<app>/` |
| Active theme | `~/.cache/linux-ricing/current/` |
| Active manifest | `~/.cache/linux-ricing/current/manifest.json` |
| Manifest history | `~/.cache/linux-ricing/current/history/` |
| Session logs | `~/.config/rice-sessions/` |
| Backups | `~/.cache/linux-ricing/backups/<timestamp>/` |
| Baselines | `~/.cache/linux-ricing/baselines/<timestamp>_baseline.json` |
| Assets | `~/.hermes/skills/creative/linux-ricing/assets/` |
| Symlink | `~/.local/bin/ricer` -> ricer.py |

---

## Design System JSON — 10-Key Palette

```json
{
  "name": "my-theme",
  "description": "One-sentence description.",
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
    "warning":    "#c87820"
  },
  "kvantum_theme": "catppuccin-mocha-teal",
  "cursor_theme": "catppuccin-macchiato-teal-cursors",
  "icon_theme": "Papirus-Dark",
  "gtk_theme": "Adwaita-dark",
  "mood_tags": ["dark", "dragon", "cyan"]
}
```

---

## Dependencies

- Python 3.10+ (`list[str]`, `str | None` syntax)
- `jinja2` — templating (optional, fallback renderer built-in)
- `pillow` — image color extraction (optional)
- KDE tools (if using KDE):
  - `plasma-apply-colorscheme`
  - `plasma-apply-wallpaperimage`
  - `plasma-apply-cursortheme`
  - `kreadconfig6` / `kwriteconfig6`
  - `qdbus6`

---

## Safety

- This skill never overwrites main config files directly. It writes theme fragments
  and uses include/source directives with tracked markers.
- Backups are created before every change.
- `--dry-run` previews all changes without writing anything.
- `simulate-undo` shows exactly what rollback would do before you commit.
- See `ricer-rollback` for the full 4-layer backup architecture.

---

## Skill Maintenance Notes (Meta)

- Keep this skill generic. All steps, commands, paths, and examples must be
  reproducible by any user on any machine. Do NOT embed usernames, machine names,
  character IDs, specific file paths outside of `~/.hermes/` and `~/.cache/`, or
  session-specific notes.

- Incremental patching causes drift. After several small patches, line-number
  artifacts and stale content accumulate. If the file starts showing embedded
  line numbers or personal references, do a full rewrite via `write_file`.

- Separate "what the user did" from "what anyone should do." Findings from
  live testing (discovered pitfalls, confirmed commands) belong in the relevant
  subskill's Known Pitfalls section — not as session logs tied to a specific machine.
