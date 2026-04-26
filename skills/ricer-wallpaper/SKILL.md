---
name: ricer-wallpaper
description: "Wallpaper generation and palette extraction for hermes-ricer. Load when generating AI wallpapers via image_gen, applying style transfer via fal.ai, or extracting a design system palette from a reference image."
---

# ricer-wallpaper — Wallpaper Generation and Palette Extraction

Part of the hermes-ricer suite.

---

## Wallpaper Generation via image_gen

Use the native `image_gen` tool (configured in Hermes settings). This produces
dramatically better results than any programmatic approach (matplotlib, PIL, etc.).

### Check configuration first

    hermes tools   # image_gen should appear in the list

If `image_gen` is not configured, tell the user:
> "Wallpaper generation requires image_gen to be set up. Run `hermes tools`,
> enable image_gen, and set a model (fal-ai/nano-banana-pro recommended).
> Then come back and I'll generate it."

Do NOT attempt programmatic generation with matplotlib or other Python graphics libraries.

### Invoking image_gen

The image_gen tool lives in Hermes' own venv — not callable from system Python.
Invoke it via a hermes chat call.

ALWAYS use `background=True` with `notify_on_complete=True` — generation takes 10-30s
and will time out in foreground mode:

    terminal(background=True, notify_on_complete=True,
             command='hermes chat -Q -q "Use image_gen to generate: <prompt>" 2>/dev/null')

After generation:

    plasma-apply-wallpaperimage /path/to/output.png

### Prompt tips for themed wallpapers

- Describe the character/theme first, then the mood/lighting
- Specify aspect ratio: "16:9 widescreen wallpaper composition"
- Include color language from the palette: "deep void-blue-black background, cyan energy glow, gold filigree border"
- Style anchors: "dark fantasy digital painting, cinematic lighting, highly detailed"

---

## Image-to-Palette Workflow

Extract a full 10-key design system palette from any image (wallpaper, artwork, screenshot).

### Automated extraction (preferred)

Use the `ricer extract` CLI — backed by `scripts/palette_extractor.py` (Pillow-based, no extra deps):

    # Extract palette to stdout (JSON)
    ricer extract --image /path/to/image.png

    # Extract and write to a file
    ricer extract --image /path/to/image.png --out ~/my-theme.json --name my-theme

    # Extract palette from wallpaper AND apply it in one step
    ricer apply --wallpaper /path/to/image.png --extract

    # Dry-run: preview all changes without writing anything
    ricer apply --wallpaper /path/to/image.png --extract --dry-run

The extractor pipeline: alpha-composite → thumbnail → quantize (MAXCOVERAGE, fallback MEDIANCUT) →
classify into 6 ricemood buckets → assign 10 semantic slots with fallback cascades → validate contrast
+ uniqueness → infer mood tags. Deterministic: same image always produces identical output.

### Manual extraction (fallback when Pillow is unavailable)

If `ricer extract` fails (Pillow not installed), use a vision subagent as a fallback:

    delegate_task(toolsets=["vision", "file"])

Prompt the subagent to analyze the image in 4 passes (background/environment, subject colors,
accent/glow, decorative elements) and synthesize a 10-key palette:
`background, foreground, primary, secondary, accent, surface, muted, danger, success, warning`

Then paste the resulting JSON into `ricer apply --design <path>`.

---

## Style Transfer via fal.ai

When generating a mockup of the panel in a target visual style, use AI style transfer.

### Model comparison (verified from OpenAPI schemas)

| Model | Two-image input | Structure preservation | How style is set |
|-------|----------------|----------------------|----------------|
| `fal-ai/image-apps-v2/style-transfer` | YES — `style_reference_image_url` | Moderate (layout may drift) | Reference image OR preset enum |
| `fal-ai/flux-pro/kontext` | No — one image + prompt | Excellent | Natural language prompt |
| `fal-ai/image-editing/style-transfer` | No — one image + prompt | Weak (full repaint) | Text description only |

Use `fal-ai/image-apps-v2/style-transfer` for reference-image style transfer.
Use `fal-ai/flux-pro/kontext` for layout cleanup or prompt-guided edits.

### Two-stage recommended pipeline

Stage 1 — style transfer:

    fal-ai/image-apps-v2/style-transfer
    inputs:
      image_url: <screenshot of your toolbar>
      style_reference_image_url: <reference image showing the target style>

Stage 2 — layout cleanup (if Stage 1 drifts widget positions):

    fal-ai/flux-pro/kontext
    inputs:
      image_url: <stage 1 output>
      prompt: "Restore the widget layout to match the original toolbar exactly.
               Keep the texture and borders. Do not change icon positions or panel height."
      guidance_scale: 3.5   # keep low — high values hallucinate new content

Total cost: ~$0.08 for both calls.

