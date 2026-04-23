---
name: ricer-rollback
description: "Rollback architecture, deterministic session protocol, and preset management for hermes-ricer. Load when setting up safety backups, running a ricing session, reverting changes, or adding/modifying presets."
---

# ricer-rollback — Rollback Architecture and Session Protocol

Part of the hermes-ricer suite. Safety first — always load this before applying any theme.

---

## Rollback Architecture (4 Layers)

Four layers of protection, from external long-term to session-level.

### Layer 0 — GitHub dotfiles (external)

Your full home directory config backed up to a private GitHub repo:
`~/.dotfiles` → `git@github.com:H-Ali13381/home-pc-backup.git`

This is your off-machine, long-term backup. Use it to:
- Restore on a new machine
- Rollback changes from weeks/months ago
- Survive disk failure

Setup (one-time):
```bash
git init --bare $HOME/.dotfiles
alias dotfiles='git --git-dir=$HOME/.dotfiles --work-tree=$HOME'
dotfiles remote add origin git@github.com:H-Ali13381/home-pc-backup.git
# Add .gitignore, then add files you want to track
dotfiles add ~/.bashrc ~/.config/kdeglobals ...
dotfiles commit -m "init: dotfiles baseline"
dotfiles push --set-upstream origin main
```

The deterministic session script prompts you to back up here before starting.

### Layer 1 — ~/.hermes/ git baseline

Before any ricing session, ensure a baseline git commit exists at `~/.hermes/`.
If not set up: load and follow the `hermes-dot-dir-git-backup` skill first.
This rolls back skill files, ricer.py, templates — anything in `~/.hermes/`.

### Layer 2 — ricer.py pre-flight backups

Every `apply` or `preset` run creates a timestamped backup dir:
`~/.cache/hermes-ricer/backups/<timestamp>/`

Before writing anything, ricer.py snapshots:
- **KDE**: active colorscheme, LookAndFeelPackage, Kvantum theme, widgetStyle,
  Plasma theme, cursor theme, and wallpaper via `kreadconfig6` + file parsing
- **GTK**: `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`, `gtk-4.0/gtk.css`
- **Konsole**: default profile from `konsolerc`
- **kitty**: `theme.conf` AND `kitty.conf` (main config gets an injected include line)
- **rofi**: `hermes-theme.rasi` AND `config.rasi`
- **waybar**: `style-hermes.css` AND main config
- **dunst**: `hermes-dunstrc` AND `dunstrc`

The `undo` command:
- Restores all backed-up files
- Removes injected include/theme lines via stored markers (no traces left)
- Re-applies previous KDE colorscheme via `plasma-apply-colorscheme`
- Re-applies previous Kvantum theme and widgetStyle
- Re-applies previous Plasma theme via `plasma-apply-desktoptheme`
- Re-applies previous cursor theme via `plasma-apply-cursortheme`
- Reports: `restored / failed / skipped` — `"partial"` status on any failure

### Layer 3 — Immutable baseline via desktop_state_audit.py

The `desktop_state_audit.py` script captures the COMPLETE desktop state. It is READ-ONLY
and writes:
- JSON manifest: `~/.cache/hermes-ricer/baselines/<timestamp>_baseline.json`
- Config backup dir: `~/.cache/hermes-ricer/baselines/<timestamp>_files/`

This baseline includes wallpaper path, panel/widget topology, all config files,
and every themable setting. Use it to manually restore anything the ricer undo misses.

---

## Safe Live-Test Protocol

Run this sequence before trusting ricer on a daily driver:

0. **Backup first** — The script will prompt you to back up to GitHub dotfiles or skip
1. Ensure `~/.hermes/` has a git baseline commit
2. Dry-run to confirm snapshot is correct:

       ricer preset <name> --dry-run

   Check that `previous_colorscheme` appears in the output.

3. Apply for real:

       ricer preset <name>

4. Immediately verify rollback plan:

       ricer simulate-undo

5. If anything looks wrong, undo:

       ricer undo

6. Confirm live revert:

       plasma-apply-colorscheme --list-schemes   # previous scheme should show (current)

---

## Deterministic Session Script

Use the session script for all production ricing. It enforces the safety protocol automatically.

    ~/.hermes/skills/creative/hermes-ricer/scripts/deterministic_ricing_session.py

### Quick Reference

    # Dry-run a preset (no changes)
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/deterministic_ricing_session.py \
        --preset <name> --dry-run

    # Apply for real (with confirmation prompt)
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/deterministic_ricing_session.py \
        --preset <name>

    # Apply with wallpaper
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/deterministic_ricing_session.py \
        --preset <name> --wallpaper /path/to/wallpaper.png

    # Rollback last session
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/deterministic_ricing_session.py \
        --rollback

    # Show status
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/deterministic_ricing_session.py \
        --status

