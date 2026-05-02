# Game UI Design Philosophy: A Research Synthesis for Desktop Ricing

Game interfaces are the most diverse and opinionated laboratory of UI design in software. Unlike productivity software, which converges on conventions to reduce friction, games invent interface languages because the interface is part of the experience. Every game answers a deep question: *what is my relationship with the player, and how much of the machine do I let them see?* Desktop environments are designed to disappear; game UIs are designed to speak. The opportunity for a ricing skill is to treat the desktop as a designed artifact with a stance, borrowing from games the idea that UI can be a voice, not just a wrapper.

## 1. Diegetic vs Non-Diegetic UI

The foundational axis in game UI theory is the diegesis spectrum. A *diegetic* element exists inside the fiction — the character can see it, touch it, interact with it. A *non-diegetic* element is layered on top, visible only to the player. There are also hybrid categories: *spatial* elements that exist in the world but aren't part of the fiction (floor markers, enemy outlines), and *meta* elements that exist outside the world but respond to it (blood on the screen edges when hurt).

Non-diegetic UI — the floating health bar, the minimap in the corner, the inventory grid overlay — is honest about being a tool. It admits "you are playing a game, and here is your dashboard." It optimizes for legibility over immersion. Almost every RTS, MMO, and productivity app leans this way.

Diegetic UI folds the interface into the world. The player reads the story and the stats in the same glance. When Isaac's spine glows blue in Dead Space, there is no "HUD moment" — he is a body, and his body tells you what you need to know. Diegetic UI says: *I trust you to understand this world without a dashboard.* It raises the cost of information (you have to look for it) but raises the reward (the information is part of the fiction).

The philosophical payload: non-diegetic UI treats the user as an operator of a machine. Diegetic UI treats the user as a participant in a world. A desktop is usually a machine — but it doesn't have to be.

## 2. Genre UI Philosophies

