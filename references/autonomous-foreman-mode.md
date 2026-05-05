# Autonomous Foreman Mode for Linux Ricing

Use this reference when the user explicitly delegates the whole `/linux-ricing` run to the agent, including approving aesthetic gates from known preferences and fixing workflow breakages while continuing.

## Trigger

User phrases like:
- "do the entire thing autonomously"
- "manage it yourself end-to-end"
- "edit the skill as you find issues or the process breaks, then continue"

## Operating Contract

Autonomy means the agent owns execution, monitoring, debugging, and routine gate answers. It does not mean blind mutation of workflow state.

Allowed without re-asking when delegation is explicit:
1. Start/resume via the bridge script.
2. Use known user aesthetic preferences to answer Step 2/2.5/4 gates.
3. Reject previews that conflict with user profile/aesthetic memory.
4. Wipe stale rice sessions after a dry-run shows only rice-session artifacts and the user has explicitly asked for a clean autonomous run.
5. Patch the linux-ricing skill/code/tests when a verified workflow bug appears.
6. Continue the workflow after fixing the bug and verifying the fix.
7. Apply post-workflow manual gaps documented by the skill, such as wallpaper, when they are necessary to satisfy the approved theme.
8. Iterate change → live check/confirmation → next change; do not batch a pile of manual fixes without verifying each material requirement before proceeding.
9. Hide/autohide stock KDE panels when the approved plan says an EWW/Quickshell/widget toolbar replaces the default panel feel, then verify the widget toolbar is running.

Still forbidden:
- Hand-editing `design.json`, LangGraph checkpoints, or session state to force progress.
- Claiming the final state without `resume-check`, file/config verification, relevant regression tests, and live preview-plan-implementation checks.
- Ignoring visual mismatch/stale preview artifacts; restart or use workflow-owned regenerate/backtrack.
- Treating element scores as sufficient when the live desktop still shows default wallpaper, visible stock panel chrome, or only icon/palette changes.
- Running destructive commands outside declared rice artifacts without explicit user approval.

## Successful Pattern from Ashen Sanctuary Ledger

1. Preflight: `resume-check`, FAL/key/client checks, existing bridge inspection.
2. Reject stale/mismatched preview state rather than approving it.
3. Wipe sessions with `session_manager.py wipe-sessions --yes` only after a dry-run confirms scope and delegation is explicit.
4. Drive creative answers using the user's stable taste: Diablo II / Classic WoW / Dark Souls, in-world ambience, thin thorn borders, worn metal/parchment/ash, no pixel art, no bulky frames, no KDE-default recolor.
5. On a materializer failure, inspect code with Auggie, add/adjust tests first, patch implementation, run targeted tests, then retry the workflow gate.
6. After completion, verify live KDE state with `kreadconfig6`, file existence checks, test suite slice, and `session_manager.py resume-check`.
7. Update `handoff.md`/`handoff.html` only for truthful post-workflow manual actions (example: wallpaper applied after completion).

## Regression Signals

Patch skill/code immediately when observing:
- Fresh FAL image with stale `visualize.html` title/palette/copy from a prior direction.
- `plasma_theme` applies successfully but verification reports every `~/.local/share/plasma/desktoptheme/<Theme>/...` file missing.
- Generated KDE desktop theme lacks `metadata.json` even though handoff/verification expects it.
- Final handoff says default wallpaper remains after manual wallpaper was applied.

## Verification Checklist

Minimum end-state checks before saying done:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
python3 ~/.hermes/skills/creative/linux-ricing/scripts/session_manager.py resume-check
python -m pytest tests/test_kde_materializers.py::TestMaterializePlasmaTheme -q
kreadconfig6 --file plasmarc --group Theme --key name
kreadconfig6 --file kdeglobals --group General --key ColorScheme
kreadconfig6 --file kdeglobals --group Icons --key Theme
kreadconfig6 --file kdeglobals --group KDE --key widgetStyle
```

Expected `resume-check`: `[]`.
