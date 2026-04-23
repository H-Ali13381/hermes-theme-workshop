---
name: ricer-catalog-capture
description: "Create a real screenshot catalog for Linux ricing options by resetting to a fixed KDE baseline, applying one isolated customization, capturing the result, restoring baseline, and repeating. Use when building user-facing comparison references for Kvantum themes, cursor themes, colorschemes, Plasma themes, or other desktop customization layers."
---

# ricer-catalog-capture

Use this when the goal is to help a user compare real customization options before choosing what to apply.

## Quick Reference — Just Run It

Scripts are already implemented and working. For most uses, just run:

    # Dry run (shows plan, no desktop changes):
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/capture_theme_references.py \
      --category kvantum --dry-run

    # Capture all default Kvantum themes:
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/capture_theme_references.py \
      --category kvantum

    # Capture all default cursor themes:
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/capture_theme_references.py \
      --category cursors

    # Capture specific themes:
    python3 ~/.hermes/skills/creative/hermes-ricer/scripts/capture_theme_references.py \
      --category kvantum --option catppuccin-mocha-teal --option catppuccin-mocha-mauve

Output: `~/.hermes/skills/creative/hermes-ricer/assets/catalog/<category>/<option>/preview.png`

WARNING: This restarts plasmashell and changes the desktop between each capture. The user's desktop will flicker. Run as a background job with notify_on_complete.

To expand beyond defaults, edit `DEFAULT_KVANTUM_OPTIONS` / `DEFAULT_CURSOR_OPTIONS` in the script, or pass `--option` flags.

This is NOT the same as generating mockups. Mockups are fine for rough planning, but they are not trustworthy enough for a real decision catalog. The correct method is to capture real screenshots from the actual desktop after applying each option in isolation.

## Core Principle

For a useful comparison catalog, keep the scene fixed and change only ONE variable at a time.

Bad:
- applying multiple theme layers at once and calling it a "Kvantum preview"
- taking screenshots from different wallpapers, window layouts, or panel states
- chaining apply/undo blindly and assuming the baseline is still clean

Good:
- restore a known baseline explicitly
- apply one customization layer only
- verify the change landed
- screenshot the exact same scene
- restore baseline explicitly again
- repeat

## Recommended Capture Baseline

Pick one neutral baseline and keep it constant across the entire batch.

Recommended KDE baseline for dark-theme reference shots:
- Colorscheme: `BreezeDark`
- Look-and-feel package: `org.kde.breezedark.desktop`
- Plasma theme: `default`
- Cursor: `breeze_cursors`
- Icon theme: `breeze-dark`
- Widget style: `Breeze`
- Kvantum config reset to a neutral baseline before each shot
- Wallpaper: one fixed stock KDE wallpaper for all captures (e.g. `/usr/share/wallpapers/Next/contents/images_dark/5120x2880.png`)
- Simplified, standardized panel launcher list so the panel reads as "default KDE" to a human viewer
- Same windows, same geometry, same monitor, same crop for every screenshot

Important experiential finding: a config-level baseline is NOT enough. Users judge "default KDE look" visually, so baseline standardization must include wallpaper, icons, panel launchers, plasmashell refresh, and scene preparation — not just colorscheme/cursor/theme keys.

Important finding: icon theme MUST be part of the baseline. Panel/task icons, desktop icons, launcher icons, and file-manager visuals all drift with the icon theme. If icons are not standardized, the catalog no longer isolates the customization under test.

You do NOT need to uninstall or delete themes. Reset to a known baseline instead.

## Correct Batch Loop

Use this control flow for every option in the catalog:

1. Restore baseline explicitly
2. Apply one option
3. Verify the change landed
4. Capture screenshot(s)
5. Save into the option's catalog folder
6. Restore baseline explicitly again
7. Verify the baseline is back
8. Move to the next option

This is more deterministic than relying only on repeated apply/undo chaining.

## Why Explicit Baseline Restore Beats Blind Undo Chaining

`undo()` is useful, but for a large capture batch it is safer to treat baseline restoration as its own explicit phase.

Why:
- one failed or partial undo can poison all later captures
- KDE state can drift subtly between runs
- screenshot catalogs are only useful if every comparison starts from the same state

Use `undo()` as one restoration tool, but still verify the resulting state against the intended baseline before continuing.

## Best Categories to Capture First

Start with the highest-value, easiest-to-control layers:

1. Kvantum themes
   - biggest visible Qt widget change
   - easiest payoff for comparison

2. Cursor themes
   - concrete installed options
   - easy to categorize, though pointer capture needs special handling

3. KDE colorschemes / palette presets
   - useful, but visually subtler unless paired with widgets or terminal

4. Plasma themes
   - valuable if you truly have multiple real panel themes installed

Defer launchers/notifications until you can standardize their scene too.

## Standardized Capture Scene

