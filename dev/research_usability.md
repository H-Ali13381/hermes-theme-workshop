# Usability Philosophy for Linux Desktop Design

A research synthesis for the Linux desktop ricing agent. The goal is not to produce a checklist of rules, but a vocabulary of principles the agent can deploy deliberately — applying them when they serve the user, breaking them when the break is itself the point.

## 1. Core HCI Frameworks: What They Actually Say About Desktops

**Fitts's Law** models target acquisition time as a function of distance and target size: `MT = a + b·log₂(D/W + 1)`. The practical consequence is that screen edges and corners are effectively infinite in size — the mouse cannot overshoot them. This is why the macOS menu bar lives at the top edge and the Windows taskbar at the bottom. For desktop design this argues for: putting the most frequent targets on edges, making hot corners a first-class mechanism, and sizing click targets proportional to frequency of use. But Fitts's Law also reveals the tiling WM's secret: **keyboard actions have zero acquisition distance**. A keybind is a Fitts-distance of zero regardless of screen size. This is why power users migrate to keyboard-driven workflows — not because mice are bad, but because keybinds collapse the Fitts term entirely.

**Hick's Law** states that decision time grows logarithmically with the number of choices: `RT = a + b·log₂(n + 1)`. A 20-item application menu is not 20× slower than a 1-item menu; it is roughly 4× slower. This has two implications. First, flat menus with many items are often faster than deeply nested ones, which contradicts the intuition to "organize." Second, Hick's Law only applies to *undifferentiated* choices — familiar, spatially-stable layouts become pattern-matching, not decision-making. A rofi launcher with 200 applications is not a 200-way Hick's decision; it is a text-prefix filter that collapses the decision space to 2–3 matches per keystroke.

**Miller's Law** (7±2) is the most *mis*cited rule in HCI. Miller's 1956 paper was about short-term memory capacity for discrete items, not UI design. The actual working-memory figure is closer to 4±1 (Cowan, 2001). For desktops this matters in two places: workspaces and window counts per workspace. A user can track ~4 spatial "rooms" before they start losing the map. Tiling WMs that expose 10 numbered workspaces are betting that users will populate 3–5 meaningfully and let the rest idle — which, empirically, is what happens.

**Jakob's Law** — "users spend most of their time on other sites" — is the conservative rule. Familiarity is a feature. This is the single strongest argument against radical desktop redesign: a user coming from Windows expects close-buttons on the right, alt-tab to switch windows, and a start-menu-like launcher. GNOME's decision to put close-buttons on the right and hide minimize/maximize reflects Jakob's Law as filtered through opinionated simplification; KDE's decision to mirror Windows reflects Jakob's Law taken literally. A ricing agent should know which conventions the user expects from their prior desktop and break them only deliberately.

## 2. Don Norman's Principles Applied to Desktop Environments

Norman's *The Design of Everyday Things* gives us six lenses:

- **Affordances** are what an object permits. A button affords pressing; a scrollbar affords dragging. On desktops, the erosion of affordance signaling (flat design, hidden scrollbars, invisible window borders in tiling WMs) trades discoverability for aesthetic cleanliness. This is a real cost, not just a style choice.
- **Signifiers** are the perceivable cues that advertise affordances. A raised button *signifies* pressability. A keybind-only action has zero signifiers — it is invisible to anyone who does not already know it. Tiling WMs are almost entirely signifier-free surfaces, which is why their learning curves are vertical.
- **Mappings** are the correspondence between controls and effects. Workspace-switching keybinds that map `Mod+1` through `Mod+9` to workspaces 1–9 are a good mapping (spatial, numeric, direct). `Mod+Shift+1` to *move a window to* workspace 1 is also good — the shift modifier maps to "with this window." The mapping is self-documenting once the pattern is visible.
- **Feedback** is the system telling the user what just happened. A window that visibly slides to a new workspace has feedback; one that teleports silently does not. Tiling WMs historically under-feedback because motion was expensive; on modern hardware, adding subtle animation is a usability win even for power users, as long as it doesn't block input.
- **Conceptual models** are the user's mental model of how the system works. The floating-window model ("windows are papers on a desk") is deeply entrenched; the tiling model ("windows are tenants in a container tree") requires explicit teaching. A rice that mixes both models without committing to one creates a broken conceptual model and constant low-level friction.
- **Constraints** are what the system prevents you from doing. Constraints reduce error. A tiling WM that refuses to let windows overlap is using constraint as a feature — it eliminates the entire class of "window lost behind other windows" errors.

