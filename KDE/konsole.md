# Konsole Theming

## Canonical Rules

Konsole theming has two separate files:

- Colorscheme: `~/.local/share/konsole/hermes-<theme>.colorscheme`
- Profile: `~/.local/share/konsole/<active-default-profile>.profile`
- Default profile pointer: `~/.config/konsolerc` → `[Desktop Entry] DefaultProfile`

**Always read `konsolerc` first.** Do not assume `linux-ricing.profile` or
`hermes-ricer.profile` is active.

```bash
kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile
```

Edit the profile named by that key. If no default profile exists, create
`linux-ricing.profile` and set `DefaultProfile` explicitly.

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
ColorScheme=hermes-mossgrown-throne
Opacity=0.75
BlurBackground=false
BackgroundContrast=false

[General]
Name=linux-ricing
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
- A written profile is not enough; `konsolerc` must point at it.
- The active profile may be a user-created name such as `Default.profile` or
  `linux-ricing.profile`; always read it.
- Do not debug transparency indefinitely on native Plasma Wayland; detect the
  platform bug and fall back to Kitty.
