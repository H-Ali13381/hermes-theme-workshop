# Cost Control and Rollback Lessons

## Paid image generation discipline

The user explicitly called out that repeated FAL/image generations cost money. Treat image generation as a paid, scarce resource.

Default protocol:
1. Generate at most one Step 2.5 hero image for the main concept unless the user explicitly approves another generation.
2. Never regenerate for small caveats such as wallpaper swappability, terminal frame size, toolbar/menu tweaks, or implementation notes. Approve/lock the existing image, then carry the caveat into Step 4 plan feedback or implementation.
3. Before any extra generation, inspect existing session files first: `visualize.html`, `visualize.pending.json`, `plan.html`, `design.json`, and workflow logs.
4. Prefer non-generative fixes: workflow feedback, plan refinement, materializer/config fixes, local wallpaper reuse, or existing generated URLs.
5. If state is stale/mixed, report the mismatch and use workflow-safe restart/backtracking only after considering whether an existing artifact can be reused. Do not generate just to escape confusion.
6. Ask before spending again unless the user has explicitly said `regenerate`, `new image`, or `start fresh and generate again`.

## Rollback cleanup gap from Ashen Sanctuary Ledger

Observed rollback result: `scripts/ricer.py undo-session` successfully restored 13 manifests and 35 items, but some manually created/post-workflow artifacts were outside the manifest and needed explicit cleanup.

After undo-session, verify and remove Ashen/new-theme leftovers:

```bash
test -e ~/.local/share/wallpapers/hermes/ashen-sanctuary-ledger.png && echo manual_wallpaper_exists || echo manual_wallpaper_absent
test -d ~/.local/share/plasma/desktoptheme/Ashen-Sanctuary-Ledger && echo ashen_desktoptheme_exists || echo ashen_desktoptheme_absent
test -f ~/.config/eww/eww.yuck && echo eww_yuck_exists || echo eww_yuck_absent
test -f ~/.config/eww/eww.scss && echo eww_scss_exists || echo eww_scss_absent
```

If those files were generated for the session and have no manifest backup, close EWW and remove them:

```bash
eww close-all 2>/dev/null || true
rm -f ~/.local/share/wallpapers/hermes/ashen-sanctuary-ledger.png
rmdir ~/.local/share/wallpapers/hermes 2>/dev/null || true
rm -rf ~/.local/share/plasma/desktoptheme/Ashen-Sanctuary-Ledger
rm -f ~/.config/eww/eww.yuck ~/.config/eww/eww.scss
```

Then set the previous/default wallpaper if the manual wallpaper had been applied:

```bash
plasma-apply-wallpaperimage /usr/share/wallpapers/Next/contents/images_dark/5120x2880.png
```

Verification used in-session:

```bash
kreadconfig6 --file plasmarc --group Theme --key name
kreadconfig6 --file kdeglobals --group General --key ColorScheme
kreadconfig6 --file kdeglobals --group Icons --key Theme
kreadconfig6 --file kdeglobals --group KDE --key widgetStyle
kreadconfig6 --file kcminputrc --group Mouse --key cursorTheme
kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage
pgrep -a plasmashell
pgrep -a eww || true
```

Important: a plain `undo-session` may restore to the previous rice (e.g. `hermes-bonfire-hollow`), not stock KDE. Always report the actual restored target from verification instead of saying "back to default".

## Manual rollback cleanup gap from Emberward Reliquary

Observed rollback result: `scripts/ricer.py undo-session` can restore all manifest-owned files with zero failures and still leave the live desktop visually broken when post-workflow/manual artifacts were created outside manifests. In the Emberward Reliquary rollback, the workflow restore succeeded, but EWW was still running, `~/.config/eww` still contained the custom toolbar, Plasma desktop applet config still pointed at the generated wallpaper, and the custom Plasma desktoptheme directory still existed.

Use a conservative verify-and-stash pattern rather than blind deletion:

```bash
# From the skill venv/workdir
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python3 scripts/ricer.py simulate-undo-session
python3 scripts/ricer.py undo-session

# Verify live KDE state and remaining generated processes/files
kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage
kreadconfig6 --file kdeglobals --group General --key ColorScheme
kreadconfig6 --file kdeglobals --group Icons --key Theme
kreadconfig6 --file plasmarc --group Theme --key name
pgrep -a plasmashell
pgrep -a eww || true
pgrep -a quickshell || true
find ~/.config ~/.local/share/plasma ~/.local/share/wallpapers ~/Pictures \
  \( -iname '*emberward*' -o -iname '*reliquary*' -o -iname '*hermes*' \) 2>/dev/null
```