## 3. The Usability vs Learnability Tension

There is a fundamental tradeoff: systems optimized for experts have high performance ceilings and high learning costs; systems optimized for beginners have low ceilings and low costs. You cannot maximize both. The three major Linux desktop schools resolve this differently:

- **Tiling WMs (i3, sway, Hyprland, bspwm, dwm)** optimize aggressively for experts. Everything is keyboard-driven, configuration is code, and the UI provides minimal signifiers. The bet is that a user who invests a week of learning gets years of payoff. The cost is that a new user is helpless — they cannot even discover how to open a terminal without reading the config.
- **GNOME** optimizes for a specific conceptual model: focused single-task work, activities overview as the primary navigation hub, opinionated removal of customization. GNOME's philosophy is that fewer decisions = less cognitive load, which is *Hick's Law applied to configuration itself*. The cost is that users whose workflow doesn't match GNOME's model find it actively hostile. GNOME is learnable *and* usable — if your work looks like what GNOME expects.
- **KDE Plasma** tries to serve both ends by making everything configurable. This is the "bag of tools" approach: provide Windows-like defaults for Jakob's-Law reasons, expose every setting for experts. The cost is that the settings surface is itself a usability problem — users get lost in preference panes, and the default experience is a compromise that fully satisfies no one.

A ricing agent should recognize that *picking a point on this tradeoff is itself a design act*. The user's actual work patterns — not their stated preferences — should drive the choice.

## 4. Cognitive Load Theory on the Desktop

Sweller's cognitive load theory distinguishes three types:

- **Intrinsic load** is the inherent difficulty of the task. Writing code, reading a paper, editing video — these have irreducible cognitive cost.
- **Extraneous load** is cost imposed by the interface that doesn't contribute to the task. Hunting for a window that got hidden, reading the same notification twice, context-switching because a modal stole focus.
- **Germane load** is cost that builds useful mental structure — learning a keybind that will pay off thousands of times, building spatial memory of where workspaces live.

The goal is to minimize extraneous load, preserve intrinsic load (it *is* the work), and invest in germane load when the payoff horizon is long.

Concrete sources of extraneous load on desktops: notification popups that interrupt flow, animations that delay response, tooltips that appear on hover over everything, window-manager behaviors that are non-deterministic (is this window going to go there or not?), multiple ways to do the same thing with no clear "blessed" path, status bars packed with indicators that are 95% irrelevant 95% of the time.

