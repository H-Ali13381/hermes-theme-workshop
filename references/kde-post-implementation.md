# Post-Implementation Verification & Manual Elements (KDE)

After the workflow completes Step 6, run these checks and apply any elements the
queue does not own. The Step 7 cleanup node handles most of this automatically;
this doc is the manual fallback when cleanup reports a skipped/unsupported action.

---

## Palette Audit (Agent Responsibility)

The workflow's scorecard validates structure and palette presence, but can miss cases where old config values remain (e.g. kitty appending `include theme.conf` while old colors stay inline). Verify each written config actually reflects the design palette:

```bash
# Quick palette audit — grep actual color values in each config
echo "=== kitty ===" && grep -E "^(foreground|background|color[0-9]|cursor )" ~/.config/kitty/kitty.conf 2>/dev/null
echo "=== starship ===" && head -6 ~/.config/starship.toml 2>/dev/null
echo "=== rofi ===" && cat ~/.config/rofi/hermes-theme.rasi 2>/dev/null | head -10
echo "=== fastfetch ===" && python3 -c "import json; d=json.load(open('$HOME/.config/fastfetch/config.jsonc')); print(d.get('color',{}))" 2>/dev/null
```

If any config still has colors from a previous theme (e.g. Shiva Temple's `#0a0b1a` or `#5b4fcf`), replace them inline. Don't rely on `include` files overriding old values — some terminals parse includes differently.

---

## Konsole Theming — Dedicated Themed Profile

The workflow creates a fresh `hermes-<theme-slug>.profile` per run and points `~/.config/konsolerc` `DefaultProfile` at it. The user's prior default profile is never overwritten. After the workflow runs, verify the swap took effect:

```bash
kreadconfig6 --file konsolerc --group "Desktop Entry" --key DefaultProfile
# expected: hermes-<theme-slug>.profile
```

If it shows anything else, the workflow's `kwriteconfig6` call failed — check that `kwriteconfig6` is on PATH and re-run.

When manually editing Konsole config (rare — prefer letting the workflow own it), edit the `hermes-<theme-slug>.profile` file. Do NOT edit the user's original profile; undo relies on it being unmodified.

The `Opacity` key belongs in `[Appearance]` of the `.profile` file — NOT in the `.colorscheme` file. The `.colorscheme` file's `Opacity` key is ignored by Konsole.

Correct profile structure (as written by the workflow):
```ini
[Appearance]
ColorScheme=hermes-<theme-slug>

[Cursor Options]
CustomCursorColor=<r>,<g>,<b>
CustomCursorTextColor=<r>,<g>,<b>
UseCustomCursorColor=true

[General]
Name=hermes-<theme-slug>
Parent=FALLBACK/
```

Konsole transparency on native Wayland is broken — see `konsole-wayland-transparency.md`. Recommend Kitty when transparency is part of the design.

---

## AUR Package Install via Agent Terminal

`yay -S` builds the package but fails the final `sudo pacman -U` step (no TTY for password). The built package is left in `~/.cache/yay/<pkg>/`. Install it directly:

```bash
sudo pacman -U ~/.cache/yay/<pkg>/<pkg>.pkg.tar.zst
```

This works from the agent terminal without PTY issues.

---

## Workflow Gaps: Elements Requiring Attention

The audit node builds an initial `element_queue` from detected apps. Step 3 may then add design-driven elements such as `widgets:eww` when the user vision calls for EWW widgets, terminal frames, custom borders, or overlay chrome. Do not add generic widgets just to satisfy a checklist; use them when they make the concept less boring and more true.

| Element | In queue? | Notes |
|---------|-----------|-------|
| wallpaper | No | Must be sourced separately (see `wallpaper-sourcing.md`). Applied during implement, not shown in plan.html. |
| widgets / EWW chrome (KDE) | Design-driven | `widgets:eww` is added after `design.json` only when `widget_layout` or `chrome_strategy` calls for custom overlays, frames, borders, or widgets. |
| notifications (dunst/mako/swaync) | No | May not be installed. Install + configure manually if needed. |
| panel/bar (KDE panel) | Design-driven | Use `panel_layout` when the concept changes panel composition. Prefer original overlay/dock/rail chrome over the normal KDE toolbar when it fits the user brief. |
| cursor theme | No | design.json defaults to "default". Override manually. Catppuccin cursor themes are pre-installed and palette-matched. Bibata requires AUR install + sudo. |
| Hermes skin | No | Only relevant if user has custom Hermes CLI. |

When the user asks about widgets, panels, rounded windows, or custom borders, treat them as visual promises. Collect preferences during explore/plan, preview them in `plan.html`, and ensure `chrome_strategy` maps the promise to an implementable target such as EWW frames, Kitty decoration settings, Kvantum, or KDE color/window decoration settings.

---

## KDE-Specific Notes

### Cursor theme
Bibata-Modern-Classic requires AUR install (`yay -S bibata-cursor-theme-bin`) plus `sudo pacman -U` to install the built package. If sudo is unavailable, Catppuccin cursor themes are pre-installed and palette-matched. Use the variant that best matches the theme's primary/accent color:

```bash
# Set cursor via kwriteconfig (no sudo needed)
kwriteconfig6 --file kcminputrc --group Mouse --key cursorTheme --type string "catppuccin-macchiato-green-cursors"
# Cursor change takes effect on next login (KDE requirement)
```

### Notifications
KDE Plasma has its own notification system (plasmashell). No external daemon (dunst/mako/swaync) is needed. The color scheme automatically applies to notifications.

### Originality / chrome composition
KDE Plasma color inheritance is not enough. The workflow requires `originality_strategy` and `chrome_strategy`; optional `panel_layout` and `widget_layout` are used only when they serve the user vision. If the preview shows rounded windows, custom terminal frames, ornamental borders, or non-stock panel chrome, the final output must implement them through EWW frames, terminal config, Kvantum, or KDE decoration/color settings. Do not call a palette-only panel "done."

### Wallpaper
Use `plasma-apply-wallpaperimage <path>` to set wallpaper on all desktops. This is NOT in the element_queue. The cleanup node handles it when the design exposes a wallpaper target as top-level `wallpaper_path` / `wallpaper`, nested `chrome_strategy.wallpaper_path` / `wallpaper`, a `chrome_strategy.implementation_targets` entry such as `wallpaper:local_artifact:/path/to/theme-wallpaper.png`, or a `visual_element_plan` item whose `desktop_element` is `wallpaper` and whose `config_targets` point at a wallpaper directory/file. If that local file is missing and the session has an approved `visualize_image_url`, cleanup downloads the approved overview to the target path before applying it. If cleanup reports `wallpaper-apply` skipped, then perform the manual `plasma-apply-wallpaperimage <path>` fallback and update this reference/test coverage for the new failure mode.

Observed failure mode: designs may express wallpaper only through `visual_element_plan` (`desktop_element: wallpaper`, `config_targets: ["~/.local/share/wallpapers/<slug>/"]`) and omit `wallpaper_path`. Cleanup must infer `<target-dir>/wallpaper.png` from that contract instead of leaving the KDE default wallpaper active.

### Quickshell runtime validation
KDE Wayland widget chrome should prefer Quickshell. Generated QML must be tested against the installed runtime, not only file existence. Current Quickshell runtimes may not provide an `IconImage` QML type; generated tray/launcher components should use `Text` glyphs or a supported QtQuick `Image` source unless the runtime proves `IconImage` exists. Verify with:

```bash
# There is no `quickshell reload` subcommand on the current runtime.
# After editing shell.qml, restart explicitly:
quickshell kill || true
quickshell --path ~/.config/quickshell/shell.qml --daemonize --no-color --log-times -v
quickshell list
quickshell log --no-color | tail -80
```

Promised shell chrome must use `PanelWindow`, not `FloatingWindow`. On KDE/Wayland a `FloatingWindow` can appear as a normal decorated app-style surface with a titlebar, causing preview/plan drift when the preview showed integrated toolbar/widget chrome. For bars, launcher strips, quest/notification cards, and corner inventory widgets, use `PanelWindow`. Current installed Quickshell does **not** expose the `WlrLayershell` attached object used in some upstream examples; adding `WlrLayershell.layer: WlrLayer.Overlay` fails with `Non-existent attached object`. Verify side/corner widgets by screenshot, and if `exclusionMode: Ignore` makes them invisible behind app/desktop layers, use `exclusionMode: ExclusionMode.Normal` or reshape the surface into a visible anchored panel. Static craft validation rejects generated QML that combines a Quickshell widget promise with `FloatingWindow`.

### Color scheme naming
The workflow's implement node may write the color scheme file under a different name than what `plasma-apply-colorscheme` searches for. Check `~/.local/share/color-schemes/` for the actual filename and verify with:

```bash
plasma-apply-colorscheme <scheme-name> 2>&1
# "already set" = working. "does not exist" = name mismatch.
```

---

## See Also

- Known KDE issues / quirks → `kde-known-issues.md`
- Konsole transparency bug → `konsole-wayland-transparency.md`
- Manual baseline restore → `baseline-restore-procedure.md`
- Wallpaper sourcing → `wallpaper-sourcing.md`
