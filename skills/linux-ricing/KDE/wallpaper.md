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

## Pitfalls

- **`hermes chat -Q -q` will time out** on image generation in foreground mode. Always use `terminal(background=True, notify_on_complete=True)`.
- **Wallpaper changed manually** (outside ricer) will not be restored by undo — undo restores the snapshot-time value.
- **Do NOT use matplotlib or PIL** for wallpaper generation — `image_gen` produces dramatically better results.