If live applet/wallpaper state still points at generated files, restore the relevant baseline copy of `plasma-org.kde.plasma.desktop-appletsrc` from `~/.cache/linux-ricing/baselines/<timestamp>_files/` only after confirming it is the intended pre-rice baseline. Then reapply stock KDE targets and restart plasmashell:

```bash
cp ~/.cache/linux-ricing/baselines/<timestamp>_files/plasma-org.kde.plasma.desktop-appletsrc \
   ~/.config/plasma-org.kde.plasma.desktop-appletsrc
plasma-apply-colorscheme BreezeDark
plasma-apply-lookandfeel org.kde.breezedark.desktop
plasma-apply-desktoptheme default
kwriteconfig6 --file kdeglobals --group Icons --key Theme breeze-dark
kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle Breeze
kquitapp6 plasmashell && kstart plasmashell
```

For generated artifacts not owned by manifests, stop the process and move them into a timestamped stash under `~/.cache/linux-ricing/manual-rollback-stash/` rather than deleting immediately. This preserves forensics/recovery while removing them from the active desktop:

```bash
stamp=$(date +%Y%m%d_%H%M%S)
stash=~/.cache/linux-ricing/manual-rollback-stash/$stamp
mkdir -p "$stash"
eww close-all 2>/dev/null || true
pkill -x eww 2>/dev/null || true
[ -d ~/.config/eww ] && mv ~/.config/eww "$stash/eww"
[ -d ~/Pictures/EmberwardReliquary ] && mv ~/Pictures/EmberwardReliquary "$stash/EmberwardReliquary"
[ -d ~/.local/share/plasma/desktoptheme/EmberwardReliquary ] && \
  mv ~/.local/share/plasma/desktoptheme/EmberwardReliquary "$stash/EmberwardReliquary.desktoptheme"
```

Final verification should include both effective settings and absence of live session references:

```bash
kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage       # org.kde.breezedark.desktop
kreadconfig6 --file kdeglobals --group General --key ColorScheme         # BreezeDark
kreadconfig6 --file kdeglobals --group Icons --key Theme                 # breeze-dark
kreadconfig6 --file kdeglobals --group KDE --key widgetStyle             # Breeze
kreadconfig6 --file plasmarc --group Theme --key name                    # default
pgrep -a eww || true                                                     # absent
pgrep -a quickshell || true                                              # absent
pgrep -a plasmashell                                                     # running
grep -RniE 'emberward|reliquary|ashen|bonfire' ~/.config 2>/dev/null | grep -v brave || true
```

Tell the user exactly what was restored and what was merely stashed. Do not claim every app window is visually refreshed; tell them to close/reopen already-running KDE apps/Dolphin/Kitty if icon/theme inheritance looks stale.

## Failed Bonfire Blackiron rollback gaps

Observed rollback result: `scripts/ricer.py undo-session` restored manifest-owned files with zero failures, but the live desktop still had post-workflow manual artifacts: Quickshell was still running from `~/.config/quickshell/shell.qml`, the active wallpaper still pointed at `~/.local/share/wallpapers/bonfire-blackiron/wallpaper.png`, and generated theme directories were outside the manifest path set.

When the user says "roll back all changes" after a KDE/Quickshell rice, treat it as active-session rollback plus manual residue cleanup. Use the workflow undo first, then verify and stash generated runtime artifacts:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python3 scripts/ricer.py simulate-undo-session
python3 scripts/ricer.py undo-session

# Verify live residue after manifest rollback.
kreadconfig6 --file kdeglobals --group General --key ColorScheme
kreadconfig6 --file kdeglobals --group Icons --key Theme
kreadconfig6 --file kdeglobals --group KDE --key widgetStyle
kreadconfig6 --file plasmarc --group Theme --key name
pgrep -ax quickshell || true
python3 - <<'PY'
from pathlib import Path
p=Path.home()/'.config/plasma-org.kde.plasma.desktop-appletsrc'
for line in p.read_text(errors='replace').splitlines():
    if line.startswith('Image='):
        print(line.split('=',1)[1]); break
