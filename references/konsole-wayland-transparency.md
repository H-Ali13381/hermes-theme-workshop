# Konsole Transparency on KDE Plasma 6 Wayland

## Status
**BROKEN** as of Plasma 6.6.4 on native Wayland. The `Opacity` key in `.profile`
is silently ignored. This is a known upstream regression in the blur-behind Wayland
protocol — not a config error.

## Diagnosis
```bash
# Confirm Konsole is native Wayland (not XWayland)
xlsclients 2>/dev/null | grep -i konsole || echo "Native Wayland — Opacity broken"

# Confirm compositor is running
qdbus6 org.kde.KWin /Compositor org.kde.kwin.Compositing.active
# Returns "true" even though Konsole opacity still doesn't work

# Confirm blur effect is loaded
qdbus6 org.kde.KWin /Effects org.kde.kwin.Effects.isEffectLoaded "blur"
```

## The Config That's Correct But Ignored
```ini
# ~/.local/share/konsole/<profile>.profile
[Appearance]
Opacity=0.75           # Correct key, correct section — just ignored on Wayland
BlurBackground=false   # Also ignored
BackgroundContrast=false
```

Note: `Opacity` in the `.colorscheme` file is ignored. Konsole reads opacity
from the active `.profile` file only. On affected Plasma Wayland builds, even
the correct profile setting has no visible effect.

## Canonical Profile Selection

Before editing Konsole, read the active default profile:

```bash
kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile
```

Edit `~/.local/share/konsole/<that-profile>`. If no value is set, create a
profile and set the key explicitly with `kwriteconfig6`. Editing a guessed
profile such as `hermes-ricer.profile` has no effect unless `konsolerc` points to it.

## Workarounds

### 1. Use Kitty Instead (Recommended)
Kitty's `background_opacity` works correctly on Wayland:
```
# ~/.config/kitty/kitty.conf
background_opacity 0.75
dynamic_background_opacity yes
```
Point users to Kitty for transparency when Konsole is native Wayland.

### 2. System Update / Retest
The bug may be fixed by a future Plasma release. If the user updates Plasma,
retest with a fresh Konsole session before declaring support:
```bash
sudo pacman -Syu
```

### 3. Force XWayland (Not Recommended)
Launch Konsole with `DISPLAY=:1 WAYLAND_DISPLAY= konsole`. Loses some Wayland
benefits (HiDPI, input handling). Messy to automate.

## Related Notes
- `konsoleprofile Opacity=0.75` command returns exit 0 but has no visible effect
  on Wayland native — same bug, different entry point
- `AllowKonsoleRemoteCommands=true` in konsolerc is required for D-Bus
  `setProfile` calls to work; without it, `AccessDenied` is returned
- The default profile used by Konsole is set in `~/.config/konsolerc`:
  ```ini
  [Desktop Entry]
  DefaultProfile=<active-profile>.profile
  ```
  Always check this file before editing any profile — editing the wrong profile
  has no effect
