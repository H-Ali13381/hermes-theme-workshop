# KDE Wallpaper

## Setting Wallpaper

```bash
plasma-apply-wallpaperimage /path/to/wallpaper.png
```

This updates `~/.config/plasma-org.kde.plasma.desktop-appletsrc` with the new `Image=` path.

## Wallpaper Generation via image_gen

Use the native `image_gen` tool. Always use background mode (generation takes 10-30s):

```bash
terminal(background=True, notify_on_complete=True,
         command='hermes chat -Q -q "Use image_gen to generate: <prompt>" 2>/dev/null')
```

After generation:
```bash
plasma-apply-wallpaperimage /path/to/output.png
```

### Prompt Tips

- Describe the character/theme first, then mood/lighting
- Specify aspect ratio: "16:9 widescreen wallpaper composition"
- Include palette language: "deep void-blue-black background, cyan energy glow, gold filigree border"
- Style anchors: "dark fantasy digital painting, cinematic lighting, highly detailed"

## Finding Wallpapers

| Source | Notes |
|--------|-------|
| **WallHaven** (wallhaven.cc) | Massive curated collection; filter by hex color — paste your palette's background color to find matching wallpapers |
| **Unsplash** (unsplash.com) | High-quality free photos; good for atmospheric/nature themes |
| **r/wallpaper**, **r/wallpapers** | Community submissions; broad variety |
| **KDE Store** (store.kde.org) | Plasma-specific packs, dynamic wallpapers |
| **Bing Daily** | Daily high-quality photo; available as a KDE Plasma plugin |

WallHaven's color filter is particularly useful for ricing: search for any hex color and it returns wallpapers dominated by that hue. Use your palette's `background` color to find wallpapers that will feel coherent with the rest of the theme.

---

## Palette Extraction Integration

Extract a design system palette from the wallpaper:

```bash
ricer extract --image /path/to/wallpaper.png --out design.json --name my-theme
```

Or extract and apply in one step:
```bash
ricer apply --wallpaper /path/to/wallpaper.png --extract
```

### Inline Preview (kitty)

When `TERM=xterm-kitty`, display the wallpaper inline before printing the palette:

```python
import os, subprocess
if os.environ.get("TERM") == "xterm-kitty":
    subprocess.run(["kitty", "+kitten", "icat", wallpaper_path])
```

## Snapshot

The wallpaper path is captured from `Image=` in `~/.config/plasma-org.kde.plasma.desktop-appletsrc` during `snapshot_kde_state()`.

## Video / Animated Wallpaper on KDE Plasma 6 (Wayland)

`org.kde.video` is listed by `plasmapkg2 --list-types` but is NOT a real wallpaper package
on a base KDE install. Setting it via qdbus6 produces "no valid package loaded" in plasmashell
logs and nothing visible on screen. Do NOT use it.

### Correct approach — Smart Video Wallpaper Reborn (AUR)

Install:
```bash
yay -S plasma6-wallpapers-smart-video-wallpaper-reborn
# Requires mpv as backend:
sudo pacman -S mpv
```
Plugin ID after install: `luisbocanegra.smart.video.wallpaper.reborn`

Set via qdbus6:
```bash
WALLPAPER="/path/to/video.mp4"
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {
    var d = allDesktops[i];
    d.wallpaperPlugin = 'luisbocanegra.smart.video.wallpaper.reborn';
    d.currentConfigGroup = ['Wallpaper', 'luisbocanegra.smart.video.wallpaper.reborn', 'General'];
    d.writeConfig('VideoUrls', '$WALLPAPER');
    d.writeConfig('MuteAudio', true);
    d.writeConfig('FillMode', 2);
    d.writeConfig('PauseVideo', false);
    d.writeConfig('BackgroundColor', '#000000');
}
print('Done');
"
```

Verify install:
```bash
ls /usr/share/plasma/wallpapers/ | grep luisbocanegra
# should show: luisbocanegra.smart.video.wallpaper.reborn
```

### Other AUR video wallpaper options (Plasma 6, confirmed Apr 2026)
- `plasma6-wallpapers-smart-video-wallpaper-reborn` — best maintained, Plasma 6 native ✓
- `plasmavideowallpaper-git` — alternative, less active
- `ghostlexly-gpu-video-wallpaper` — GPU-accelerated variant

### mpvpaper — NOT for KDE
mpvpaper targets wlroots compositors (Hyprland, Sway) only. Does not work on KDE Wayland.

---

## Pitfalls

- **`hermes chat -Q -q` will time out** on image generation in foreground mode. Always use `terminal(background=True, notify_on_complete=True)`.
- **Wallpaper changed manually** (outside ricer) will not be restored by undo — undo restores the snapshot-time value.
- **Do NOT use matplotlib or PIL** for wallpaper generation — `image_gen` produces dramatically better results.
- **`org.kde.video` is a trap** — appears in plugin type listings but is not an installed wallpaper package. Setting it silently fails with "no valid package loaded" in journalctl. Use `luisbocanegra.smart.video.wallpaper.reborn` instead.
- **yay AUR installs need a real TTY** — `yay -S` silently fails at the sudo step when invoked without a terminal. Tell the user to run it themselves.
