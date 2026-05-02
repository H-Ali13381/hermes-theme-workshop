# Konsole Theming

## Canonical Rules

Konsole theming has three artifacts:

- Colorscheme: `~/.local/share/konsole/hermes-<theme-slug>.colorscheme`
- Profile:     `~/.local/share/konsole/hermes-<theme-slug>.profile` (fresh per run)
- Default profile pointer: `~/.config/konsolerc` → `[Desktop Entry] DefaultProfile`

The workflow creates a dedicated `hermes-<theme-slug>.profile` and switches
`konsolerc` `DefaultProfile` to it on every apply. The user's pre-existing
profile is never modified — it stays as a natural backup that undo restores by
flipping `DefaultProfile` back via the konsolerc backup.

After a run, verify the swap took effect:

```bash
kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile
# expected: hermes-<theme-slug>.profile
```

Already-running Konsole windows keep the previous profile in memory; open a new
tab/session to pick up the swap.

## Colorscheme Format

Konsole `.colorscheme` files use decimal RGB (`r,g,b`), same as KDE `.colors`
files. Always convert palette hex with `hex_to_rgb()`.

```ini
[General]
Description=hermes-mossgrown-throne
Wallpaper=

[Background]
Color=15,21,20

[Foreground]
Color=209,219,200
```

Do **not** put `Opacity` in the `.colorscheme`; Konsole ignores it there.

## Profile Format

The profile chooses the colorscheme and terminal runtime options:

```ini
[Appearance]
ColorScheme=hermes-<theme-slug>
Opacity=0.75
BlurBackground=false
BackgroundContrast=false

[General]
Name=hermes-<theme-slug>
Parent=FALLBACK/
```

`Opacity` belongs in `[Appearance]` of the `.profile`, not the `.colorscheme`.

## Plasma 6 Wayland Transparency Bug

As of 2026-05-01, native Wayland Konsole on Plasma 6.6.4 can silently ignore the
profile `Opacity` key even when the profile is correct and KWin compositing is
active. This is a platform bug, not a config error.

Preferred workaround: use Kitty when transparent terminal background is a design
requirement. See `references/konsole-wayland-transparency.md`.

## 10-Key → 16 ANSI Color Mapping

Konsole uses the same 10-key → 16 ANSI mapping defined in
`shared/design-system.md`. If `primary == warning`, avoid using `primary` as ANSI
blue (`Color4`); use `secondary` so blue and yellow remain distinguishable.

## Pitfalls

- Running Konsole sessions usually need a new profile/session to pick up theme
  changes.
- A written profile is not enough; `konsolerc` must point at it. The workflow
  always sets `DefaultProfile` on apply — verify with `kreadconfig6` if the
  visible Konsole still shows old colors.
- Never modify the user's pre-existing default profile. The workflow creates a
  separate `hermes-<theme-slug>.profile`; undo restores `DefaultProfile` to the
  original via the konsolerc backup.
- Do not debug transparency indefinitely on native Plasma Wayland; detect the
  platform bug and fall back to Kitty.