Before taking any screenshots, create a stable comparison scene.

Recommended scene for KDE/Qt widget captures:
- Konsole open with fixed sample text
- One Qt settings/demo window open (or another widget-rich app)
- Panel visible in a fixed position
- Same workspace every time
- Same window sizes and placement
- Same monitor and same crop region

The capture scene matters as much as the theme itself. If the scene changes, the comparison quality collapses.

## Catalog Output Structure

Use per-option folders, not one giant image dump.

Example:

    ~/.hermes/skills/creative/hermes-ricer/assets/catalog/
      kvantum/
        catppuccin-mocha-teal/
          preview.png
          full.png
          README.md
          metadata.json
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

Recommended files per option:
- `preview.png` — the primary comparison image
- `full.png` — optional full desktop capture
- `README.md` — what this option is and when to use it
- `metadata.json` — optional machine-readable info (theme name, timestamp, baseline, capture notes)

## Capture Script Responsibilities

A reusable capture script should:
- restore the capture baseline
- apply one isolated theme/customization option
- wait for the UI to settle
- take screenshot(s)
- crop to a standard frame if needed
- save into the correct catalog folder
- restore baseline again
- log success/failure per option

Suggested location:

    ~/.hermes/skills/creative/hermes-ricer/scripts/capture_theme_references.py

## Implemented Capture Script

Location:

    ~/.hermes/skills/creative/hermes-ricer/scripts/capture_theme_references.py

Reference window helper (PyQt6 widget showcase):

    ~/.hermes/skills/creative/hermes-ricer/scripts/reference_capture_window.py

Supports: `--category kvantum`, `--category cursors`

