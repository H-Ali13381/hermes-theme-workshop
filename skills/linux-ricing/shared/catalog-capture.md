# Screenshot Catalog Builder

Build real screenshot catalogs for comparing ricing options by applying one isolated customization at a time.

## Core Principle: Isolate One Variable

For a useful comparison, keep the scene fixed and change only ONE variable:

- ✅ Restore known baseline → apply ONE layer → screenshot → restore baseline → repeat
- ❌ Apply multiple layers at once, screenshot from different wallpapers/layouts

## Capture Baseline

Recommended KDE baseline for dark-theme reference shots:

| Setting | Value |
|---------|-------|
| Colorscheme | `BreezeDark` |
| Look-and-feel | `org.kde.breezedark.desktop` |
| Plasma theme | `default` |
| Cursor | `breeze_cursors` |
| Icon theme | `breeze-dark` |
| Widget style | `Breeze` |
| Wallpaper | `/usr/share/wallpapers/Next/contents/images_dark/5120x2880.png` |

**Important:** A config-level baseline is NOT enough. Standardize wallpaper, icons, panel launchers, and scene preparation too.

## 8-Step Batch Loop

For every option in the catalog:

1. **Restore baseline explicitly** (don't rely on undo alone)
2. **Apply one option**
3. **Verify the change landed**
4. **Prepare capture scene** (open reference windows, close strays)
5. **Capture screenshot(s)**
6. **Save into option's catalog folder**
7. **Restore baseline explicitly again**
8. **Verify baseline is back**, then move to next option

## Capture Scene

Before screenshots, create a stable comparison scene:
- Konsole open with fixed sample text
- PyQt6 reference window with buttons, inputs, tabs, checkboxes, sliders
- Panel visible in fixed position
- Same workspace, window sizes, monitor, and crop every time

The reference window helper: `~/.hermes/skills/creative/linux-ricing/scripts/reference_capture_window.py`

## Wayland Multi-Monitor Capture

On Wayland with mixed-DPI monitors, `spectacle` behaves unexpectedly:

- `spectacle --fullscreen` → captures ALL monitors at 2x DPR (correct starting point)
- `spectacle --current` → captures FOCUSED monitor (wrong — captures terminal, not reference)
- `spectacle --activewindow` → captures only reference window (missing panel/desktop context)

**Correct approach:** `spectacle --fullscreen` + PIL crop + resize:

```python
from PIL import Image
img = Image.open("screenshot.png")
# DP-1 at logical (0,0) 1920x1080 with 2x DPR:
crop = img.crop((0, 0, 3840, 2160))
preview = crop.resize((1920, 1080), Image.LANCZOS)
preview.save("preview.png")
```

DPR factor = actual screenshot dimensions ÷ total logical canvas size.

## KWin D-Bus Scripting (Window Placement)

On Wayland, Qt's `raise_()`, `activateWindow()`, `move()` are ALL silently ignored. Use KWin D-Bus scripting:

```javascript
// KWin JS script
var clients = workspace.windowList();
for (var i = 0; i < clients.length; i++) {
    if (clients[i].caption.indexOf("Hermes Ricer Reference") !== -1) {
        var c = clients[i];
        var newX = Math.round((1920 - c.width) / 2);
        var newY = Math.round((1080 - c.height) / 2);
        c.frameGeometry = {x: newX, y: newY, width: c.width, height: c.height};
        c.minimized = false;
        workspace.activeWindow = c;
        break;
    }
}
```

Load and run:
```bash
SCRIPT_ID=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript /path/to/script.js hermes_raise)
qdbus6 org.kde.KWin "/Scripting/Script${SCRIPT_ID}" run
sleep 0.5
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript hermes_raise
```

## Catalog Output Structure

```
~/.hermes/skills/creative/linux-ricing/assets/catalog/
  kvantum/
    catppuccin-mocha-teal/
      preview.png         # primary comparison image
      full.png            # optional full desktop capture
      README.md           # what this option is
      metadata.json       # machine-readable info
    catppuccin-mocha-mauve/
      preview.png
      README.md
  cursors/
    catppuccin-macchiato-teal-cursors/
      preview.png
      README.md
  palettes/
    void-dragon/
      preview.png
      README.md
```

## Running the Capture Script

```bash
# Dry run
python3 ~/.hermes/skills/creative/linux-ricing/scripts/capture_theme_references.py \
  --category kvantum --dry-run

# Capture specific themes
python3 ~/.hermes/skills/creative/linux-ricing/scripts/capture_theme_references.py \
  --category kvantum --option catppuccin-mocha-teal --option catppuccin-mocha-mauve

# Capture cursors
python3 ~/.hermes/skills/creative/linux-ricing/scripts/capture_theme_references.py \
  --category cursors
```

**WARNING:** This restarts plasmashell and changes the desktop between each capture.
