# Wallpaper Sourcing for Ricing Sessions

This file is only for the separate case where the user explicitly wants an actual
wallpaper candidate. Do not use it as the default answer to "real image references".
For reference-grounded ricing, game/menu screenshots and artwork should inform the
chrome, borders, menus, widgets, icon language, materials, and atmosphere; they are not
wallpapers unless the user explicitly selects one as wallpaper.

When the user wants a game/media-themed wallpaper that matches the session palette,
or when they reject a generated/procedural wallpaper as ugly or off-theme, use this
workflow to find, evaluate, and present candidates. A complaint that the wallpaper is
bad is an explicit signal to switch to real wallpaper sourcing; do not improvise another
local procedural placeholder unless the user asks for generative/local art.

## Sources (in order of reliability)

1. **Alpha Coders** (`alphacoders.com`) — Largest free wallpaper archive.
   - URL pattern: `https://alphacoders.com/<game-slug>-wallpapers`
   - Thumbnails: `https://imagesN.alphacoders.com/<id>/thumbbig-<id>.webp`
   - Full res: `https://images.alphacoders.com/<id>/<id>.jpg` (drop the `thumbbig-` prefix)
   - No API key needed. Download with `curl -sL`.
   - Game slugs: `elden-ring`, `bloodborne`, `hollow-knight`, `nier-automata`, `dark-souls`

2. **Wallhaven** (`wallhaven.cc`) — High quality, good search filters.
   - Tag-based search: click game tags from search results
   - Color filter available (useful for palette matching)
   - Thumbnails: `https://th.wallhaven.cc/small/<prefix>/<id>.jpg`
   - Full res requires navigating to the detail page

3. **Reddit** — Good for fan art, but JS-heavy; often blocked by bot detection.
   - Use `old.reddit.com` when possible
   - Subreddits: `r/wallpapers`, `r/wallpaper`, `r/<game>`

## Evaluation Workflow

1. **Search** — Query 3-4 game slugs on Alpha Coders in parallel (use `delegate_task`)
2. **Download thumbnails** — `curl -sL` all candidates to `/tmp/wallpaper-candidates/`
3. **Vision analysis** — Use `vision_analyze` on each thumbnail with this prompt:
   ```
   Describe the color palette, mood, and whether this has a dark, mossy,
   sanctuary-like atmosphere with green/gold tones. Rate how well it matches
   a '<theme-name>' theme (1-10).
   ```
   (Adjust the theme description to match the session's stance/mood)
4. **Rank** — Sort by score, present top 3-4 to user with descriptions
5. **Download full res** — Once user picks, download the full-resolution version
6. **Save to session** — Copy to `~/.config/rice-sessions/<thread-id>/wallpaper.<ext>`

## Quality Gate

Before applying a wallpaper, verify it against the design brief instead of settling for
"dark + orange":

- The image should establish the world/ambience first, not look like a generated UI mockup
  or a quick procedural sketch.
- For this user's dark RPG taste, prefer real game/fantasy landscape wallpapers with
  ruined chapels, ash/soot, bonfire/campfire glow, dead branches, worn stone, or
  Soulsborne/Diablo ambience. Avoid bright fantasy posters, logos, anime splash art,
  pixel art, neon sci-fi, and obvious watermarks.
- Use `vision_analyze` or equivalent visual inspection on thumbnails before download.
  If the candidate would score below 8/10 for the theme, keep searching.
- Apply only after saving the full-resolution file locally, then verify KDE points at
  the local file and capture a screenshot.

## Pitfalls

- Do not respond to "the wallpaper is ugly" by generating a new procedural placeholder.
  Switch to image search and ranked candidates unless the user explicitly asks for
  generated/local art.
- Do not use the Step 2.5 full-desktop concept preview as wallpaper; it includes mock UI
  and is not a clean background.

- Some wallpapers have game logos/watermarks — `vision_analyze` can detect these.
- Webp format is fine for thumbnails but save full res as JPG/PNG for KDE compatibility.
- The workflow's `plan_node` cannot embed local images into `plan.html` — the wallpaper
  will be applied during the `implement` phase, not shown in the preview HTML.
- If `identify` (ImageMagick) isn't installed, use `file` to verify image format/dimensions.
