# Cursor Theme

## Installation

Cursor themes are installed to `~/.local/share/icons/` or `/usr/share/icons/`.

On Arch with Catppuccin cursors:
```bash
yay -S catppuccin-cursors-macchiato
```

Check installed cursor themes:
```bash
find /usr/share/icons ~/.local/share/icons -maxdepth 1 -name "*cursor*" -type d
```

## Activation

Two commands are needed for full activation:

```bash
# Apply via Plasma
plasma-apply-cursortheme "catppuccin-macchiato-teal-cursors"

# Also write to kcminputrc for persistence
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "catppuccin-macchiato-teal-cursors"
```

**Note:** KDE shows a confirmation popup about system-wide SDDM apply. Normal — dismiss as preferred.

## GTK Sync

Ensure GTK apps also use the cursor theme by setting it in both `settings.ini` files:

```ini
# ~/.config/gtk-3.0/settings.ini and ~/.config/gtk-4.0/settings.ini
[Settings]
gtk-cursor-theme-name=catppuccin-macchiato-teal-cursors
gtk-cursor-theme-size=24
```

## Undo

Restore the previous cursor theme from the snapshot:
```bash
plasma-apply-cursortheme "breeze_cursors"
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme "breeze_cursors"
```

## Pitfalls

- **Every preset must include `cursor_theme`.** Without it, the materializer falls back to "default" which looks inconsistent.
- **Cursor theme names are case-sensitive** and must match the directory name exactly.
- **Some cursor themes need a relogin** for SDDM/login screen to pick up the change.
