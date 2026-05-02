# Baseline Restore Procedure (Manual Undo)

Use this when `ricer.py undo-session` is unavailable (corrupt manifest, missing
session dir, workflow hung before step 6 completed).

## Step 1 — Find the baseline JSON

```bash
ls ~/.config/rice-sessions/<thread-id>/baseline_*.json
# e.g. baseline_20260501_052441.json
cat ~/.config/rice-sessions/<thread-id>/baseline_<timestamp>.json | python3 -m json.tool | head -80
```

The `"backups"` section lists every file that was copied before the rice ran.
The `"baseline_dir"` key is the absolute path to the backup folder.

## Step 2 — Restore flat files

```python
import shutil
from pathlib import Path

baseline_dir = Path("/home/neos/.cache/linux-ricing/baselines/<timestamp>_files")
home = Path.home()

restore_map = {
    "kdeglobals":       home / ".config/kdeglobals",
    "kcminputrc":       home / ".config/kcminputrc",
    "konsolerc":        home / ".config/konsolerc",
    "ksplashrc":        home / ".config/ksplashrc",
    "plasmarc":         home / ".config/plasmarc",
    "kvantum.kvconfig": home / ".config/Kvantum/kvantum.kvconfig",
    "gtkrc-2.0":        home / ".gtkrc-2.0",
    "gtk-3.0-settings": home / ".config/gtk-3.0/settings.ini",
    "gtk-4.0-settings": home / ".config/gtk-4.0/settings.ini",
    "kitty.conf":       home / ".config/kitty/kitty.conf",
    "fastfetch.config.json": home / ".config/fastfetch/config.json",
    "dunstrc":          home / ".config/dunst/dunstrc",
    "rofi.config.rasi": home / ".config/rofi/config.rasi",
    "waybar.style.css": home / ".config/waybar/style.css",
    "starship.toml":    home / ".config/starship.toml",
    "bashrc":           home / ".bashrc",
    "zshrc":            home / ".zshrc",
}

for backup_name, dest in restore_map.items():
    src = baseline_dir / backup_name
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))
        print(f"RESTORED: {backup_name}")
    else:
        print(f"SKIP (no backup): {backup_name}")
```

## Step 3 — Restore directory backups

> **PITFALL:** `shutil.rmtree` + `copytree` replaces the directory with EXACTLY
> what the baseline captured. If the baseline itself contained files from an
> earlier rice session (e.g. `hermes-catppuccin-mocha.colors` was already present
> before mossgrown-throne ran), those files ARE in the backup and will be restored
> correctly. But if the backup dir was created AFTER a previous rice, those earlier
> rice artifacts are part of your baseline — that is correct behavior.
> After the copy, verify that `color-schemes/` matches what you expected and
> re-add any files that were in the baseline but appear missing.

```python
for backup_name, dest in {
    "konsole_profiles": home / ".local/share/konsole",
    "color-schemes":    home / ".local/share/color-schemes",
}.items():
    src = baseline_dir / backup_name
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(str(dest))
        shutil.copytree(str(src), str(dest))
        print(f"RESTORED DIR: {backup_name}")
        # Verify against baseline manifest
        restored = sorted(p.name for p in dest.iterdir())
        backed_up = sorted(p.name for p in src.iterdir())
        if restored != backed_up:
            print(f"  WARNING: mismatch after restore! Check {dest}")
```

## Step 4 — Apply KDE live state

```bash
# Read these values from the baseline JSON
SCHEME="BreezeDark"        # baseline.kde.colorscheme.active_scheme
WALLPAPER="/usr/share/wallpapers/Next/contents/images_dark/5120x2880.png"  # strip file://
CURSOR="breeze_cursors"    # baseline.kde.cursor.active_cursor
KVANTUM_THEME="KvDark"     # baseline.kde.kvantum.kvantum_theme

plasma-apply-colorscheme "$SCHEME"
plasma-apply-wallpaperimage "$WALLPAPER"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "$CURSOR"
kvantummanager --set "$KVANTUM_THEME" 2>/dev/null || \
  echo -e "[General]\ntheme=$KVANTUM_THEME" > ~/.config/Kvantum/kvantum.kvconfig
```

## Step 5 — Post-restore cleanup

### kitty theme.conf
The baseline does NOT back up `theme.conf` separately. If it still has rice colors:
```bash
# Remove it — kitty will use inline colors from restored kitty.conf
rm -f ~/.config/kitty/theme.conf
```

### fastfetch config.json symlink
The rice may have replaced `config.json` with a symlink to `config.jsonc`:
```bash
# Check
ls -la ~/.config/fastfetch/config.json
# If it's a symlink, restore the real file
rm -f ~/.config/fastfetch/config.json
cp "<baseline_dir>/fastfetch.config.json" ~/.config/fastfetch/config.json
```

### rofi hermes-theme.rasi
This file is NOT backed up (predates all sessions). After restore, `config.rasi`
still points to it. Restore it to the previous theme's colors manually, or update
`config.rasi` to reference a different existing theme file (e.g. `void-dragon.rasi`).

### Artifact check
```bash
find ~/.config ~/.local/share -name "*<theme-name>*" 2>/dev/null
# Should return empty. If not, remove or overwrite those files.
```

## Step 6 — Flush KDE live color cache (CRITICAL)

Even after all files are correctly restored, plasmashell may still render the old
theme's colors because the color scheme is cached in the running process. If folder
icons, window decorations, or UI elements still show rice colors after restore:

```bash
# Force restart plasmashell to flush in-memory color state
kquitapp6 plasmashell 2>/dev/null; sleep 1; killall plasmashell 2>/dev/null
# Then relaunch (as background process from agent terminal)
plasmashell  # background=true
sleep 4 && pgrep plasmashell && echo "plasmashell running"
```

This is the root cause when "configs are correct but screen still shows old colors."
Dolphin and other apps should also be restarted to pick up the live session change.

Also note: `kscreenlockerrc` is NOT in the baseline backup. The rice modifies it to
set the lock screen wallpaper and theme. After restore, check it manually:
```bash
cat ~/.config/kscreenlockerrc
# Expected: Theme=org.kde.breezedark.desktop, stock wallpaper image
# If it has rice theme/wallpaper, reset manually:
kwriteconfig6 --file kscreenlockerrc --group Greeter --key Theme "org.kde.breezedark.desktop"
```

## Step 7 — Mark session as undone

```bash
echo "## UNDONE" >> ~/.config/rice-sessions/<thread-id>/session.md
echo "Session undone $(date). Restored from baseline <timestamp>." >> \
  ~/.config/rice-sessions/<thread-id>/session.md
```

---

## Notes

- This procedure was validated against session `rice-20260501-0021-d8a9db`
  (mossgrown-throne, KDE Plasma 6 Wayland, 2026-05-01).
- The `ricer_undo.py` script handles the same flow but uses the manifest JSON,
  not the baseline JSON. Baseline restore is the fallback for headless/broken
  manifests.
- Config changes that take effect immediately: kitty (on next launch),
  starship (on next shell), fastfetch (on next run), KDE color scheme (live).
- Config changes that require re-login: cursor theme, GTK theme in some apps.