Things that reduce extraneous load: deterministic window placement (tiling's hidden virtue), predictable keybinds across applications, quiet-by-default status bars that surface information only when it changes, modal systems where the user's current mode is always visible.

## 5. Nielsen's Heuristics in the Desktop Context

Two of Nielsen's ten are especially load-bearing for desktops:

**Visibility of system status.** The user should always know what mode they're in, what's happening, and what the system is about to do. On desktops this maps to: the current workspace being visible, the focused window being unambiguous, pending operations (updates, syncs, builds) being surfaceable without being intrusive. The anti-pattern is the silent system — a desktop that does things (moves windows, switches focus, starts background tasks) without telling the user is a desktop that breeds distrust.

**User control and freedom.** The user should be able to undo, to exit modes, to back out of mistakes. Desktops historically fail at this — there's no Ctrl+Z for "I just closed the wrong window," no "previous workspace layout" history. A rice that adds even crude undo (an "oh no" keybind that restores the last window state) is doing real usability work. Conversely, modal systems (vim-style modes in window managers) violate this unless the mode is visible and the escape is consistent.

## 6. Deliberate Usability Violations as Design

Not all usability violations are mistakes. Three traditions violate usability rules on purpose:

**Soulslike games** refuse to hold the player's hand. Dark Souls does not have a tutorial in the normal sense; it has an environment that *teaches through consequence*. The violation is deliberate because the *feeling of competence earned* is the product. If Dark Souls were usable in the Nielsen sense, it would not be Dark Souls.

**Brutalist web design** rejects polish, gradients, and friendly empty states in favor of raw structure, default browser fonts, and exposed mechanics. The violation is a statement: *I am not trying to seduce you. I am showing you the thing.* This is useful for desktops because it anchors an aesthetic tradition where "looks unfinished" is intentional, not a failure state.

**Tiling WMs** violate Jakob's Law (they are nothing like Windows or macOS), affordance and signifier principles (nothing tells you what to do), and learnability norms (the first hour is unusable). They are justified by the same logic as vim: the investment amortizes. Ten minutes per day saved, over five years, is 300 hours.

The distinction that matters: **"hard to use" vs "requires investment."** A system is hard-to-use when its difficulty is arbitrary, non-compounding, and does not increase user capability. A system requires investment when the difficulty is structured, the learning compounds, and each unit of effort makes the user more capable. A rice can demand investment — it cannot be arbitrarily hard and call that a feature.

The test: *does effort invested in this system transfer elsewhere, or build capability that persists?* Vim keybinds transfer. A custom launcher shortcut that only works in one DE does not. Spatial workspace memory transfers between tiling WMs. An idiosyncratic status bar layout does not.

## 7. Flow State and the Desktop

Csikszentmihalyi's flow theory describes the state of absorbed concentration where time distorts and self-consciousness fades. Flow requires: clear goals, immediate feedback, a challenge calibrated to skill (not too easy, not too hard), and — crucially — minimal interruption.

For desktops, flow imposes specific requirements:

- **Input latency must be imperceptible.** Flow shatters when the system feels sluggish. Every animation that delays a keystroke response, every window manager hiccup, every notification that takes focus, is a micro-break in flow.
- **The interface must disappear.** During flow, the user is not interacting with the desktop — they are interacting with the work *through* the desktop. Any UI element that demands attention is stealing it from the work. This is the real argument for minimalism: not aesthetics, but attention economics.
- **Interruptions must be the user's choice.** Push notifications, auto-popping dialogs, and modal prompts are flow-killers. Pull-based surfaces (a status bar glance, a notification drawer) preserve flow because the user decides when to look.
- **State must persist across context switches.** When the user returns from a distraction, the desktop should be exactly where they left it. A desktop that loses window layout on sleep/wake is actively hostile to flow.

The strongest flow-supportive desktop pattern is probably: tiling layout (deterministic spatial memory) + quiet status bar (glanceable, non-interrupting) + keyboard-driven navigation (Fitts-distance zero) + aggressive notification silencing (user-pull, not system-push) + no background animation (nothing moves unless the user moved it).

## Synthesis: Principles as Design Vocabulary

These frameworks are not a checklist. They are a vocabulary that lets the agent *name what it's doing*. A rice that puts a launcher on a hot corner is deploying Fitts's Law. A rice that hides all signifiers is making a soulslike bet — the aesthetic payoff must justify the learnability cost. A rice that copies macOS conventions is using Jakob's Law; a rice that inverts them is declaring that the user's prior habits are wrong.

The best design stance the agent can take is *conscious*: know the rule, know the cost of breaking it, know what the break buys. The worst stance is *accidental* — breaking rules without knowing they exist, and then being surprised when the system feels bad for reasons no one can name.
