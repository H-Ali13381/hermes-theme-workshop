---
name: hermes-ricer
description: "Deterministic KDE Plasma theming engine. Captures complete desktop state before any change, applies themes atomically with full rollback, and maintains a machine-readable audit trail. Supports colorschemes, Kvantum, cursors, Konsole, and wallpaper."
tags: [kde, plasma, theming, ricing, kvantum, wayland]
---

# hermes-ricer — Deterministic KDE Desktop Theming Engine

## Philosophy

Every desktop change must be **reversible, audited, and reproducible**. No manual edits. No ad-hoc commands. No state drift. Treat your desktop environment the way you'd treat production infrastructure.

```
Capture baseline → Dry-run → Review diff → Apply → Verify → Rollback if needed
```

## Quick Start

```bash
# 1. Install
bash ~/.hermes/skills/hermes-ricer/scripts/setup.sh

# 2. Capture your current desktop state (READ-ONLY, always safe)
python3 ~/.hermes/skills/hermes-ricer/scripts/desktop_state_audit.py

# 3. Dry-run a preset (no changes made)
ricer preset void-dragon --dry-run

# 4. Apply
python3 ~/.hermes/skills/hermes-ricer/scripts/deterministic_ricing_session.py --preset void-dragon

# 5. Undo
python3 ~/.hermes/skills/hermes-ricer/scripts/deterministic_ricing_session.py --rollback
```

---

## Scripts

### `desktop_state_audit.py` — Read-only baseline capture
Captures the complete KDE desktop state. **Never writes any config.**

Output:
- `~/.cache/hermes-ricer/baselines/<timestamp>_baseline.json` — full state manifest
- `~/.cache/hermes-ricer/baselines/<timestamp>_files/` — physical copies of all config files

Captures:
- Colorscheme, LookAndFeelPackage, widgetStyle
- Kvantum theme
- Plasma theme
- Cursor theme, icon theme, splash screen
- Wallpaper path + fill mode (per monitor, from `appletsrc`)
- Panel and widget topology (containment IDs, applet plugins, pinned launchers)
- GTK theme
- All Konsole profiles

### `ricer.py` — Materialization engine

```bash
ricer discover          # detect DE/WM and installed apps
ricer status            # show active theme + detected stack
ricer presets           # list built-in presets
ricer preset <name>     # apply a named preset
ricer preset <name> --dry-run
ricer simulate-undo     # show exactly what undo would restore
ricer undo              # restore previous state
ricer apply --design <path>  # apply a design_system.json file
```

### `deterministic_ricing_session.py` — Corporate-grade session orchestrator

The **only safe entry point** for applying themes. Enforces the full protocol:

| Phase | Action |
|-------|--------|
| 0 — Pre-flight Audit | `desktop_state_audit.py` captures immutable baseline |
| 1 — Design Selection | Load preset or custom JSON |
| 2 — Dry-Run | Preview all changes, zero writes |
| 3 — Verification | Human-readable diff printed for review |
| 4 — Apply | Only proceeds after `yes` confirmation |
| 5 — Post-flight | Re-audits and compares all 6 critical fields against baseline |
| 6 — Rollback | Full restore to pre-flight state |

```bash
python3 deterministic_ricing_session.py --preset <name>
python3 deterministic_ricing_session.py --preset <name> --dry-run
python3 deterministic_ricing_session.py --preset <name> --wallpaper /path/to/wall.png
python3 deterministic_ricing_session.py --rollback
python3 deterministic_ricing_session.py --status
```

---

## Backup Architecture (3 Layers)

### Layer 1 — `~/.hermes/` git
Tracks the **scripts themselves**. If the tool gets broken by a bad edit, `git revert` here.
Not the place for desktop state — that's Layers 2 and 3.

### Layer 2 — Pre-flight ricer backups
Before every `apply`, `snapshot_kde_state()` reads current values and `backup_file()` copies
affected configs to a timestamped directory:

```
~/.cache/hermes-ricer/backups/<timestamp>/
  kde/hermes-<theme>.colors
  kvantum/kvantum.kvconfig
  kvantum/kdeglobals
  cursor/kcminputrc
  plasma/plasmarc
  konsole/<profile>.profile
  konsole/konsolerc
```

The manifest at `~/.cache/hermes-ricer/current/manifest.json` records every change with
its previous value and backup path. `ricer undo` reads this to restore.

