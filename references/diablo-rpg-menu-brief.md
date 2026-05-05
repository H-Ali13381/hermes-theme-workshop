# Diablo II / dark RPG menu brief pattern

Use this as a compact reference when a user asks for a Diablo II, Lord of Destruction, campfire-in-a-dark-land, or RPG inventory/menu-inspired KDE rice.

## Motifs captured from session

- Place: next to a campfire, in a dark land.
- Mood/reference: inside the Diablo II in-game menu; Lord of Destruction anchor.
- Avoid: generic KDE default color swaps; standard toolbars.
- Prefer: RPG-inspired widget menus, AI-generated/relic-like icons, carved borders for menu buttons, thorn motifs on borders, black terminal window, glyphs for buttons.
- Strong correction from user: the thorn motif is not just decorative trim — they specifically want ornate window borders like the thorned frames around Diablo II windows and buttons. Carry this into `chrome_strategy`, `window_decorations:kde`, custom EWW/overlay frames, launcher borders, and button states rather than only palette or wallpaper.

## Design translation

- Treat menus/widgets as diegetic game UI panels: inventory frames, quest-log plaques, campfire-lit sanctuary overlays.
- Use black or near-black terminal surfaces, not merely tinted dark themes.
- Use carved/etched button borders and thorn/vine/iron filigree as the repeated shape language. For Quickshell, this means real tiled/9-slice frame construction with QtQuick `BorderImage` assets for panels, buttons, and slots — not plain `Rectangle { border.color }` outlines with labels.
- Use glyph iconography for launcher/actions/buttons; avoid flat KDE-default symbolic recolors when the workflow supports generated icon assets.
- Keep the homage readable but not legally/logo-specific: evoke Diablo II through materials, layout, and atmosphere rather than copying logos or exact assets.
- New correction: do **not** make the whole desktop feel like it is trapped inside one giant menu. The world/wallpaper should feel like the game world; windows, widgets, launchers, and buttons should inherit the in-game menu/chrome language.
- Prefer Dark Souls / Soulsborne restraint when Diablo ornamentation becomes too loud: thin thorn/forged borders, smoky translucent panels, quiet ember-gold hover/focus states, and high readability over heavy carved frames.
- Avoid a bulky decorative square/cage around the terminal. The terminal should be a usable window with subtle menu-style chrome, not a centerpiece box that distracts from work.
- Widget menu replacing a standard toolbar is good; keep that idea, but with clear hierarchy, legible spacing, and practical UX.

## Workflow handling note

After the explore node proposes named directions, feed the user's motif refinements verbatim instead of collapsing them to a choice number if they provide concrete constraints. This gives the explore/finalize nodes usable anchors for `originality_strategy`, `chrome_strategy`, widgets, and icon direction.