PY
```

If residue remains, restore the baseline captured before the rice from
`~/.cache/linux-ricing/baselines/<timestamp>_files/` after checking the session's
`baseline_*.json`, stop Quickshell, and move generated artifacts to a timestamped stash
instead of deleting blindly:

```bash
stamp=$(date +%Y%m%d-%H%M%S)
stash=~/.cache/linux-ricing/manual-rollback-$stamp
base=~/.cache/linux-ricing/baselines/<timestamp>_files
mkdir -p "$stash"
pkill -x quickshell 2>/dev/null || true
[ -f ~/.config/quickshell/shell.qml ] && mkdir -p "$stash/quickshell" && mv ~/.config/quickshell/shell.qml "$stash/quickshell/shell.qml"
cp "$base/plasma-org.kde.plasma.desktop-appletsrc" ~/.config/plasma-org.kde.plasma.desktop-appletsrc
cp "$base/kdeglobals" ~/.config/kdeglobals
cp "$base/plasmarc" ~/.config/plasmarc
cp "$base/kvantum.kvconfig" ~/.config/Kvantum/kvantum.kvconfig
for path in \
  ~/.local/share/wallpapers/bonfire-blackiron \
  ~/.local/share/plasma/desktoptheme/BonfireBlackiron \
  ~/.local/share/plasma/look-and-feel/BonfireBlackiron \
  ~/.local/share/icons/bonfire-blackiron \
  ~/.local/share/icons/bonfire-blackiron-icons \
  ~/.config/Kvantum/BonfireBlackiron; do
  [ -e "$path" ] && mv "$path" "$stash/$(basename "$path")"
done
plasma-apply-colorscheme BreezeDark
plasma-apply-lookandfeel --apply org.kde.breezedark.desktop
plasma-apply-wallpaperimage /usr/share/wallpapers/Next/contents/images_dark/5120x2880.png
kwriteconfig6 --file kdeglobals --group Icons --key Theme breeze-dark
kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle Breeze
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'for (var i=0;i<panels().length;++i){panels()[i].hiding="none"}'
kquitapp6 plasmashell && kstart plasmashell
```

Final verification for this failure class:

```bash
kreadconfig6 --file kdeglobals --group General --key ColorScheme       # BreezeDark
kreadconfig6 --file kdeglobals --group Icons --key Theme               # breeze-dark
kreadconfig6 --file kdeglobals --group KDE --key widgetStyle           # Breeze
kreadconfig6 --file plasmarc --group Theme --key name                  # default
pgrep -ax quickshell || true                                           # absent
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'for (var i=0;i<panels().length;++i){var p=panels()[i]; print(p.id+":"+p.hiding)}'
```

Capture and visually inspect a screenshot before claiming rollback. The expected visual result is stock KDE panel visible, default/dark KDE wallpaper, no Quickshell left rail or bottom bar, and no parchment/blackiron widgets.

## Full history rollback to stock KDE/Breeze baseline

When the user asks to roll back past earlier rice sessions to the pre-automation/default KDE state, use the workflow's all-history undo path instead of stopping after the active session:

```bash
source ~/.hermes/skills/creative/linux-ricing/.venv/bin/activate
cd ~/.hermes/skills/creative/linux-ricing
python3 scripts/ricer.py simulate-undo-session --all
python3 scripts/ricer.py undo-session --all -y
```

Observed successful pattern: all-history undo can report many manifests skipped as already undone and a smaller set executed; success criteria are `status: success` and `total failed: 0`, not that every manifest executes.

After `--all`, explicitly verify stock/default KDE targets and clean any post-manifest residue:

```bash
kreadconfig6 --file kdeglobals --group Icons --key Theme          # expected: breeze-dark
kreadconfig6 --file kdeglobals --group General --key ColorScheme  # expected: BreezeDark
kreadconfig6 --file plasmarc --group Theme --key name             # expected: default
kreadconfig6 --file kdeglobals --group KDE --key widgetStyle      # expected: Breeze
kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage # expected: org.kde.breezedark.desktop
kreadconfig6 --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key Image
find ~/.local/share/plasma -iname '*hermes*' -o -iname '*ashen*' -o -iname '*bonfire*'
find ~/.local/share/color-schemes -iname 'hermes-*'
```

If residue remains outside manifests, remove only verified generated artifacts and set explicit defaults:

```bash
rm -f ~/.local/share/color-schemes/hermes-*.colors
plasma-apply-wallpaperimage /usr/share/wallpapers/Next/contents/images_dark/5120x2880.png
plasma-apply-colorscheme BreezeDark
plasma-apply-lookandfeel org.kde.breezedark.desktop
plasma-apply-desktoptheme default
kwriteconfig6 --file kdeglobals --group Icons --key Theme breeze-dark
kwriteconfig6 --file kdeglobals --group KDE --key widgetStyle Breeze
kwriteconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage org.kde.breezedark.desktop
kquitapp6 plasmashell && kstart plasmashell
python3 scripts/ricer.py simulate-undo-session --all  # expected: would_undo_count 0
```

Keep the distinction clear in user reports: `undo-session` = current session rollback; `undo-session --all` = history-wide rollback toward stock defaults.