### Layer 3 — Immutable baseline audit
`desktop_state_audit.py` captures everything Layer 2 captures, plus panel topology,
GTK, icons, splash, and all Konsole profiles. **Read-only, always safe to run.**

If `ricer undo` fails on a specific setting, manually restore from Layer 3:
```bash
cp ~/.cache/hermes-ricer/baselines/<ts>_files/kdeglobals ~/.config/kdeglobals
```

---

## What Gets Applied

When you apply a preset, the following materializers run in order:

| Materializer | What it does |
|---|---|
| `kde` | Writes a `.colors` file and calls `plasma-apply-colorscheme` |
| `kvantum` | Writes `kvantum.kvconfig`, sets `widgetStyle=kvantum`, reloads KWin |
| `plasma_theme` | Sets `plasmarc Theme/name`, calls `plasma-apply-desktoptheme` |
| `cursor` | Sets `kcminputrc Mouse/cursorTheme`, calls `plasma-apply-cursortheme` |
| `konsole` | Writes `.profile` + `.colorscheme`, activates via `DefaultProfile` in `konsolerc` |

---

## Design System Format

```json
{
  "name": "my-theme",
  "description": "Human description",
  "palette": {
    "background": "#0c1220",
    "foreground": "#e4f0ff",
    "primary":    "#7ad4f0",
    "secondary":  "#0d2e32",
    "accent":     "#d4a012",
    "surface":    "#1c1e2a",
    "muted":      "#3d5060",
    "danger":     "#cc3090",
    "success":    "#2a8060",
    "warning":    "#c87820"
  },
  "kvantum_theme": "catppuccin-mocha-teal",
  "cursor_theme": "breeze_cursors",
  "plasma_theme": "breeze-dark",
  "mood_tags": ["dark", "cyan"]
}
```

All hex values are converted to decimal RGB internally for KDE `.colors` files.

---

## Built-in Presets

| Name | Description |
|---|---|
| `catppuccin-mocha` | Soothing pastel dark |
| `nord` | Arctic blue |
| `gruvbox-dark` | Retro groove warm |
| `dracula` | Vibrant neon purple |
| `tokyo-night` | Dark cyberpunk |
| `rose-pine` | Soft nature pastels |
| `solarized-dark` | Low-contrast warm |
| `doom-knight` | Gothic gold and crimson |
| `void-dragon` | Void sky, cyan blade, gold filigree |

---

## KDE-Specific Critical Knowledge

### widgetStyle values (verified against Qt6 plugin names)
```
Breeze   → /usr/lib/qt6/plugins/styles/breeze6.so
kvantum  → /usr/lib/qt6/plugins/styles/libkvantum.so   ← CORRECT value
Oxygen   → /usr/lib/qt6/plugins/styles/oxygen6.so
```
`kvantum-dark` is NOT a valid Qt6 style name. It silently falls back to Breeze.

### Konsole DefaultProfile group
```
kwriteconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile hermes-ricer.profile
```
Group is `Desktop Entry` not `General`. Verified from live `konsolerc` format.

### Safe KWin reload
```bash
qdbus6 org.kde.KWin /KWin reconfigure
```
Safe on Wayland. DO NOT call `qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.refreshCurrentShell` — kills plasmashell on Wayland with no restart.

### KDE `.colors` files require decimal RGB
`BackgroundNormal=12,18,32` not `BackgroundNormal=#0c1220`. Hex is accepted without error but produces no visible change.

### plasma-apply-colorscheme takes the Name field, not the filename
The name comes from `[General] ColorScheme=` inside the `.colors` file.

---

## Extending with New Apps

1. Create `templates/<app>/` with `.template` files using `{{palette_key}}` placeholders
2. Add a materializer function taking `(design, backup_ts, dry_run)` args:
   - Backup existing config **before** writing
   - Inject with a `# hermes-ricer` marker for clean undo
   - Return a list of change dicts
3. Add entry to `APP_MATERIALIZERS` in `ricer.py`
4. If it's a KDE sub-system (no binary to check), add `apps["your_key"] = {"installed": True}` in `discover_apps()` when `"kde" in apps`

---

## Dependencies

- Python 3.10+
- KDE Plasma 6
- `plasma-apply-colorscheme`, `plasma-apply-wallpaperimage`, `plasma-apply-cursortheme`
- `plasma-apply-desktoptheme`, `kreadconfig6`, `kwriteconfig6`, `qdbus6`
- `kvantum` package (for Kvantum materialization)
- `jinja2`, `pillow` (optional — fallback renderers built-in)