**RPG.** Stats are the medium. RPGs descend from pen-and-paper tabletop, and they preserve that heritage in menus: inventory grids, character sheets, quest logs, dialogue trees. The assumption is that the player *wants* to see the numbers — the fantasy is managerial as much as heroic. Classic WRPGs (Baldur's Gate, Pillars of Eternity) lean into dense spreadsheet aesthetics. JRPGs (Final Fantasy, Persona) treat menus as fashion, spending enormous design budget on menu typography and transition animations. Persona 5's menus are arguably its most iconic visual feature — UI as swagger.

**FPS.** Minimal, heads-up, peripheral. The fantasy demands your eyes stay in the world. Ammunition count, a reticle, a small health indicator — anything more competes with situational awareness. Modern military FPSes have pushed this further toward *absence*: no crosshair when hip-firing, regenerating health instead of a visible bar, ammo embedded in the weapon model. The UI says: *you are the body, not the commander.*

**RTS.** The inverse. You are god, and god needs a dashboard. StarCraft, Age of Empires, Command & Conquer cover 20–30% of the screen with command panels, minimaps, resource counters, build queues. The premise is information density as empowerment — the better your dashboard, the better your decisions. RTS UI is the closest relative of the power-user desktop (tiling WMs, status bars, system monitors).

**Horror.** UI as tension tool, or its absence. Resident Evil 2's inventory is slow, physical, and limited — opening it doesn't pause the world. Silent Hill hides information and distorts the map. The *absence* of UI in horror is a strategy: without a health bar, you don't know how close to death you are, and fear fills the gap. Amnesia removes combat UI entirely because combat isn't the point; your relationship with information becomes the fear.

**Soulslike (FROM Software).** Sparse, cryptic, earned. The Dark Souls / Elden Ring UI philosophy is almost monastic: tiny HP/stamina bars in the top-left, no quest markers, no objective tracker, no tutorial popups after the first hour. Item descriptions are the narrative. The world is the map. Information must be earned — by dying, by reading, by paying attention. The UI communicates: *we will not hold your hand, and in that refusal is respect.* This is perhaps the most philosophically loaded UI stance in games.

**Visual Novel.** UI as atmosphere. The text box *is* the game. VN designers obsess over text frame ornamentation, name-tag typography, log-review affordances, transition timing. Danganronpa's trial UI is a carnival of kinetic typography; 13 Sentinels uses UI as puzzle. The VN lesson: when the interface is where the experience lives, every pixel carries tone.

## 3. Landmark UI Systems

**Dead Space (2008)** — the canonical diegetic HUD. Isaac's health is his spine, glowing blue and depleting. Stasis is a gauge on his shoulder. Ammo is projected from the gun itself. The inventory is a hologram Isaac projects in front of him, and crucially the world does not pause — you are vulnerable while reading your UI. The result is a horror game that never breaks immersion, and a case study proving diegetic UI can be *functional*, not just aesthetic.

**Alien Isolation (2014)** — UI as lore. Every screen, button, terminal, and save point is styled as 1979 retro-futurism: CRT scanlines, monochrome amber, chunky typography, audio cassette save icons. The UI isn't just consistent with the Alien film aesthetic — it teaches you what the world *is* before the monster ever appears. A save station hums. A motion tracker chirps. The UI is the world, and the world is the UI.

**Hades (2020)** — warm mythic UI. Supergiant Games treats UI like a painted manuscript: hand-illustrated portraits, gold filigree frames, serif display type, warm parchment backgrounds. The boon selection screen is a religious experience — literally, since you're accepting gifts from gods. The UI carries the mythology; you don't just play a Greek myth, you read one.

**Disco Elysium (2019)** — literary, text-forward. The interface is a novel with stats. Skill checks appear as parenthetical asides; your skills *speak to you* in the dialogue log as named voices with their own typography. The Thought Cabinet is a UI element that is also a narrative device. Disco Elysium proves that text-dense UI, far from being obsolete, can be the richest possible interface when the text itself is the art.

**Hollow Knight (2017)** — minimal, art-forward. Tiny masks for health, a geo counter in a corner, no minimap for much of the game (you buy them from a cartographer). The UI recedes so the hand-drawn art can breathe. Even the pause menu is restrained. The lesson: when your art is good enough, UI should defer to it.

**NieR: Automata (2017)** — meta-UI breaks. The HUD is a pod companion's projection; it can be damaged, corrupted, hacked, removed. During certain story beats the game uninstalls its own UI, then its own save files. The UI is a character, and the willingness to weaponize it against the player is what makes Yoko Taro's games singular.

**Final Fantasy evolution.** FF1's blocky menus, FFVII's Materia grids, FFX's Sphere Grid as sprawling UI-as-game, FFXIII's Paradigm shifts, FFXVI's real-time minimalism. The series is a 35-year record of how JRPG UI tracks hardware, genre shifts, and the slow move from menu-driven to action-driven. Worth studying as a longitudinal case.

**World of Warcraft addon culture.** Blizzard shipped a default UI but exposed a Lua API, and the community built an ecosystem (WeakAuras, ElvUI, Bartender, Details) that lets players rebuild the entire interface. WoW is the proof-of-concept for *UI as a personal configuration project*. Hardcore raiders' screens look nothing like the default and nothing like each other. This is the closest game-world analogue to the Linux ricing ethos: a platform provides primitives; a community composes identities.

## 4. What UI Encodes About the Player

Every interface makes implicit claims about who is using it. Game UIs make these claims loudly:

- **Do we trust you with information?** A soulslike says *we trust you to find it.* An MMO tutorial says *we don't, and here are thirty tooltips.* Trust is expressed as *absence* of explanation.
- **Do we hide the machine?** Diegetic UIs hide it behind fiction. Non-diegetic UIs expose it as a dashboard. Both are valid; the choice is a statement about whether the experience is *being in a world* or *operating a system*.
- **Is the UI part of the narrative?** NieR and Alien Isolation say yes — the interface carries meaning beyond function. Most productivity software says no — the interface should be invisible.
- **Does mastery matter?** Games with deep UI (EVE Online, Dwarf Fortress, Paradox grand strategy) reward the player who climbs the learning cliff with capabilities unreachable via simpler interfaces. Complexity is a gift to the committed.
- **Is the UI stable, or does it evolve?** Some games teach you one UI and stick with it. Others grow with you — new panels, new readouts, new affordances unlocked by progress. The unfolding interface communicates growth.

## 5. Mapping to Desktop Environments

A desktop is a game that never ends and where the player is the author. The stances above translate directly:

**The Soulslike desktop.** Chrome hidden. No title bars, no docks, no visible panels. Keybindings over menus. Information surfaces only when invoked — a status bar that fades, a launcher that vanishes. The desktop trusts the user to know their system. Every affordance is earned by learning. This is roughly what minimal tiling-WM rices (dwm, a bare Hyprland) already gesture at, but the *philosophical frame* is what makes it coherent rather than just sparse.

**The diegetic desktop.** Status information integrated into the environment, not floating on top. The wallpaper reacts to CPU load. The window border color encodes battery. The cursor trail changes with network state. Information lives in the world of the desktop rather than in a chrome layer. This is the Dead Space stance: the machine tells you its state through its body.

**The Alien Isolation desktop.** A complete retro-aesthetic commitment — CRT shaders, amber monochrome, chunky bitmap fonts, terminal-first tooling, save-cassette chimes on file operations. Every element sings the same song. The aesthetic isn't decoration; it's a world-claim about what computing *is* to the user.

**The Hades desktop.** Warm, ornamented, hand-illustrated. Serif fonts for system text. Gold-leaf window borders. Notifications as illuminated manuscript cards. A desktop that says *computing can be mythic, not sterile.*

**The WoW-addon desktop.** The Linux ricing canon already. A base (compositor + WM) with an exposed configuration surface, and a community building interchangeable modules (Waybar, eww, Quickshell, Polybar). The stance here is *the desktop is a platform for self-authorship,* and the rice is the player character.

**The Disco Elysium desktop.** Text-forward, literary. Notifications with prose personality. Status bars that read like narration. A desktop where the typography is the art and the written word is the primary visual texture. Aerc, neomutt, and tiling terminal setups already live here, but a full environment could push further.

**The NieR desktop.** The desktop as a character that can be broken, corrupted, celebrated. Glitches used as art. Boot sequences that remember previous sessions. A UI willing to break its own rules for a moment of meaning.

**The exploration-reward desktop.** Functions hidden until discovered. A man-page-as-dungeon-map metaphor. First-run experience that reveals only the essentials, with deeper affordances unlocked by use. This inverts the productivity default of *show everything, explain everything.*

## Closing: the design stance

Game UI teaches desktop design one decisive lesson: **the interface is a voice, and a voice must have a stance.** Productivity software defaults to the neutral stance — invisible, conventional, uncontroversial — because neutrality scales. But a personal desktop is not productivity software; it is a space of self-authorship. The ricing tradition already knows this implicitly. What games offer is a vocabulary for making the stance explicit: diegetic or non-diegetic, sparse or dense, trusting or tutorial, literary or mechanical, mythic or clinical. A design-stance model for desktops should ask the user not *what theme do you want* but *what kind of world is your computer?* The answer — soulslike, Hades, Isolation, Automata — encodes a thousand smaller decisions in a single coherent frame.
