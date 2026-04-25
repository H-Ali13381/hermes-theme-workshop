# Wallpaper Generation & Style Transfer

> **Animated wallpaper pipeline (4 time-of-day variants via FAL + Seedance) → `dev/DESIGN_PHILOSOPHY.md §The Wallpaper System`**
> This is the primary pipeline for ricing sessions. The sections below cover static generation and style transfer tools used within it.

---

## Animated Wallpaper Pipeline (Primary)

Full spec is in `dev/DESIGN_PHILOSOPHY.md §The Wallpaper System`. Summary:

### Prerequisites
- `FAL_KEY` set in `~/.bashrc` / `~/.zshrc` (not `~/.hermes/.env` — confirmed Apr 2026)
- Animated engine — depends on WM:
  - **Hyprland**: `mpvpaper` (AUR) for video loops. `awww`/`swww` for static+transitions.
  - **KDE Plasma Wayland**: use KDE's built-in `org.kde.video` wallpaper plugin via qdbus6.
    Requires `mpv` (`sudo pacman -S mpv`) as the backend. mpvpaper does NOT work on KDE —
    it targets wlroots compositors only.

### Pipeline Overview

1. **Generate 4 static variants** (same composition, different times of day):
   - Dawn — cool light, soft edges, mist
   - Day — full clarity, saturated
   - Dusk — warm golden tones, long shadows
   - Night — deep darks, accent highlights, stars/neon if fitting

   Use `mcp_image_generate` for each variant. Describe the stance and mood explicitly; vary only the lighting.

2. **Animate each** via FAL image-to-video:

   **Recommended model (Apr 2026): Seedance 2.0**

   CRITICAL — `fal_client.result()` is broken for Seedance 2.0. It has a bug where it
   drops the sub-path from deeply nested endpoint IDs, constructing a URL missing
   `/seedance-2.0/image-to-video`, causing 404. `fal_client.status()` works (pure queue
   lookup). Direct REST GET on the result URL also fails. The ONLY working retrieval
   method is `fal_client.subscribe()`:

   ```python
   import fal_client, os, urllib.request

   os.environ['FAL_KEY'] = '<your_key>'

   result = fal_client.subscribe(
       "bytedance/seedance-2.0/image-to-video",   # no "fal-ai/" prefix — official ID
       arguments={
           "prompt": "Gentle atmospheric motion. Seamless loop. No camera movement.",
           "image_url": "<uploaded_image_url>",
       },
       with_logs=True,
   )
   video_url = result['video']['url']   # shape: {"video": {"url": "..."}, "seed": N}
   urllib.request.urlretrieve(video_url, 'output.mp4')
   ```

   **Seedance endpoint history (all probed Apr 2026):**
   - `fal-ai/seedance-*` → 404 (wrong namespace)
   - `fal-ai/bytedance/seedance-1-lite` → works for v1 (normal result() retrieval OK)
   - `bytedance/seedance-2.0/image-to-video` → works for v2 (**subscribe only**)

   **Other confirmed working models (Apr 2026) — normal queue+result retrieval:**
   - `fal-ai/kling-video/v1.6/pro/image-to-video` — fields: `prompt`, `image_url`, `duration` ("5"), `aspect_ratio` ("16:9")
   - `fal-ai/wan-pro/image-to-video` — fields: `prompt`, `image_url`; optional `num_frames`, `resolution`, `num_inference_steps`
   - `fal-ai/minimax-video/image-to-video` — fields: `prompt`, `image_url`

   **Multi-model racing pattern:** Submit all models in parallel via queue, download all
   results, let the user pick best per theme. ~$0.10-0.30 total. Especially valuable for
   organic/surrealist imagery where model differences are dramatic. Note: Seedance 2.0 must
   use subscribe() (blocking), so race it sequentially or in a thread alongside queue jobs.

   **FAL endpoint discovery pattern:**
   POST empty `{}` to `https://queue.fal.run/<endpoint>` — interpret response as:
   - 404 = endpoint doesn't exist
   - 422 = endpoint valid, auth passed, missing required fields (check error.detail)
   - 200 IN_QUEUE = accepted (cancel immediately if probe; cancel may return 400/405 — not fatal)

3. **Store**:
   ```
   ~/.config/wallpapers/<theme-name>/dawn.mp4
   ~/.config/wallpapers/<theme-name>/day.mp4
   ~/.config/wallpapers/<theme-name>/dusk.mp4
   ~/.config/wallpapers/<theme-name>/night.mp4
   ```

