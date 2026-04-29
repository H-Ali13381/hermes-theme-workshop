# Rollback Architecture & Session Protocol

## 4-Layer Rollback Architecture

### Layer 0 — GitHub Dotfiles (external)
Full home directory config backed up to a private GitHub repo (`~/.dotfiles`).

```bash
git init --bare $HOME/.dotfiles
alias dotfiles='git --git-dir=$HOME/.dotfiles --work-tree=$HOME'
dotfiles remote add origin git@github.com:<user>/<repo>.git
dotfiles add ~/.bashrc ~/.config/kdeglobals ...
dotfiles commit -m "init: dotfiles baseline"
dotfiles push --set-upstream origin main
```

### Layer 1 — ~/.hermes/ Git Baseline
Before any ricing session, ensure a baseline git commit exists at `~/.hermes/`. Rolls back skill files, ricer.py, templates.

### Layer 2 — ricer.py Pre-flight Backups
Every `apply` or `preset` run creates: `~/.cache/linux-ricing/backups/<timestamp>/`

Snapshots before writing: KDE state, GTK settings, Konsole profile, kitty conf, rofi, waybar, dunst configs.

The `undo` command restores all backed-up files, removes injected markers, re-applies previous KDE colorscheme/Kvantum/Plasma theme/cursor via their respective `plasma-apply-*` commands.

### Layer 3 — Immutable Baseline via desktop_state_audit.py
Captures COMPLETE desktop state (read-only):
- JSON manifest: `~/.cache/linux-ricing/baselines/<ts>_baseline.json`
- Config backups: `~/.cache/linux-ricing/baselines/<ts>_files/`

---

## Safe Live-Test Protocol

1. Backup to GitHub dotfiles (or skip)
2. Ensure `~/.hermes/` git baseline commit
3. Dry-run: `ricer preset <name> --dry-run`
4. Apply: `ricer preset <name>`
5. Verify rollback: `ricer simulate-undo`
6. If wrong: `ricer undo`

---

## Deterministic Session Script

```bash
# Dry-run
python3 ~/.hermes/skills/creative/linux-ricing/scripts/deterministic_ricing_session.py \
    --preset <name> --dry-run

# Apply with wallpaper
python3 ~/.hermes/skills/creative/linux-ricing/scripts/deterministic_ricing_session.py \
    --preset <name> --wallpaper /path/to/wallpaper.png

# Rollback
python3 ~/.hermes/skills/creative/linux-ricing/scripts/deterministic_ricing_session.py --rollback
```

### 7 Phases

| Phase | What Happens |
|-------|-------------|
| -1 — Backup Prompt | Prompt to back up to GitHub dotfiles or skip |
| 0 — Pre-flight Audit | `desktop_state_audit.py` captures immutable baseline |
| 1 — Design Selection | Load preset or custom `design_system.json` |
| 2 — Dry-Run | Preview all changes without writing |
| 3 — Verification | Human reviews proposed changes and previous values |
| 4 — Apply | Execute materialization (after "yes" confirmation) |
| 5 — Post-flight Verify | Re-audit and confirm changes took effect |
| 6 — Rollback (opt) | Full restore to pre-flight baseline if anything fails |

---

## Manifest Files

| File | Purpose |
|------|---------|
| `~/.cache/linux-ricing/current/manifest.json` | Active theme — what's currently applied |
| `~/.cache/linux-ricing/current/history/` | One JSON per past apply |
| `~/.cache/linux-ricing/backups/<ts>/` | Pre-apply file backups |
| `~/.cache/linux-ricing/baselines/<ts>_baseline.json` | Immutable pre-session audit |
| `~/.cache/linux-ricing/session_logs/` | Session script verbose logs |

### Manifest JSON

```json
{
  "theme_name": "void-dragon",
  "applied_at": "2026-04-22T21:00:00",
  "backup_dir": "~/.cache/linux-ricing/backups/20260422_210000",
  "previous_state": {
    "active_colorscheme": "BreezeDark",
    "look_and_feel": "org.kde.breeze.desktop",
    "kvantum_theme": null,
    "widget_style": null,
    "plasma_theme": "default",
    "cursor_theme": "breeze_cursors",
    "wallpaper": "/usr/share/wallpapers/Next/contents/images/3200x1800.png"
  },
  "changes": [...],
  "status": "applied"
}
```

---

## All 10 Presets

| Name | Description |
|------|-------------|
| `catppuccin-mocha` | Soothing pastel dark theme |
| `nord` | Arctic, north-bluish color palette |
| `gruvbox-dark` | Retro groove dark colors |
| `dracula` | Dark theme with vibrant colors |
| `tokyo-night` | Dark Tokyo-inspired blue/purple |
| `rose-pine` | Rose Piné — warm dawn theme |
| `doom-knight` | DragonFable DoomKnight — deep purples, battered gold, dark crimson |
| `void-dragon` | Void dragon knight — cyan soul blade, gold filigree, void sky |

### void-dragon Canonical Dict

```python
"void-dragon": {
    "name": "void-dragon",
    "description": "Void dragon knight — extracted from DragonFable character art.",
    "palette": {
        "background": "#0c1220",  "foreground": "#e4f0ff",
        "primary":    "#7ad4f0",  "secondary":  "#0d2e32",
        "accent":     "#d4a012",  "surface":    "#1c1e2a",
        "muted":      "#3d2214",  "danger":     "#cc3090",
        "success":    "#2a8060",  "warning":    "#c87820",
    },
    "kvantum_theme": "catppuccin-mocha-teal",
    "cursor_theme": "catppuccin-macchiato-teal-cursors",
    "icon_theme": "Papirus-Dark",
    "gtk_theme": "Adwaita-dark",
    "mood_tags": ["void", "dragon", "cyan", "gold", "dragonfable"],
}
```

### Adding New Presets

1. Add dict entry to `PRESETS` in `ricer.py`
2. Include ALL required keys: `name`, `description`, `palette` (all 10), `kvantum_theme`, `cursor_theme`, `icon_theme`, `gtk_theme`, `mood_tags`
3. Verify installed themes:
   - Kvantum: `find /usr/share/Kvantum ~/.local/share/Kvantum -maxdepth 1 -type d`
   - Icons: `find /usr/share/icons ~/.local/share/icons -maxdepth 1 -type d`
   - Cursors: `find /usr/share/icons ~/.local/share/icons -maxdepth 2 -name "cursors" -type d`
4. Dry-run: `ricer preset <name> --dry-run`
