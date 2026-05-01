# Wallpaper Sourcing for Ricing Sessions

When the user wants a game/media-themed wallpaper that matches the session palette,
use this workflow to find, evaluate, and present candidates.

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

## Pitfalls

- Alpha Coders `big.php?i=<id>` returns an HTML page, NOT the image directly.
  Use `https://images.alphacoders.com/<id>/<id>.jpg` for direct download.
- Some wallpapers have game logos/watermarks — `vision_analyze` can detect these.
- Webp format is fine for thumbnails but save full res as JPG/PNG for KDE compatibility.
- The workflow's `plan_node` cannot embed local images into `plan.html` — the wallpaper
  will be applied during the `implement` phase, not shown in the preview HTML.
- If `identify` (ImageMagick) isn't installed, use `file` to verify image format/dimensions.