4. **Schedule** — Hermes cron job swaps based on system time:
   ```bash
   # Example cron entry (times are user-configurable)
   # 06:00 dawn  09:00 day  18:00 dusk  21:00 night
   hermes cron create "Set wallpaper to dawn variant: awww img ~/.config/wallpapers/<theme>/dawn.mp4" --schedule "0 6 * * *"
   ```
   `awww` handles transitions (fade/wipe/grow); `mpvpaper` plays the video loop.

### Fallback (FAL not available)
- Use static wallpaper only (single image, `awww img`)
- Skip Seedance step; store `.png` instead of `.mp4`
- Revisit animated pipeline after FAL key is configured

---

## image_gen Wallpaper Generation

Use the native `image_gen` tool (configured in Hermes settings). Do NOT use matplotlib or PIL.

### Check Configuration
```bash
hermes tools   # image_gen should appear in the list
```

### Invoking image_gen

Always use background mode — generation takes 10-30s:

```python
terminal(background=True, notify_on_complete=True,
         command='hermes chat -Q -q "Use image_gen to generate: <prompt>" 2>/dev/null')
```

### Prompt Tips
- Describe character/theme first, then mood/lighting
- Specify aspect ratio: "16:9 widescreen wallpaper composition"
- Include palette language: "deep void-blue-black background, cyan energy glow"
- Style anchors: "dark fantasy digital painting, cinematic lighting, highly detailed"

---

## fal.ai Style Transfer

### Model Comparison

| Model | Two-image input | Structure preservation | Style method |
|-------|----------------|----------------------|-------------|
| `fal-ai/image-apps-v2/style-transfer` | YES — `style_reference_image_url` | Moderate | Reference image OR preset enum |
| `fal-ai/flux-pro/kontext` | No — one image + prompt | Excellent | Natural language prompt |
| `fal-ai/image-editing/style-transfer` | No — one image + prompt | Weak (full repaint) | Text only |

### Two-Stage Pipeline

**Stage 1 — Style transfer:**
```
fal-ai/image-apps-v2/style-transfer
  image_url: <toolbar screenshot>
  style_reference_image_url: <reference image>
```

**Stage 2 — Layout cleanup (if Stage 1 drifts):**
```
fal-ai/flux-pro/kontext
  image_url: <stage 1 output>
  prompt: "Restore widget layout to match original. Keep texture and borders."
  guidance_scale: 3.5   # keep low
```

Total cost: ~$0.08 for both calls.

### Uploading Local Images to fal.ai

```python
import urllib.request, json, os

def upload_to_fal(path, fal_key):
    ext = path.split(".")[-1]
    mime = {"png": "image/png", "jpg": "image/jpeg"}.get(ext, "image/png")
    with open(path, "rb") as f:
        data = f.read()
    # Initiate upload
    req = urllib.request.Request(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        data=json.dumps({"file_name": os.path.basename(path), "content_type": mime}).encode(),
        headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        info = json.loads(r.read())
    # PUT to signed URL
    put_req = urllib.request.Request(
        info["upload_url"], data=data, method="PUT",
        headers={"Content-Type": mime}
    )
    urllib.request.urlopen(put_req, timeout=60)
    return info["file_url"]
```

Use `queue.fal.run` for submission — NOT `fal.run`. Load `FAL_KEY` from `~/.hermes/.env`.

---

## AI-Generated UI Chrome

Wallpaper is not the only visual element that benefits from AI generation:

| Target | What to Generate | Output Format |
|--------|-----------------|---------------|
| Frame overlay | Ornamental border, transparent interior | PNG with alpha, monitor res |
| Panel background | Textured strip (parchment, stone, carbon) | PNG, crop to bar height |
| Window titlebar | Full-width decorative image | SVG or PNG, ~62px tall |
| Login screen | Full background with theme character art | JPG, exact monitor res |
| Lock screen | Wallpaper variant with blur/dim | PNG |

### Frame Overlay Prompt Template

```
"<theme-style> ornamental border frame, full screen, transparent interior void center,
 <material> texture carvings, <decorative-elements> at corners and edges,
 symmetric, no text, ultra detailed, <palette-color> tones"
```

## Making Frame Art Transparent

```python
from PIL import Image
img = Image.open("frame.png").convert("RGBA")
data = img.load()
for y in range(img.height):
    for x in range(img.width):
        r, g, b, a = data[x, y]
        if r > 240 and g > 240 and b > 240:
            data[x, y] = (r, g, b, 0)
img.save("frame_transparent.png")
```

Adjust threshold based on interior color. For non-white interiors, use a specific chroma-key color.