Behavior:
- restores the Breeze Dark capture baseline explicitly before each option
- standardizes default Plasma theme, Breeze cursor, Breeze icons, and Breeze widget style
- applies `plasma-apply-lookandfeel --apply org.kde.breezedark.desktop` for full L&F reset
- sets wallpaper to standard KDE "Next" dark
- rewrites panel launchers to explicit common apps (Firefox, Dolphin, System Settings, Discover, Konsole)
- writes real `.desktop` shortcut files to `~/Desktop/` with proper icons and trust xattrs
- cleans up old placeholder `.txt` files from the desktop
- restarts plasmashell so panel/desktop changes take effect
- opens a standardized PyQt6 reference window with buttons, inputs, tabs, checkboxes, sliders, etc.
- uses KWin D-Bus scripting to move the window to DP-1 and activate it (Qt's own setScreen/move/raise is silently ignored on Wayland — the compositor always places new windows on the focused monitor)
- closes stray GUI windows (image viewers, file managers) that would obscure the reference window
- captures with `spectacle --fullscreen`, crops to DP-1's pixel region at 2x DPR, resizes to 1920x1080
- saves to `assets/catalog/<category>/<option>/preview.png`
- closes the reference window and restores baseline again after capture

## Panel Launcher Configuration

Use explicit `.desktop` file references, NOT `preferred://` aliases.

Bad (generic, shows different icons per distro):

    preferred://filemanager,preferred://browser

Good (explicit, shows the intended app icon every time):

    applications:firefox.desktop,applications:org.kde.dolphin.desktop,applications:systemsettings.desktop,applications:org.kde.discover.desktop,applications:org.kde.konsole.desktop

The panel launcher string is written directly into `appletsrc` via regex replacement of all `launchers=` lines, then plasmashell is restarted.

## Desktop Shortcut Icons — KDE Trust Mechanism

Writing `.desktop` files to `~/Desktop/` is NOT enough for KDE to render them with proper app icons. Without trust metadata, KDE shows them as text file icons.

Required steps for proper icon rendering:
1. Write the `.desktop` file with `[Desktop Entry]` header, Name, Icon, Type, Exec/URL
2. Set executable bit: `chmod +x file.desktop`
3. Set xattr trust marker: `setfattr -n user.xdg.origin.url -v "file:///path/to/file.desktop" file.desktop`
4. Restart plasmashell so the folder view picks up the changes

For Link-type shortcuts (Home, Trash), use `Type=Link` with a `URL=` key instead of `Exec=`.

Clean up any old placeholder files (`.txt` marker files) before capture — they show up as ugly text file icons.

## Monitor Capture Strategy (Wayland Multi-Monitor)

CRITICAL: On Wayland with mixed-DPI monitors, Spectacle capture modes behave unexpectedly:

- `spectacle --fullscreen` captures ALL monitors into one image at 2x DPR backing. A 4320x1755 logical desktop → 6912x2808 pixel image.
- `spectacle --current` captures the monitor of the FOCUSED window, NOT the reference window. Since the capture script runs from a terminal (typically on the secondary monitor), `--current` captures the wrong monitor.
- `spectacle --activewindow` captures only the reference window, missing panel/desktop/wallpaper context.

The correct approach is `spectacle --fullscreen` + PIL crop + resize:
1. Take fullscreen capture (all monitors)
2. Crop to the target monitor's pixel region using 2x DPR math
3. Resize to 1920x1080 for standard output

Example pixel math for DP-1 at logical (0,0) 1920x1080 with 2x DPR:
- Crop region: (0, 0, 3840, 2160) in the fullscreen buffer
- Resize: 3840x2160 → 1920x1080 via PIL LANCZOS

To determine the DPR factor: divide actual screenshot dimensions by total logical canvas size (from kscreen-doctor --outputs geometry values).

Do NOT rely on `spectacle --current` for automated batch capture — focus stays with the launching terminal, not the reference window.

### Reference Window Screen Targeting (Wayland KWin Scripting)

On Wayland, Qt's `raise_()`, `activateWindow()`, and `move()` are ALL silently ignored by KWin. The compositor places new windows on the monitor that currently has focus — typically the terminal running the script (HDMI-A-1), NOT the target capture monitor (DP-1).

Setting the screen by connector name in Qt (`app.screens()` + `win.setScreen()` + `win.move()`) does NOT work on Wayland. The window still opens on the focused monitor. This is true regardless of whether you call `win.move()` before or after `win.show()` — both are ignored. Even `win.setScreen(target_screen)` combined with explicit geometry does nothing. The Qt positioning code in reference_capture_window.py is dead weight on Wayland. This was verified: even with correct DP-1 coordinates passed to `win.move()` before `win.show()`, KWin placed the window on HDMI-A-1 (where the terminal had focus). The Qt positioning code in reference_capture_window.py is dead weight — it does nothing on Wayland. The KWin D-Bus script is the ONLY mechanism that actually moves the window.

The ONLY reliable approach is **KWin D-Bus scripting** to move and activate the window after it opens:

```javascript
// KWin JS script — loaded via qdbus6 org.kde.KWin /Scripting
var clients = workspace.windowList();
for (var i = 0; i < clients.length; i++) {
    if (clients[i].caption.indexOf("Hermes Ricer Reference") !== -1) {
        var c = clients[i];
        // Move to DP-1 coordinates (logical origin 0,0)
        var newX = Math.round((1920 - c.width) / 2);
        var newY = Math.round((1080 - c.height) / 2);
        c.frameGeometry = {x: newX, y: newY, width: c.width, height: c.height};
        c.minimized = false;
        workspace.activeWindow = c;
        break;
    }
}
```

Loading and running via D-Bus:
```bash
SCRIPT_ID=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript /path/to/script.js hermes_raise)
qdbus6 org.kde.KWin "/Scripting/Script${SCRIPT_ID}" run
sleep 0.5
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript hermes_raise
```

Setting `frameGeometry` to coordinates within DP-1's logical geometry (0,0 to 1920x1080) causes KWin to move the window to that monitor. This is the only method that works reliably on Wayland.

### Stray Window Cleanup Before Capture

Any GUI windows left open on DP-1 (from previous `xdg-open` calls, file managers, image viewers) will appear in the fullscreen capture and obscure the reference window. The capture script must close stray windows before each capture:

```python
for proc_name in ["gwenview", "okular", "eog", "feh"]:
    subprocess.run(["pkill", "-f", proc_name], capture_output=True, timeout=5)
subprocess.run(["qdbus6", "org.kde.dolphin", "/dolphin/Dolphin_1", "close"],
               capture_output=True, timeout=5)
```

This is implemented in `close_stray_windows()` in the capture script.

### Debugging Window Placement

To verify which monitor a window is on, use KWin scripting to list all windows:
```bash
# Lists all window captions + their output screen name in KWin journal
cat > /tmp/list_windows.js << 'EOF'
var clients = workspace.windowList();
for (var i = 0; i < clients.length; i++) {
    console.log("Window: " + clients[i].caption + " on " + clients[i].output.name);
}
EOF
SCRIPT_ID=$(qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.loadScript /tmp/list_windows.js hermes_list)
qdbus6 org.kde.KWin "/Scripting/Script${SCRIPT_ID}" run
journalctl --user -u plasma-kwin_wayland -n 20 --no-pager | grep "Window:"
qdbus6 org.kde.KWin /Scripting org.kde.kwin.Scripting.unloadScript hermes_list
```

The target output name is configured in `KDE_CAPTURE_BASELINE["capture_output"]` in capture_theme_references.py.

## Verification Pattern

When adding or changing the capture script, verify it in two layers:

1. unit tests for deterministic logic (paths, slugs, baseline constants)
2. script `--dry-run` output for the real capture plan before mutating the desktop

A good minimal test set covers:
- baseline constant contents
- per-option preview path generation
- option slug normalization

This keeps risky UI-changing work out of the first verification pass.

## Monitor Selection Pitfall

A multi-monitor system can silently invalidate the catalog if the capture lands on the wrong display.

Findings from live testing on Wayland with mixed-DPI monitors:
- `spectacle --fullscreen` captures ALL monitors at 2x DPR — this is the correct starting point, combined with PIL crop + resize
- `spectacle --activewindow` only captures the reference window, missing panel/desktop/wallpaper entirely
- `spectacle --current` captures the monitor of the FOCUSED window (the launching terminal), NOT the reference window — unreliable for batch automation

The correct approach for batch automation:
1. Use `spectacle --fullscreen` to capture everything
2. Crop to the target monitor's pixel region (accounting for 2x DPR backing factor)
3. Resize to 1920x1080 for a standard catalog preview
4. The reference window helper finds the target screen by connector name (e.g. "DP-1") via `QApplication.screens()`, NOT `primaryScreen()` (which Qt may map to the wrong monitor)

## User Expectations vs. Technical Correctness

A major lesson from this session: the user's mental model of "default KDE look" is much richer than just config keys.

When the user says "make it look like a basic KDE PC", they mean:
- Standard wallpaper (not a custom one, not blank)
- Panel with recognizable app icons (Firefox, Dolphin, Settings — not generic `preferred://` aliases)
- Desktop shortcuts with real icons (Home folder icon, Trash can icon — not `.desktop` text files)
- Standard icon theme (Breeze)
- The whole desktop visible in the screenshot, not just a cropped window

Config-only baseline reset (colorscheme, cursor, Kvantum) produces screenshots that look "the same" to the user because the things they actually look at (panel icons, desktop icons, wallpaper) haven't changed.

The correct approach includes ALL of:
1. Theme config reset (colorscheme, cursor, Kvantum, Plasma theme, icon theme)
2. Look-and-feel package application
3. Wallpaper set to stock KDE default
4. Panel launchers rewritten to explicit common apps
5. Desktop shortcuts created as proper `.desktop` files with trust xattrs
6. Plasmashell restart so changes are visually reflected
7. Close stray GUI windows that might obscure the reference window
8. Launch the reference window subprocess, then use KWin D-Bus scripting to move it to DP-1 and activate it (Qt's own move/raise is ignored on Wayland)
9. Fullscreen capture via `spectacle --fullscreen` + crop to target monitor (DP-1) at 2x DPR + resize to 1920x1080

Skipping any of these produces technically-correct-but-visually-useless reference images.

## Visible-Difference Pitfall

A theme change can apply correctly yet produce a bad reference screenshot if the scene does not contain the UI elements that actually demonstrate the difference.

Important finding from live testing:
- Kvantum captures look like "nothing changed" if you only shoot a generic desktop screen
- writing config + reconfiguring KWin is not enough; you need a widget-rich reference scene
- `--activewindow` captures ONLY the reference window — the user loses panel/desktop context
- the solution is fullscreen capture with the reference window open ON TOP of the desktop

Therefore, before capturing Kvantum or similar widget-layer changes:
1. Open a dedicated PyQt6 reference window (buttons, inputs, tabs, checkboxes, sliders, progress bars, menus, toolbars)
2. Position it on the target capture monitor by connector name (e.g. "DP-1"), NOT primaryScreen()
3. Capture with `spectacle --fullscreen` + crop to target monitor's pixel region so the panel, desktop icons, wallpaper, AND reference window are all visible

The reference window helper is at:

    ~/.hermes/skills/creative/hermes-ricer/scripts/reference_capture_window.py

It accepts `--category kvantum --theme-name <name>` or `--category cursors --theme-name <name>`.
The capture script launches it as a subprocess, waits for focus settle, captures, then terminates it.

## Anti-Pattern: Over-Engineering Tests Before Running the Actual Thing

A major process failure in this session: writing dozens of test functions for scene metadata, payload structures, and README content BEFORE ever running a real capture and checking the visual result.

The correct order is:
1. Run one real capture manually
2. Look at the screenshot with your eyes (or vision tool)
3. Fix what looks wrong
4. THEN codify the working approach into tests

Writing 50+ tests for constants and payloads does not help if the screenshot itself is wrong.
The user doesn't care about metadata.json — they care about what the PNG looks like.

## Safety Notes

Before running a large capture batch:
- ensure the user has a backup strategy in place
- prefer the deterministic ricing safety stack
- avoid destructive system-level changes just to make the baseline "clean"

Reset to baseline. Do not "wipe themes" by deleting packages or files.

## Practical Recommendation

Do a small pilot batch before scaling up.

Best first pilot:
- 4 Kvantum themes
- 4 cursor themes

Validate:
- baseline restore reliability
- screenshot consistency
- folder structure
- naming convention
- whether the images are actually decision-useful

Only then expand to the full installed theme set.