### Protocol Phases

| Phase | What Happens |
|-------|-------------|
| -1 — Backup Prompt | Script prompts user to back up to GitHub dotfiles or skip |
| 0 — Pre-flight Audit | `desktop_state_audit.py` captures complete desktop state (immutable baseline) |
| 1 — Design Selection | Load preset or custom `design_system.json` |
| 2 — Dry-Run | Preview all changes without writing anything |
| 3 — Verification | Human reviews proposed changes and previous values |
| 4 — Apply | Execute materialization (only after "yes" confirmation) |
| 5 — Post-flight Verify | Re-audit and confirm changes took effect |
| 6 — Rollback (opt) | Full restore to pre-flight baseline if anything fails |

### Pitfall: phase5_postflight wrong JSON paths

The audit JSON structure is `kde.colorscheme.active_scheme`, `kde.kvantum.kvantum_theme`,
`kde.kvantum.widget_style`, etc. Do NOT use flat top-level keys — they won't match the
nested structure and post-flight comparison will always show SAME.

---

## Presets

### Available Presets

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

### void-dragon Preset (canonical)

```python
"void-dragon": {
    "name": "void-dragon",
    "description": "Void dragon knight — extracted directly from DragonFable character art.",
    "palette": {
        "background": "#0c1220",
        "foreground": "#e4f0ff",
        "primary":    "#7ad4f0",   # cyan soul blade
        "secondary":  "#0d2e32",
        "accent":     "#d4a012",   # gold filigree
        "surface":    "#1c1e2a",
        "muted":      "#3d2214",
        "danger":     "#cc3090",   # chaos magenta gem
        "success":    "#2a8060",
        "warning":    "#c87820",
    },
    "kvantum_theme": "catppuccin-mocha-teal",
    "cursor_theme": "catppuccin-macchiato-teal-cursors",
    "gtk_theme": "Adwaita-dark",
    "mood_tags": ["void", "dragon", "cyan", "gold", "dragonfable"],
}
```

### Adding a New Preset

1. Add a dict entry to `PRESETS` in `ricer.py`
2. Include ALL required keys:
   - `name` — matches the dict key
   - `description` — one sentence
   - `palette` — all 10 keys: background, foreground, primary, secondary, accent, surface, muted, danger, success, warning
   - `kvantum_theme` — MUST be an installed Kvantum theme. Check: `find /usr/share/Kvantum ~/.local/share/Kvantum -maxdepth 1 -type d`
   - `cursor_theme` — MUST be an installed cursor theme. Check: `find /usr/share/icons ~/.local/share/icons -maxdepth 1 -name "*cursor*" -type d`
   - `gtk_theme` — optional; falls back to Adwaita-dark if omitted
   - `mood_tags` — list of descriptive strings

3. Verify with dry-run before applying:

       ricer preset <name> --dry-run

### Pitfall: presets missing kvantum_theme

Presets missing `kvantum_theme` silently fall back to `"kvantum-dark"` which is almost
certainly not installed. Always specify an installed theme explicitly.

---

## Manifest Files

| File | Purpose |
|------|---------|
| `~/.cache/hermes-ricer/current/manifest.json` | Active theme — what's currently applied |
| `~/.cache/hermes-ricer/current/history/` | One JSON per past apply |
| `~/.cache/hermes-ricer/backups/<ts>/` | Pre-apply file backups |
| `~/.cache/hermes-ricer/baselines/<ts>_baseline.json` | Immutable pre-session audit |
| `~/.cache/hermes-ricer/session_logs/` | Session script verbose logs |

### Manifest JSON structure

```json
{
  "theme_name": "void-dragon",
  "applied_at": "2026-04-22T21:00:00",
  "backup_dir": "~/.cache/hermes-ricer/backups/20260422_210000",
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

## Known Pitfalls

- **Pre-2026-04-22 manifests are incomplete.** They don't contain `kvantum_theme`,
  `plasma_theme`, or `cursor_theme`. For old manifests, use `desktop_state_audit.py`
  to capture a fresh baseline before undoing.

- **Wallpaper changed manually (outside ricer) will not be restored by undo.**
  The pre-flight snapshot reads the wallpaper from `appletsrc` at snapshot time.
  If you changed it manually after that, undo will restore the snapshot version, not
  whatever you most recently set.

- **`undo()` must use `--delete` to clear widgetStyle**, not an empty string.
  See ricer-kde pitfalls for details.

- **simulate-undo showed incomplete output on pre-2026-04-22 versions.**
  The display loop only checked `app == "kde"` branches. After the materializer fix,
  simulate-undo now shows all restore actions for all apps. Ensure your ricer.py is
  up-to-date before trusting the output.
