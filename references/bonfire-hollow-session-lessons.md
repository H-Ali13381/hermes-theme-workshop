# Bonfire Hollow / Dark RPG KDE Rice — Session Lessons

Use this when a Linux rice direction starts from Diablo II / classic WoW RPG menus but the user rejects heavy menu-box treatment and wants a more FromSoft in-world desktop.

## Durable aesthetic lessons

- The user likes the emotional anchor: campfire in a dark land, Diablo II / Lord of Destruction, Classic WoW / Burning Crusade, and Dark Souls/FromSoft warmth.
- Do not interpret “RPG menu” as “the whole desktop is inside a giant menu.” The stronger target is: the desktop feels like the game world, while windows/widgets inherit the menu/chrome language.
- Ornamentation should be restrained and usable: thin thorn/forged borders, ember focus lines, smoky translucent wells, parchment-dark panels. Avoid bulky frames, big square cages around terminals, and ornaments that compete with content.
- Widget menus are desirable when they replace toolbars/panels, but they must preserve hierarchy, legibility, and clear hit targets. “More UX love” means less visual clutter, stronger grouping, and readable interaction states.
- Wallpaper can remain user-swappable/manual. If the user likes the UI/chrome but not the wallpaper, proceed with the chrome/menu direction and leave wallpaper as a documented deviation rather than forcing another full concept loop.
- Grunge matters: soot, ash, worn metal, aged parchment, smoke, ruin, and ember light. Avoid outputs that look too clean, glossy, or generic fantasy-card-like.

## Workflow handling lessons

- At the Step 2.5 visual approval gate, only exact approvals such as `approve`, `yes`, `ok`, `looks good`, or `good` route to refine. Free-form caveats regenerate. If the user approves with caveats (for example, “menus good, wallpaper manual”), send `approve` only, then carry the caveat into Step 4 plan feedback or handoff notes.
- If an explore revision changes direction but the visualize gate still shows an old image URL, ask for/issue `regenerate` before approval. This prevents stale concept images from anchoring the new design.
- If FAL returns an image URL but the multimodal LLM times out downloading it, a subsequent no-answer bridge call may continue/retry normally once the image is available. Report the literal error first; if the user says to wait, run the read-only/no-answer bridge status/continue call rather than patching state.
- Bridge gates can appear to move quickly after a score gate. If a later `retry` is refused with “session has no pending interrupt,” immediately read `session.md` and `handoff.md` before assuming failure; the workflow may have completed and recorded final scores.

## Implementation notes from this session

- `terminal:kitty` initially scored 2/10 due structured-output/spec issues, but a later `retry` produced an 8/10 verified config. Do not give up on the first low score for important visible elements.
- `widgets:eww` initially surfaced as 6/10 but the final session recorded 10/10. Verify final session artifacts before summarizing.
- Package install failures for `breeze` and `papirus-icon-theme` can remain logged even after the user manually installs them; verify with `pacman -Q` before telling the user they are missing.
