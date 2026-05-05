# Reference-Grounded Desktop Overviews

Use this when Step 2.5 / preview quality drifts into generic AI fantasy art, wallpaper thinking, or cinematic letterboxed mockups.

## Correct hierarchy

1. **Real image references first**
   - Game/menu/UI screenshots and artwork are grounding evidence.
   - Extract visual grammar: border thickness, menu hierarchy, surface materials, icon/glyph silhouettes, ornament density, lighting, panel layering, and spatial hierarchy.
   - References are **not wallpapers** unless the user explicitly selects one as wallpaper.

2. **Generated representative overview second**
   - The generated image is a synthesized desktop overview concept, not the sole source of truth.
   - Prefer terms like `representative overview image` or `desktop overview concept`; avoid overusing `hero image` because it nudges models toward cinematic poster framing.
   - It should show the OS shell: wallpaper/background treatment, windows, terminal, launcher/menu, panel/widgets, borders, icons/glyphs, and app chrome.

3. **Implementation third**
   - Implement elements from both the real-reference grammar and the generated overview.
   - If the generated overview conflicts with concrete references or user-stated taste, references/user direction outrank the generated concept.

## Black bar / letterbox pitfall

A generated overview can contain black bars baked into the image. Check the image itself, not just the HTML CSS.

Quick probe:

```bash
python3 - <<'PY'
from PIL import Image
import numpy as np
p='/path/to/generated-overview.png'
img=Image.open(p).convert('RGB')
arr=np.array(img)
lum=arr.mean(axis=2)
row=lum.mean(axis=1)
print('size', img.size, 'aspect', img.size[0]/img.size[1])
for th in [10,15,20,25,30,40]:
    top=0
    while top<len(row) and row[top]<th: top+=1
    bot=0
    while bot<len(row) and row[-1-bot]<th: bot+=1
    print('threshold', th, 'top dark rows', top, 'bottom dark rows', bot)
PY
```

If bands exist, patch prompt/feedback with:
- `Fill the canvas edge-to-edge with the desktop overview`
- `no cinematic letterbox bars`
- `no black bands above or below`
- `no framed movie-still presentation`

## Aspect ratio pitfall

Do not assume 16:9 represents the target desktop.

- A single 2560x1440 monitor is 16:9.
- A multi-monitor virtual desktop may be ultrawide (example observed: 4096x1764 = 2.322:1).
- The workflow should make the target explicit: primary monitor, full virtual desktop, or per-monitor assets.

Use live display geometry (`kscreen-doctor -o` on KDE) before judging whether an overview should fill the user's screen.

## Widget framework pitfall on KDE Wayland

If custom panel/widget chrome is required on KDE Wayland, Quickshell should be evaluated before sinking time into EWW. EWW failures such as Yuck `calc()` geometry rejection, `$1/$2` shell interpolation getting eaten, empty first-render progress values, and missing helper commands are signals to switch/re-evaluate rather than endlessly patch EWW.

Preferred framework policy:
- KDE Wayland / Hyprland: Quickshell default when available.
- KDE X11 / unknown / explicit fallback: EWW.
- If a design/session unexpectedly selects `widgets:eww` on KDE Wayland, investigate framework selection before implementing.