### image-apps-v2/style-transfer full input schema

    image_url                  [required]  Content image (toolbar screenshot)
    style_reference_image_url  [optional]  Style reference — overrides target_style when set
    target_style               [optional]  Preset fallback enum (impressionist, pixel_art,
                                           dark_academia, concept_art, digital_art, anime, etc.)
    aspect_ratio               [optional]  For 4K output

### flux-pro/kontext full input schema

    image_url        [optional]  Content image
    prompt           [optional]  Edit instruction (natural language)
    guidance_scale   [optional, 1-20, default 3.5]
    num_images       [optional, 1-4]
    output_format    [optional, jpeg|png]

---

## Uploading Local Images to fal.ai

fal.ai API calls require URLs — local files must be uploaded first.
Load `FAL_KEY` from `~/.hermes/.env`.

```python
import urllib.request, json, os

def upload_to_fal(path, fal_key):
    ext = path.split(".")[-1]
    mime = {"png": "image/png", "jpg": "image/jpeg"}.get(ext, "image/png")
    with open(path, "rb") as f:
        data = f.read()
    # Step 1: initiate upload
    req = urllib.request.Request(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        data=json.dumps({"file_name": os.path.basename(path), "content_type": mime}).encode(),
        headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        info = json.loads(r.read())
    # Step 2: PUT to signed URL
    put_req = urllib.request.Request(
        info["upload_url"], data=data, method="PUT",
        headers={"Content-Type": mime}
    )
    with urllib.request.urlopen(put_req, timeout=60) as r:
        pass
    return info["file_url"]   # use this in subsequent API calls
```

Then submit and poll:

```python
# Submit
payload = {"image_url": toolbar_url, "style_reference_image_url": style_url}
req = urllib.request.Request(
    "https://queue.fal.run/fal-ai/image-apps-v2/style-transfer",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Key {fal_key}", "Content-Type": "application/json"}
)
with urllib.request.urlopen(req, timeout=30) as r:
    job = json.loads(r.read())

status_url = job["status_url"]
response_url = job["response_url"]

# Poll every 3s
import time
for _ in range(30):
    time.sleep(3)
    req2 = urllib.request.Request(status_url, headers={"Authorization": f"Key {fal_key}"})
    with urllib.request.urlopen(req2, timeout=15) as r:
        status = json.loads(r.read())
    if status["status"] == "COMPLETED":
        req3 = urllib.request.Request(response_url, headers={"Authorization": f"Key {fal_key}"})
        with urllib.request.urlopen(req3, timeout=15) as r:
            result = json.loads(r.read())
        img_url = result["images"][0]["url"]
        break
```

Use `queue.fal.run` for submission — NOT `fal.run` directly.
Always use `status_url` and `response_url` from the job response — do not construct them manually.

---

## Assets Directory

Store style reference images for reuse:

    ~/.hermes/skills/creative/linux-ricing/assets/

Store reference images used for style transfer here. Check `assets/references/` for any
images already captured for the current theme.

---

## Known Pitfalls

- **`hermes chat -Q -q` with foreground timeout will time out on image generation.**
  Always use `terminal(background=True, notify_on_complete=True)` for image_gen calls.

- **Multi-monitor HiDPI setups produce oversized combined screenshots.**
  On a dual-monitor HiDPI system (3200x1800 @ 2x + 1920x1080), `spectacle --fullscreen`
  captures a combined image (e.g. 8192x3528). Calculate scale and crop using scaled coordinates:

  ```python
  from PIL import Image
  img = Image.open("screenshot.png")
  w, h = img.size
  scale = h / 1800          # logical height of primary monitor
  primary_w = int(3200 * scale)
  panel_y = int(1750 * scale)
  panel_h = int(80 * scale)  # 80px logical
  panel = img.crop((0, panel_y, primary_w, panel_y + panel_h))
  ```

  Do NOT hardcode pixel counts — they will be wrong on any setup that isn't single-monitor 1:1.

- **HuggingFace `pipeline_tag=image-to-image` does NOT list IP-Adapter or style-transfer
  models with reference image support.** The most capable style-transfer models (`h94/IP-Adapter`,
  `InstantX/FLUX.1-dev-IP-Adapter`) are tagged as `text-to-image` by HF.
  Search for `h94` or `InstantX` directly, or `search=IP-Adapter` to find the right models.

- **`fal-ai/image-editing/style-transfer` is NOT suitable for UI.** It does a full-image
  repaint with no structure preservation and no reference image input. Avoid for panel work.

- **Vision tool may be broken if gemini-2.5-turbo is configured as auxiliary model.**
  This model ID is invalid — all `vision_analyze` and `browser_vision` calls fail with 400.
  Fallback: pixel sampling via ffmpeg rawvideo + python3 struct for dominant color extraction.

- **browser vision returns blank images for local files.**
  Always use `vision_analyze` with a local file path directly, or delegate to a subagent
  with the `vision` toolset.
