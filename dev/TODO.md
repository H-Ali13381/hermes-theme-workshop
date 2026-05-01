# linux-ricing TODO

## Recommended Next Tasks

- [x] **[PRIORITY] Add reusable `gsettings` snapshot/restore support for undo**
  Build a generic helper for materializers to record prior `gsettings` values
  before applying changes, plus a matching `ricer_undo.py` restore path. Use this
  as the foundation for GTK, GNOME Shell, and GNOME lockscreen rollback fixes.
  **Done:** `core/process.py::gsettings_get` reads one key in GVariant format and
  returns it as a string passable directly to `gsettings set`. All three materializers
  call it before every `gsettings set` and store `previous_value` in the change record.
  `ricer_undo.py::_undo_gsettings` restores from `previous_value`; when the field is
  absent (legacy manifest) the change is skipped with a diagnostic message rather than
  crashing. `_APP_UNDO_HANDLERS` registers the handler for `gtk`, `gnome_shell`, and
  `gnome_lockscreen`. `core/undo_describe.py::_describe_change` renders a RESTORE or
  "pre-fix manifest, will skip" line for simulate-undo. Tests: 9 materializer tests in
  `test_gtk_materializer.py`, 7 undo-path tests in `test_kde_undo.py::TestUndoGsettings`.

- [x] **[PRIORITY] Fix GTK non-file-state rollback**
  Update `materialize_gtk()` so changes to
  `org.gnome.desktop.interface` (`gtk-theme`, `icon-theme`, `cursor-theme`) record
  previous values in the manifest and are restored by undo. Add tests for fresh
  manifests and legacy manifests with missing previous-state fields.
  **Done:** `materialize_gtk` calls `gsettings_get` for each key before applying and
  stores `previous_value` in the change record. `_undo_gsettings` restores all three
  keys; legacy manifests (`previous_value=None` or key absent) are skipped gracefully.
  Fresh-manifest and legacy-manifest undo paths covered by `TestUndoGsettings`.

- [x] **[PRIORITY] Fix GNOME Shell and GNOME lockscreen rollback**
  Apply the same `gsettings` snapshot/restore pattern to GNOME color-scheme and
  lockscreen color/shading settings so undo fully returns persistent GNOME state to
  its pre-apply values.
  **Done:** `materialize_gnome_shell` snapshots `color-scheme` before setting it.
  `materialize_gnome_lockscreen` snapshots all three `org.gnome.desktop.screensaver`
  keys (`primary-color`, `secondary-color`, `color-shading-type`). Both record
  `previous_value`; `_undo_gsettings` restores them. Full test coverage in
  `TestUndoGsettings` and `GnomeShell/GnomeLockscreenGsettingsSnapshotTests`.

- [x] **[PRIORITY] Make Flatpak GTK/icon overrides reversible**
  Snapshot user Flatpak override state before applying GTK/icon filesystem
  overrides, then remove only Hermes-added overrides or restore the prior override
  state during undo.
  **Done:** `materialize_gtk` snapshots `flatpak override --user --show` before applying
  and stores `flatpak_override_snapshot` + `filesystems_added` (only overrides not
  already present) in the manifest. `_undo_flatpak_override` removes only the tracked
  filesystems via `--nofilesystem`. `_undo_gtk` dispatches both gsettings and
  flatpak-override records. `_describe_change` renders a REMOVE line for simulate-undo.
  Tests: `FlatpakOverrideSnapshotTests` (4 materializer tests), `TestUndoFlatpakOverride`
  (4 undo tests), `TestDescribeChangeNewHandlers` (2 describe tests).

- [x] **[PRIORITY] Add KDE Look-and-Feel undo handling**
  Register an `lnf` undo handler that reapplies the previous global theme and
  safely cleans up generated Hermes Look-and-Feel packages when appropriate.
  **Done:** `_undo_lnf` reapplies `previous_lnf` via `plasma-apply-lookandfeel --apply`
  and removes the generated `hermes-*` LnF package directory only when it is safely
  under `~/.local/share/plasma/look-and-feel/`. Registered in `_APP_UNDO_HANDLERS`.
  `_describe_change` renders REAPPLY + REMOVE lines for simulate-undo. Tests:
  `TestUndoLnf` (4 tests) + 2 describe tests in `TestDescribeChangeNewHandlers`.

- [ ] **[PRIORITY] Improve undo and dry-run risk reporting**
  Ensure dry-run and simulate-undo report non-file state mutations, generated
  directories, legacy manifest gaps, and reload requirements clearly before users
  apply or rollback a rice.

- [x] **[PRIORITY] Formalize KDE post-workflow finalization as workflow code**
  The Mossgrown Throne session exposed that Step 8 completion can leave the agent
  improvising outside the rails. Wallpaper, color-scheme reapply, cursor setting,
  Kitty reload, Fastfetch `config.json`/`config.jsonc` handling, Konsole theming,
  and plasmashell/KWin health checks must be represented as a deterministic
  post-implementation/finalization node or task queue — not free-form agent work.
  The workflow should know what remains after core `element_queue` implementation,
  execute it in a fixed order, record outcomes in `impl_log`/handoff, and stop with
  explicit unsupported/skipped statuses when an item cannot be automated safely.

- [x] **[PRIORITY] Add hard guards for dangerous desktop and terminal commands**
  Documentation is not enough for destructive desktop operations. Add a safe KDE
  reload wrapper that is the only allowed path for KWin restarts: never run raw
  `kwin_wayland --replace`; if it must run, immediately verify/restart
  `plasmashell` and report both PIDs/statuses. Add process-safety rules/helpers so
  agents never `pkill`/signal all Konsole/terminal processes or kill the terminal
  currently hosting the interaction; terminal actions must target an explicitly
  identified PID/session or be deferred to next launch.

- [x] **[PRIORITY] Verify effective desktop state, not only written files**
  Score gates currently focus on target files and palette text. Add a post-apply
  effective-state audit that checks what KDE/apps are actually using: active
  KDE colorscheme, active Konsole `DefaultProfile` and its `ColorScheme`, Kitty's
  effective palette after stale inline values are removed, wallpaper path, cursor
  theme, Fastfetch load path, and whether `plasmashell`/KWin are alive. Feed these
  checks into scoring/handoff so "file written but not active" cannot pass.

- [x] **[PRIORITY] Finish root-cause fixes for Mossgrown Throne regressions in code + tests**
  Do not leave session-learned failures as SKILL.md workarounds only. Ensure the
  actual workflow/materializer code and tests cover: Kitty stale inline palette
  cleanup when injecting `theme.conf`; Konsole theming using the active
  `konsolerc [Desktop Entry] DefaultProfile`; KDE `window_decorations:kde` spec,
  apply, and verify agreeing on `hermes-<theme-name>.colors`; Fastfetch writing or
  linking the path the installed Fastfetch version loads; and score gates rejecting
  missing/incorrect active config. Some fixes are present in the working tree —
  complete, validate, and keep them covered by focused regression tests.

- [x] **[PRIORITY] Consolidate stale Konsole/KDE documentation into one source of truth**
  `SKILL.md`, `KDE/konsole.md`, and `references/konsole-wayland-transparency.md`
  can drift. Update stale guidance that implies opacity belongs in a Konsole
  `.colorscheme` or assumes a hardcoded `linux-ricing.profile`. Canonical rules:
  read `~/.config/konsolerc` first; edit the active `DefaultProfile`; `Opacity`
  belongs in `[Appearance]` of the `.profile`; native Plasma 6 Wayland may ignore
  Konsole opacity entirely; prefer Kitty when transparency is a design requirement.

- [x] **[PRIORITY] Add capability probes and unsupported-feature exits**
  Before attempting effects like terminal transparency, detect Plasma version,
  Wayland vs X11/XWayland, compositor/blur state, terminal emulator, and known
  platform bugs. If a feature is unsupported (e.g. Konsole opacity on native
  Plasma 6 Wayland), stop after one verified config attempt, mark it unsupported
  in the handoff, and select the documented workaround instead of repeatedly
  debugging a known-broken path.

- [x] **[PRIORITY] Make process rails machine-enforced, not agent-memory-based**
  The skill should make the correct path the only executable path. Encode rails as
  workflow state, allowed command wrappers, mandatory preflight/postflight checks,
  retry limits, and regression tests. After Step 8, the agent should not ask
  "what's next?" from scratch; it should present the remaining tracked tasks,
  complete the safe ones, and ask only for genuinely required user decisions.

- [x] **[PRIORITY] Harden workflow resume/bridge/model configuration paths**
  The session hit brittle resume/bridge behavior: stdin-driven retries were awkward,
  bridge-script docs had previously contained garbled API-key extraction, and model
  selection can drift from Hermes config. Replace ad hoc bridge usage with a tested
  resume/control interface, ensure API keys/model are loaded consistently from
  Hermes config/env, and add tests or smoke checks for retry/accept/skip control
  paths so recovery from score gates does not require improvisation.

- [x] **[PRIORITY] Add reliable visual verification artifacts**
  Screenshot capture and visual review were unreliable in the session. Provide a
  deterministic visual verification path: capture screenshots with KDE-compatible
  fallbacks (`spectacle` before `grim` on Plasma Wayland), store them in the session
  directory, reference/open them in the handoff, and make it explicit when automated
  vision analysis is unavailable rather than looping on unattached local images.

## Upcoming Features

- [ ] **[FEATURE] EWW widget library expansion + deeper customization**
  Today, `materialize_eww` ships exactly one widget (`hermes-clock`, a
  top-right time+date overlay) generated from a single
  `templates/eww/hermes-theme.yuck.template` and a single SCSS palette
  template. Anything beyond this requires the user to hand-write yuck.
  Build out a selectable widget library with palette-aware styling so a
  rice can compose a full bar / overlay set from declarative config:
  - **Bar widgets**: workspace indicator (per-WM: KWin virtual desktops,
    Hyprland workspaces, sway), window title / focused-app, taskbar
    (icon-only and titled variants), launcher button, power menu.
  - **System stat widgets**: CPU / RAM / GPU usage (graph + numeric),
    network throughput, disk I/O, battery (with charge state icon),
    temperatures, fan RPM.
  - **Media + audio**: now-playing (mpris2 via `playerctl`), volume
    slider with mute toggle, microphone mute indicator, audio sink
    selector.
  - **Comms / status**: notification history (read from `dunst-history`
    or `swaync`), bluetooth devices, network manager (SSID + signal),
    VPN status, calendar (next event from `khal`/`gcal`).
  - **Weather / time variants**: weather (OpenWeatherMap or wttr.in),
    moon phase, world-clock multi-row, focus/Pomodoro timer.
  - **Layout primitives**: vertical sidebar, top/bottom bar, floating
    overlay, dropdown panel toggled by hotkey, modal popup.
  - **Theming surfaces per widget**: border, padding, font, glyph set
    (nerd / emoji / ascii), background gradient / texture / blur,
    animation duration, hover effects, transitions.
  **Approach:** Promote `templates/eww/` from one file to a
  per-widget directory tree (`widgets/clock/`, `widgets/workspaces/`,
  ...), each with its own `.yuck`, `.scss`, and helper `scripts/`.
  Add `design["eww"]` schema (`enabled_widgets`, `bar_layout`,
  `overlay_widgets`, per-widget overrides). Materializer composes the
  selected set into `eww.yuck` and `eww.scss` via includes. Per-widget
  scripts (e.g. `getvol`, `getbattery`, `getnet`) installed under
  `~/.config/eww/scripts/` from `templates/eww/scripts/`. Mirror
  Rofi/notifications/GTK/Qt/cursor/starship/fastfetch TODOs in scope.

- [ ] **[FEATURE] Fastfetch shell-rc gate management + deeper customization**
  Today, `materialize_fastfetch` only writes `~/.config/fastfetch/config.jsonc`
  (recently fixed: was writing `config.json` which fastfetch never auto-loads,
  and was stripping the `#` from hex colors which fastfetch 2.x rejects).
  The materializer never touches shell rc files, so whether fastfetch
  auto-runs at terminal launch is left to the user's hand-edited `.bashrc`/
  `.zshrc`. This causes two bad UXs for fresh users:
  - **No auto-run gate**: fastfetch fires in every shell \u2014 including
    VSCode integrated terminals, AI agent terminals, SSH non-interactive
    sessions, tmux pane splits \u2014 spamming output and breaking tooling.
  - **Hand-rolled gate**: users have to know the right `$KONSOLE_VERSION`
    / `$KITTY_WINDOW_ID` env vars and write the conditional themselves.
  **Approach:** Add an optional, opt-in shell-rc gate writer to
  `materialize_fastfetch`:
  - Detect supported shells (`bash`, `zsh`, `fish`) and their rc files.
  - Insert a marked block (`# linux-ricing: fastfetch gate {start,end}`)
    that gates `fastfetch` to "main terminals" only:
    `[[ -n "$KONSOLE_VERSION" || -n "$KITTY_WINDOW_ID" || -n "$ALACRITTY_WINDOW_ID" || -n "$WEZTERM_PANE" ]] && fastfetch`.
  - Idempotent: replaces the block if present, never duplicates.
  - Opt-in via `design["fastfetch"]["manage_shell_rc"]` and gated on
    interactive confirmation in `ricer.py apply` (don't silently edit
    `.bashrc`).
  - Backups via existing `backup_file`.
  Also bundle deeper visual customization while in the materializer:
  - Custom logo (file path, image, kitty/sixel inline, palette-recolored
    SVG\u2192PNG) instead of `type: "auto"`.
  - Module set / order / format strings exposed via `design["fastfetch"]`.
  - Per-module separator / icon glyph customization (nerd / emoji / ascii).
  - Truecolor / 256-color / monochrome fallback handling.

- [ ] **[FEATURE] Starship prompt deeper customization**
  Today, `_build_starship_toml` writes a fixed-shape `~/.config/starship.toml`
  with the 10-key palette under `[palettes.<rice>]` and styles for:
  `character`, `directory`, `git_branch`, `git_status`, `cmd_duration`,
  `username`, `hostname`. (Bug fix: palette refs are bare names, not
  `$prefixed`.) Several customization surfaces are inaccessible:
  - **Format string**: locked to starship's default. Designs cannot
    request multi-line prompts, right-prompts (`right_format`), custom
    section ordering, or framed/boxed prompt styles.
  - **Per-module symbols / glyphs**: directory truncation, branch
    symbols (`ﰌ`, ``), status icons, lang module icons (rust , python
    , node , etc.) all hard-coded. Could expose a `design["prompt"]`
    `glyph_set` (nerd / emoji / ascii).
  - **Lang module styling**: `nodejs`, `python`, `rust`, `golang`,
    `docker_context`, `kubernetes`, etc. modules are not configured at
    all \u2014 they use upstream defaults (often colorful blue/green) which
    will clash with the rice palette.
  - **Background fills**: starship supports `bg:<color>` for solid pill
    segments (powerline-style). Designs cannot request this.
  - **Time / battery / OS modules**: not enabled.
  - **Profile selection**: the entire prompt could be one of several
    presets (`pure`, `bracketed-segments`, `nerd-font-symbols`,
    `tokyo-night`-style); currently only the default shape is generated.
  **Approach:** Promote `_build_starship_toml` to a Jinja template
  (`templates/starship/starship.toml.template`). Add `design["prompt"]`
  schema (`preset`, `glyph_set`, `multiline`, `right_format`, `bg_fill`,
  `enabled_lang_modules`, `time_format`, `battery_thresholds`). Mirror
  Rofi/notifications/GTK/Qt/cursor TODOs in scope.

- [ ] **[FEATURE] KDE lock screen deeper customization**
  Today, `materialize_kde_lockscreen` writes:
  - `kscreenlockerrc[Greeter].Theme` (light vs dark greeter LnF, by palette).
  - `kscreenlockerrc[Greeter].WallpaperPlugin = org.kde.image`.
  - `kscreenlockerrc[Greeter][Wallpaper][org.kde.image][General].Image`
    (resolved from `design.lockscreen_wallpaper` \u2192 `design.wallpaper`
    \u2192 current desktop wallpaper snapshot).
  - `...General.FillMode` (stretched by default).
  Several customization surfaces are inaccessible:
  - **Custom greeter LnF**: locked to upstream Breeze. Could fork
    `org.kde.breezedark.desktop`, recolor its QML clock + password box +
    user avatar background to palette accents, and ship under
    `~/.local/share/plasma/look-and-feel/<rice>-greeter.desktop`.
  - **Wallpaper plugin variants**: only `org.kde.image` supported. Plasma
    also offers `org.kde.slideshow`, `org.kde.color`, `org.kde.potd`
    (picture-of-the-day), and third-party plugins. Designs that want
    a solid-color or palette-gradient lockscreen cannot express it.
  - **Lock screen blur / transition / clock font / clock format**: not
    exposed (Plasma supports these via the greeter QML / `kscreenlockerrc`).
  - **Power management strings / unlock hint**: customizable per rice.
  - **SDDM login screen sync**: the lock screen and the SDDM login screen
    are separate surfaces but usually want the same look. SDDM theming
    requires writes to `/etc/sddm.conf.d/` (root) and a custom theme
    package; could be optional sudo-gated.
  **Approach:** Add `design["lockscreen"]` schema (`greeter_theme_fork`,
  `wallpaper_plugin`, `fill_mode`, `clock_font`, `clock_format`,
  `unlock_hint`, `blur_radius`). Implement greeter-fork generator akin to
  `_build_lnf_package`. Gate SDDM behind explicit opt-in flag.

- [ ] **[FEATURE] Cursor + Icon theme deeper customization**
  Today, `materialize_cursor` only points the system at an existing installed
  cursor theme name (writes `kcminputrc`, `kdeglobals[General].cursorTheme`,
  `~/.icons/default/index.theme`, `gsettings cursor-theme`, then refreshes via
  `plasma-apply-cursortheme` + kwin reconfigure). `materialize_icon_theme`
  has more depth (`icon_theme_gen.create_palette_icon_theme` recolor + optional
  fal.ai generation + `papirus-folders -C <color>`), but several surfaces are
  inaccessible:
  - **Cursor recolor / generation**: no equivalent of `icon_theme_gen` for
    cursors. XCursor binary format makes this nontrivial; an approach is to
    fork an installed theme (e.g. `Breeze_Light`), tint its PNG frames to
    palette `accent` / `primary` via PIL hue-rotate, regenerate XCursor
    binaries via `xcursorgen`, and install under
    `~/.local/share/icons/<rice>-cursors/`.
  - **Cursor size / animation**: `kcminputrc[Mouse].cursorSize` and
    Plasma's pointer animation toggles are not exposed.
  - **Icon palette overrides per category**: `papirus-folders` only sets
    the global folder accent. Categories like `mimetypes`, `places`,
    `apps`, `actions`, `devices`, `status` could each take a palette key
    (e.g. devices = `secondary`, actions = `accent`).
  - **Symbolic icon recolor**: GTK / libadwaita symbolic icons render
    monochrome \u2014 their color comes from the GTK theme, not the icon
    theme. Could expose this in the GTK gtk.css template.
  - **Cursor theme bundling into the LookAndFeel package**: currently
    `_build_lnf_package` references `cursor_theme` by name only. Bundling
    a recolored cursor fork into `<lnf>/contents/cursors/` would make the
    theme self-contained for sharing.
  **Approach:** Add `design["cursor"]` schema (`size`, `recolor`,
  `tint_keys`) and `design["icons"]["category_overrides"]` schema. Implement
  PIL-based cursor recolor pipeline as a sibling to `icon_theme_gen`.

- [ ] **[FEATURE] Qt / Kvantum / Plasma LookAndFeel deeper customization**
  Today, `materialize_kvantum` regenerates a fork of `KvArcDark`'s SVG with
  `_svg_color_map` swapping a fixed list of grey/blue hex strings to palette
  values, then writes a hand-rolled `kvconfig` (`_build_hermes_kvconfig`) and
  flips `widgetStyle` to `kvantum`. `materialize_lnf` ships a minimal
  `defaults` file and `metadata.json`. Several customization surfaces are
  inaccessible from the design schema:
  - **Kvantum geometry**: per-element border radius (buttons / menus /
    tabs), frame width, button padding, indicator size, focus ring style.
  - **Kvantum behavior**: animation durations, hover/pressed lightness
    deltas, gradient direction (currently flat fills only), drop shadows.
  - **Base SVG choice**: locked to `KvArcDark`/`KvAdaptaDark`/`KvFlat`/
    `KvDark`. Designs cannot request a different shape language (e.g.
    `KvBubble`, `KvCurves3d`, custom forks).
  - **Right-click menus / popups**: no per-element accent (e.g. checked
    item highlight, separator color, submenu indicator).
  - **Plasma LookAndFeel splash screen / sddm theme / lockscreen
    wallpaper bundling**: `_build_lnf_package` only writes `defaults`;
    no `splash/`, `lockscreen/`, `previews/` assets generated from
    palette + wallpaper.
  - **Plasma theme fork**: `materialize_plasma_theme` only sets the name
    (default \u2192 default no-op). Could fork `default` per-rice with
    palette-recolored `dialogs/`, `widgets/`, `tooltips/` SVG fragments.
  **Approach:** Promote the inline SVG color map and `_build_hermes_kvconfig`
  to Jinja templates with palette + design-schema inputs; expose
  `design["qt"]` schema (`base_svg`, `border_radius`, `button_padding`,
  `frame_width`, `animation_ms`, `gradient`, `menu_accent`, `splash_image`,
  `sddm_wallpaper`, etc.). Mirror Rofi/notifications/GTK TODOs in scope.

- [ ] **[FEATURE] GTK 3 / GTK 4 / libadwaita deeper customization**
  Today, `materialize_gtk` writes a fixed-shape `gtk.css` covering only:
  `window`, `headerbar`, `entry`, `entry:focus`, `button`, `button:hover`,
  plus libadwaita `@define-color accent_color / destructive_color /
  success_color / warning_color / error_color / accent_bg_color /
  accent_fg_color`. Many palette\u2192widget surfaces are not exposed:
  - `headerbar` border/shadow/title font + subtitle styling.
  - `button.suggested-action`, `button.destructive-action`, `.flat`,
    `.linked` button variants and toggle button states.
  - `popover`, `menu`, `menuitem`, `tooltip` (currently inherit defaults).
  - `notebook tab`, `stack-switcher`, `viewswitcher`, sidebar.
  - `selection`, `treeview` row hover/selection colors.
  - `scrollbar`, `progressbar`, `switch`, `checkbutton`, `radiobutton`.
  - libadwaita window border-radius, shadow, `card` widget background.
  - Per-element border radius, font family override, background textures
    / gradients (palette-derived `linear-gradient(...)` or PNG fills written
    into the rice-session dir).
  - GTK theme override choice (currently always `Adwaita-dark` / `Adwaita`
    fallback; could be a custom forked theme generated per-rice).
  **Approach:** Promote the inline f-string in `_build_gtk_css` to a Jinja
  template (`templates/gtk/gtk.css.template`) with a thorough widget map.
  Add optional `design["gtk"]` schema (`border_radius`, `shadow`,
  `body_font`, `header_font`, `button_radius`, `texture_path`, etc.) with
  sensible palette-derived defaults so existing designs keep working
  unchanged. Mirror Rofi/notifications TODOs in scope.

- [ ] **[FEATURE] KDE / Plasma notification popup deep customization**
  Today, Plasma notification popups inherit colors from the global colorscheme
  written by `materialize_kde` (`Colors:Window` for chrome, `Colors:View` for
  body, `Colors:Tooltip` only for actual tooltips). There is no way to skin
  notifications independently of the rest of the desktop without recoloring
  every dialog and window. Provide a dedicated `materialize_plasma_notifications`
  surface so the rice can give popups a distinct identity:
  - Full palette override per-urgency (low / normal / critical) using palette
    keys (e.g. critical \u2192 `danger` accent stripe, success-style green for
    `notify-send -u low -h string:category:transfer.complete`).
  - Font family + size override (e.g. force monospace prompt-style popups).
  - Border width, color, radius, and optional drop-shadow.
  - Background texture / gradient (palette-derived PNG/SVG written into the
    rice-session dir, similar to wallpaper debug strip).
  **Approach:** Plasma notification visuals are driven by the active Plasma
  theme's `dialogs/background.svg` and the colorscheme. To customize without
  hijacking the global colorscheme, generate a per-rice forked Plasma theme
  (palette-recolored copy of `default`) targeting only `dialogs/background.svg`
  and `widgets/notifications.svgz`, then set it via `plasma-apply-desktoptheme`.
  Wire optional `design["notifications"]` schema (font, urgencies, border,
  texture path) and fall back to colorscheme inheritance when absent.

- [ ] **[FEATURE] Rofi: richer border + background texture support**
  Current `materialize_rofi` exposes a fixed border (`2px solid @primary`,
  `border-radius: 8px`) and solid-color backgrounds only. RASI supports more
  expressive styling that is not yet wired through the design system:
  - `background-image: linear-gradient(...)` / `url("...")` for window and
    inputbar fills (patterns, palette-derived gradients, raster textures).
  - Per-side `border` widths and `border-color` (e.g. asymmetric / accent
    underline only).
  - Variable `border-radius` per element (window vs inputbar vs element).
  - Optional drop-shadow / outline emulation via stacked windows.
  **Approach:** Extend `design["launcher"]` schema with optional
  `border_style`, `border_radius`, `background_image`, `gradient` keys; let
  materializer fall back to current defaults when absent. For texture support,
  generate palette-derived PNG/SVG fills into the rice-session dir (similar to
  how the wallpaper debug strip is generated) and reference them by absolute
  path in the rasi.

- [ ] **[FEATURE] Hermes document style / `soul.md` theme bridge**
  When a desktop rice is active, generate a matching Hermes document/artifact
  style context from the same design system. Use the theme palette and suitable
  fonts for user-facing generated documents, reports, HTML handoffs, and other
  artifacts when the user has not explicitly specified another style.
  **Approach:** Add a safe optional materializer that updates only a managed
  block in `~/.hermes/soul.md` (or equivalent Hermes style context), preserving
  user-authored content. Derive body, heading, and monospace fonts plus document
  colors from `design["document_style"]`, `design["typography"]`, `palette`,
  `mood_tags`, and stance. Explicit user styling should always override this
  default theme context.

## Open Issues

### Architectural Concerns

- [x] **[ARCH] Tight coupling between `scripts/ricer.py` and `workflow/` layer**
  `workflow/nodes/implement/apply.py` shells out to `ricer.py` via `subprocess.run`.
  The LangGraph workflow cannot access Python functions directly, losing type safety
  and making error handling coarser (exit codes + stdout/stderr only).
  **Fix:** Long-term — expose `ricer.py` materializers as a Python API that
  `apply.py` can import and call directly.
  **Done:** `apply.py` now imports `materialize`, `discover_apps`, and `APP_MATERIALIZERS`
  directly from `scripts/`; subprocess, temp-file, and exit-code handling removed.
  Tests updated in `test_implement_spec.py` and `test_ricer_cli_routing.py`.

- [x] **[ARCH] Dual session tracking systems**
  Two parallel mechanisms: (1) `session_manager.py` + `~/.config/rice-sessions/.current`
  symlink (legacy), and (2) LangGraph SQLite checkpointing in
  `~/.local/share/linux-ricing/sessions.sqlite`. Different directory naming
  conventions (`session-YYYYMMDD-HHMM` vs `rice-YYYYMMDD-HHMM-uuid`). Could confuse
  resume behavior.
  **Fix:** Consolidate to a single canonical session directory format.
  **Done:** `session_manager.py cmd_init` now creates `rice-YYYYMMDD-HHMM-uuid6` dirs
  (same format as `workflow/run.py`). `cmd_rename` regex unanchored to handle the new
  format. `cmd_resume_check` queries SQLite first and skips filesystem dirs whose names
  match a known workflow thread_id, eliminating duplicate entries. `workflow/run.py
  _init_session_dir` now updates `.current` symlink and writes a `session.md` header
  aligned with `SESSION_HEADER_TEMPLATE` (adds `Session dir:` line and `---` separator).

### Bugs

- [x] **[BUG] `cleanup/__init__.py`: Bar reload hardcoded to waybar**
  When `bar:polybar` is in the impl_log, `cleanup_node` still calls `reload_waybar()`
  instead of reloading polybar. The notification path correctly checks which provider
  was implemented; the bar path should do the same.
  **Fix:** Mirror the notification provider-lookup pattern: inspect the actual bar
  element (`bar:waybar` vs `bar:polybar`) and dispatch to the correct reload function.
  Add a `reload_polybar` helper to `reloader.py`.

- [x] **[BUG] `implement/__init__.py`: Hard-skip after max retries doesn't append to `errors`**
  Every other SKIP path (apply failure, user-skip) appends a string to the `errors`
  reducer.  The max-retries hard-skip return is missing `"errors": [...]`, so the
  deviation goes unrecorded in the session error log.
  **Fix:** Add `"errors": [f"{element}: {verdict}"]` to the hard-skip return dict.

- [x] **[BUG] `install/__init__.py`: Any non-"cancel"/non-"skip" input silently installs packages**
  The interrupt message tells the user to type `'install'`, but the code only checks
  for `"cancel"` and `"skip"` — any other string (including typos or an empty reply)
  falls through and triggers installation.
  **Fix:** Require the user to type exactly `"install"` to proceed; treat any other
  unrecognised input as a re-prompt (or skip) rather than implicit confirmation.

- [x] **[BUG] `baseline.py`: Returns `current_step: 5`, conflicting with `install_node`**
  Both `baseline_node` and `install_node` return `{"current_step": 5}`.  After
  baseline completes, the session state falsely claims step 5 (Install) is done before
  Install has even run.
  **Fix:** `baseline_node` should not advance `current_step` (leave it at 4, set by
  `plan_node`); only `install_node` should claim step 5.

### Code Quality

- [x] **[QUALITY] `session.py` line 78: unnecessary f-string prefix**
  `print(f"[session] append_item: session_dir is empty — skipping", file=sys.stderr)`
  has an `f` prefix with no format placeholders.  This is dead syntax.
  **Fix:** Remove the `f` prefix.

- [x] **[QUALITY] `config.py`: `MODEL` constant defined after `get_llm()` that references it**
  `get_llm()` is defined at line 65 and references `MODEL` at line 74; `MODEL` is
  defined at line 114.  While valid Python, constants should precede the functions that
  use them for readability and grep-ability.
  **Fix:** Move the module-level constants (`MODEL`, `SKILL_DIR`, etc.) to the top of
  the file, before `get_llm()`.

- [x] **[QUALITY] `explore.py`: warning printed to stdout instead of stderr**
  `_parse_direction()` prints `[Explore][WARN]…` to stdout via bare `print()`.
  Warning and error messages should go to `stderr`.
  **Fix:** Import `sys` and use `print(…, file=sys.stderr)`.

- [x] **[QUALITY] `detectors.py`: single-letter variable `l` in list comprehensions**
  `detect_screens` and `detect_gpu` use `l` (lowercase L) as the loop variable.
  PEP 8 prohibits `l`, `O`, and `I` as single-character names due to visual ambiguity
  with `1`, `0`, and `|`.
  **Fix:** Rename to `line` in both comprehensions.

- [x] **[QUALITY] `score.py`: `shape` scores 1 when no targets were declared**
  When `spec["targets"]` is empty (e.g. LLM spec failure), both `files_written` and
  `files_missing` are 0.  The `else` branch of the `shape` scoring block gives 1,
  inflating the score for an element that wrote nothing.
  **Fix:** Add an explicit `elif files_missing == 0 and files_written == 0` branch
  that sets `sc["shape"] = 0`.

- [x] **[QUALITY] `handoff.py` and `plan.py`: trailing extra blank lines**
  Both files end with two blank lines instead of the standard single trailing newline.
  **Fix:** Remove the extra blank line from the end of each file.

### Scripts Layer Bugs & Quality Issues

- [x] **[BUG] `materializers/hyprland.py`: backup path discarded, undo cannot restore `hyprland.conf`**
  `backup_file(hyprland_conf, ...)` return value is thrown away at line 44; the
  resulting `set_borders` change dict has no `"backup"` key.  `ricer.undo()` iterates
  `backup` keys to find files to restore — missing the key means `hyprland.conf` is
  never restored after an undo.
  **Fix:** Capture the return value and add `"backup": backup_path` to the changes dict.

- [x] **[BUG] `materializers/kde_extras.py`: icon theme generation runs during `dry_run`**
  `materialize_icon_theme` calls `icon_theme_gen.create_palette_icon_theme` and
  `icon_theme_gen.generate_icon_via_fal` before it checks `if dry_run:`.  A dry-run
  must not write icon files to disk.
  **Fix:** Move the `dry_run` guard before the icon-generation block (or pass
  `dry_run` into the generation helpers).

- [x] **[QUALITY] `core/colors.py`: no 3-digit hex normalization**
  `hex_to_rgb` and `hex_to_rgb_tuple` assume exactly 6 hex digits after `#`.
  If an LLM returns a 3-digit shorthand (`#abc`) the slice `h[0:2]` returns `"ab"` and
  `h[4:6]` silently reads junk or raises `ValueError`.
  **Fix:** Expand 3-digit hex to 6-digit in both functions (e.g. `"abc"` → `"aabbcc"`).

- [x] **[QUALITY] `core/templates.py`: Jinja2 `Environment` without `StrictUndefined`**
  `jinja2.Environment()` uses the default `Undefined` class, which silently renders
  missing variables as empty strings.  A typo in a template key (`{{priamry}}`) would
  produce a broken config with no error.
  **Fix:** Use `undefined=jinja2.StrictUndefined` so missing variables raise immediately.

- [x] **[QUALITY] `materializers/system.py`: `materialize_gtk` hardcodes font, ignores design typography**
  `font_name` in the GTK context is always `"JetBrains Mono 10"` regardless of what
  `design["typography"]` contains.  Every other materializer reads from the design
  typography dict.
  **Fix:** Derive font from `design.get("typography", {}).get("ui_font", "JetBrains Mono")`.

- [x] **[QUALITY] `materializers/bars.py`: `import sys` inside function body**
  `materialize_polybar` has `import sys` buried inside a conditional branch (line 98).
  Module-level imports are the Python convention and eliminate repeated import overhead.
  **Fix:** Move `import sys` to the module-level imports.

- [x] **[QUALITY] `materializers/kde_extras.py`: unused `import os` in `materialize_kvantum`**
  `materialize_kvantum` imports `os` at the top of its body but never uses `os`.  The
  import is dead code.
  **Fix:** Remove the unused `import os` from `materialize_kvantum`.

### New Bugs & Quality Issues

- [x] **[BUG] `materializers/wallpaper.py`: hyprpaper backup path discarded, undo cannot restore `hyprpaper.conf`**
  `backup_file(hyprpaper_conf, ...)` return value is thrown away (line 127) and
  no `config_backup` key is added to the change dict.  `undo()` has a comment
  saying "the generic file-restore loop above" handles it, but that loop checks
  for `backup`, `config_backup`, etc. — none of which exist in the hyprpaper
  change dict.  `hyprpaper.conf` is therefore never restored after `ricer undo`.
  **Fix:** Capture the return value and store it as `"config_backup"` in the
  change dict so the generic restore loop can find and use it.

- [x] **[BUG] `materializers/terminals.py`: `materialize_alacritty` uses `jinja2.Environment()` without `StrictUndefined`**
  Line 181 creates `jinja2.Environment()` with the default `Undefined` class,
  which silently renders missing variables as empty strings.  Every other template
  path (`render_template`) already uses `StrictUndefined`.  A typo in a bright-
  color key would produce a corrupt colors.toml with no error.
  **Fix:** Use `jinja2.Environment(undefined=jinja2.StrictUndefined)` here.

- [x] **[BUG] `baseline.py`: `datetime.now()` called without timezone**
  Line 16 uses `datetime.now()` (naive local time) while every other timestamp
  in the codebase uses `datetime.now(timezone.utc)`.  The resulting `baseline_ts`
  is ambiguous and could sort incorrectly relative to UTC `backup_ts` stamps when
  the host timezone is not UTC.
  **Fix:** Import `timezone` from `datetime` and use `datetime.now(timezone.utc)`.

- [x] **[QUALITY] `implement/spec.py`: duplicate dead-code branch in `write_spec`**
  Lines 46-48:
  ```python
  if isinstance(spec, dict):
      return ElementSpec.model_validate(spec).model_dump()
  return ElementSpec.model_validate(spec).model_dump()
  ```
  Both branches are identical — the `if isinstance(spec, dict)` check is dead
  because the unconditional `return` below it does the same thing regardless of
  type.
  **Fix:** Remove the redundant `if isinstance(spec, dict)` branch.

- [x] **[QUALITY] `handoff.py`: ambiguous single-char variable `l` in `_convert_table`**
  Lines 91-92 use `l` (lowercase L) as the loop variable in two list
  comprehensions.  PEP 8 prohibits `l`, `O`, and `I` as single-character names
  due to visual ambiguity with `1`, `0`, and `|`.
  **Fix:** Rename `l` to `line` in both comprehensions.

- [x] **[QUALITY] `plan.py`: `import re` inside `_extract_html` function body**
  `re` is imported at line 103 inside the function body.  Module-level imports
  are the Python convention and improve readability and import-time clarity.
  **Fix:** Move `import re` to the module-level imports at the top of `plan.py`.

- [x] **[QUALITY] `materializers/kde_extras.py`: `import os` inside `materialize_icon_theme` function body**
  `os` is imported on line 142 inside `materialize_icon_theme`.  Unlike the
  previously-fixed dead import in `materialize_kvantum`, this one IS used
  (`os.environ.get("FAL_KEY", "")`), but it still belongs at module level.
  **Fix:** Move `import os` to the module-level imports.

- [x] **[QUALITY] `materializers/wallpaper.py`: `from pathlib import Path` inside function body**
  `materialize_wallpaper` imports `Path` at line 70 inside the function body.
  `Path` is not imported at the module level despite being used throughout.
  **Fix:** Move `from pathlib import Path` to the module-level imports.

- [x] **[QUALITY] `implement/score.py`: redundant `elif` condition in `shape` scoring**
  The `shape` block reads:
  ```python
  if files_written == 0:
      sc["shape"] = 0
  elif files_written > 0:   # always True when the 'if' is False
      ...
  ```
  Because `files_written = len(...)` is always ≥ 0, the `elif files_written > 0`
  branch is always entered when the `if` is False.  The condition is dead logic.
  **Fix:** Replace `elif files_written > 0:` with a plain `else:`.

- [x] **[ARCH] Tight coupling between `scripts/ricer.py` and `workflow/` layer**
  `scripts/desktop_utils.py:discover_desktop()` and
  `workflow/nodes/audit/detectors.py:detect_wm()` are separate and can drift.
  `desktop_utils.py` checks `ps aux` + `XDG_CURRENT_DESKTOP` more thoroughly;
  `detect_wm()` checks `XDG_CURRENT_DESKTOP` / `DESKTOP_SESSION` + `wmctrl` +
  `plasmashell --version`. They should share a single utility module.
  **Done:** `discover_desktop()` is now the canonical implementation. It gained
  `DESKTOP_SESSION` fallback, `gnome-shell` in the ps scan, and XDG fallbacks for
  gnome and hyprland (matching what the old `detect_wm()` covered). `detect_wm()` is
  now a one-line delegation: `return discover_desktop()["wm"]`. `import os` removed
  from `detectors.py` (was only used in the deleted body).

### Newly Found Bugs & Quality Issues

- [x] **[BUG] `audit/detectors.py`: swww/awww wallpaper path parsing returns garbage**
  Lines 164-165 and 170-172 parse `swww query` / `awww query` output with
  `line.split(":", 1)[-1].strip()`.  The actual output format is
  `<monitor>: image: /path/to/wallpaper.jpg` — splitting on the **first** colon
  gives `" image: /path/to/wallpaper.jpg"` instead of the bare path.
  `materializers/wallpaper.py` correctly uses `re.search(r"image:\s*(\S.*)$", line)`
  for the same data; `detectors.py` must match.
  **Fix:** Replace the split-based extraction with the same regex used in
  `wallpaper.py`.

- [x] **[QUALITY] `materializers/notifications.py`: unused import `yiq_text_color`**
  Line 5 imports `yiq_text_color` from `core.colors` but the function is never
  called anywhere in the file.  Dead imports increase cognitive load and confuse
  static analysers.
  **Fix:** Remove the unused import.

- [x] **[QUALITY] `core/snapshots.py`: redundant `import re as _re` inside `snapshot_konsole_state`**
  Line 97 imports `re as _re` inside the function body, but line 103 uses
  `_re.search()` while the `re.MULTILINE` flag on the same line is read from the
  module-level `re` import.  The function-level alias is unnecessary and mixes two
  references to the same module.
  **Fix:** Remove the `import re as _re` line and replace `_re.search` with `re.search`
  (module-level `re` is already imported).

- [x] **[QUALITY] `scripts/ricer.py`: three `read_text()` calls missing `encoding="utf-8"`**
  Lines 92, 595, and 690 read `manifest.json` with `manifest_path.read_text()`
  (no encoding argument).  All write paths already pass `encoding="utf-8"`.
  On non-UTF-8 locales the reads could raise `UnicodeDecodeError` or silently
  mis-decode content.
  **Fix:** Add `encoding="utf-8"` to all three `read_text()` calls.

- [x] **[QUALITY] `workflow/nodes/refine.py`: `write_text()` missing `encoding="utf-8"` in `_write_design_json`**
  Line 161: `path.write_text(json.dumps(design, indent=2))` omits the encoding
  argument.  `design.json` may contain non-ASCII characters (theme names, descriptions)
  that would be mis-encoded on non-UTF-8 systems.
  **Fix:** Add `encoding="utf-8"`.

- [x] **[QUALITY] `workflow/session.py`: all `read_text()`/`write_text()` calls missing `encoding="utf-8"`**
  Six calls (lines 45, 64, 85, 110, 122, 124) operate on `session.md` without an
  explicit encoding.  `session.md` may contain theme names with non-ASCII characters.
  **Fix:** Add `encoding="utf-8"` to every `read_text()` and `write_text()` call.

- [x] **[QUALITY] `scripts/session_manager.py`: `read_text()`/`write_text()` calls missing `encoding="utf-8"`**
  `update_status_line`, `update_header_theme`, `update_header_session_dir`, and
  `cmd_append_item` all read/write `session.md` without specifying encoding.
  **Fix:** Add `encoding="utf-8"` to every `read_text()` and `write_text()` call in
  those four functions.

### Newly Found Bugs & Quality Issues (2026-04-29)

- [x] **[BUG] `materializers/notifications.py`: `yiq_text_color` called but never imported**
  Lines 124–125 call `yiq_text_color(palette["primary"])` and
  `yiq_text_color(palette["danger"])`, but the function is not in the module's
  import list (imports only `HOME`, `TEMPLATES_DIR`, `run_cmd`, `backup_file`,
  `render_template`).  Any call to `materialize_swaync()` will raise `NameError`
  at runtime.  A previous TODO entry incorrectly described it as an "unused import"
  and the import was removed while the call sites were left intact.
  **Fix:** Add `from core.colors import yiq_text_color` to the import block.

- [x] **[QUALITY] `generate_panel_svg.py` and `icon_theme_gen.py`: deprecated `Image.LANCZOS`**
  Both files use `Image.LANCZOS` directly (line 35 in `generate_panel_svg.py`,
  line 436 in `icon_theme_gen.py`).  Pillow 10.0 moved this constant to
  `Image.Resampling.LANCZOS` and removed the top-level alias, raising
  `AttributeError` on modern Pillow installs.
  **Fix:** Use `Image.Resampling.LANCZOS` in both files (Pillow ≥ 9.1 supports it;
  keep a compat shim if older Pillow must be supported).

- [x] **[BUG] `install/resolver.py`: `subprocess.TimeoutExpired` not caught in `can_sudo_noninteractive()`**
  Line 70: `subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=5)`
  sets a 5-second timeout but never catches `subprocess.TimeoutExpired`.  On a
  slow or locked sudo, the exception propagates to the caller uncaught, crashing
  the install node instead of gracefully returning `False`.
  **Fix:** Wrap the call in `try/except subprocess.TimeoutExpired` and return `False`.

- [x] **[QUALITY] `workflow/config.py`: bare `except Exception` in `_load_hermes_config` swallows YAML errors silently**
  Line 93: `except Exception: return {}` catches all exceptions — including
  `ModuleNotFoundError` when `yaml` is not installed and `yaml.YAMLError` for
  malformed config — without any diagnostic output.  Operators get no indication
  why the config was silently ignored.
  **Fix:** Log the exception to stderr before returning `{}` so failures are visible.

### Comprehensive Audit Findings (2026-04-29)

#### Deprecated API / Resource Leaks

- [x] **[BUG] `scripts/capture_theme_references.py:555`: `Image.LANCZOS` deprecated in Pillow 10+**
  `cropped.resize((1920, 1080), Image.LANCZOS)` uses the old top-level constant
  removed in Pillow 10.0.  This file was missed when the same fix was applied to
  `generate_panel_svg.py` and `icon_theme_gen.py` in the previous pass.
  **Fix:** Replace with `Image.Resampling.LANCZOS`.

- [x] **[BUG] `scripts/palette_extractor.py:95`: `Image.open()` without context manager causes resource leak**
  `img = Image.open(image_path)` opens a file handle that is never explicitly
  closed.  If an exception occurs during colour-space conversion or thumbnailing,
  the handle leaks.  Pillow documents that images should be used as context
  managers or closed explicitly.
  **Fix:** Wrap with `with Image.open(image_path) as img:` and restructure the
  conversion block accordingly.

- [x] **[QUALITY] `scripts/deterministic_ricing_session.py:448,82,510`: `sys._session_log_path` private attribute abuse**
  `main()` assigns `sys._session_log_path = str(...)` (line 448) and `log()`
  reads it back via `getattr(sys, "_session_log_path", None)` (line 82).
  Injecting custom attributes into the `sys` module is fragile: future Python
  versions may treat leading-underscore names on `sys` specially, and the
  pattern obscures control flow.
  **Fix:** Replace with a module-level `_session_log_path: str | None = None`
  variable updated by `main()` and read directly by `log()`.

- [x] **[QUALITY] `workflow/nodes/cleanup/reloader.py:49,58,67,80,93`: `subprocess.Popen` without stdio redirection leaks handles**
  Five `Popen(["waybar"])`, `Popen(["polybar"])`, `Popen(["dunst"])`,
  `Popen(["mako"])`, and `Popen(["swaync"])` calls launch background daemons
  without redirecting `stdin`/`stdout`/`stderr` to `DEVNULL`.  This means (a) the
  daemon inherits the parent's file descriptors and can corrupt terminal output,
  and (b) Python emits `ResourceWarning` when the un-waited `Popen` objects are
  garbage-collected.
  **Fix:** Add `stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
  stderr=subprocess.DEVNULL` to all five calls so the daemon is fully detached.

#### Missing `encoding=` Arguments

- [x] **[QUALITY] `workflow/config.py:64`: `read_text()` without `encoding="utf-8"` in `_parse_dotenv`**
  `path.read_text().splitlines()` in `_parse_dotenv()` omits the encoding
  argument.  `.env` files may contain non-ASCII values (e.g. themed prompts),
  causing `UnicodeDecodeError` on non-UTF-8 systems.
  **Fix:** Add `encoding="utf-8"` to the `read_text()` call.

- [x] **[QUALITY] `workflow/run.py:239`: `write_text()` without `encoding="utf-8"` in `_init_session_dir`**
  `(session_dir / "session.md").write_text(header)` omits `encoding="utf-8"`.
  The header may contain non-ASCII theme names; omitting encoding risks
  `UnicodeEncodeError` on non-UTF-8 locales.
  **Fix:** Add `encoding="utf-8"`.

- [x] **[QUALITY] `scripts/materializers/wallpaper.py:38,106`: two `read_text()` calls without `encoding="utf-8"`**
  Lines 38 and 106 both read `hyprpaper.conf` with
  `hyprpaper_conf.read_text().splitlines()` — no encoding argument.  The same
  file is *written* on line 133 with `encoding="utf-8"` already.
  **Fix:** Add `encoding="utf-8"` to both `read_text()` calls for symmetry and
  safety on non-UTF-8 systems.

- [x] **[QUALITY] `scripts/materializers/hyprland.py:46,112`: `read_text()` calls missing `encoding="utf-8"`**
  Line 46 reads `hyprland.conf` with `errors="replace"` but no encoding.
  Line 112 reads `hyprlock.conf` the same way.  Both files are written with
  `encoding="utf-8"` (lines 64, 148).
  **Fix:** Add `encoding="utf-8"` alongside `errors="replace"` on both reads.

#### Silent Exception Swallowing

- [x] **[QUALITY] `workflow/config.py:69-70`: bare `except Exception: pass` in `_parse_dotenv` swallows parse errors**
  When reading or parsing the `.env` file fails (e.g. a permission error or a
  malformed line that slips past the guard), the exception is silently ignored
  and `result` may be incomplete.  Unlike `_load_hermes_config` (already fixed to
  log), this sibling function still uses `except Exception: pass`.
  **Fix:** Change to `except Exception as e: print(f"[config] Warning: ...", file=sys.stderr)`.

- [x] **[QUALITY] `workflow/nodes/explore.py:119`: bare `except` drops actual JSON parse error**
  `except Exception: pass` in `_parse_direction` catches but discards the
  specific `json.JSONDecodeError`.  The warning printed after the block is
  generic; including `str(e)` would show *why* parsing failed.
  **Fix:** Change to `except Exception as e:` and include `e` in the warning
  string: `f"... — {e}"`.

- [x] **[QUALITY] `workflow/nodes/refine.py:142`: bare `except` drops JSON parse error detail**
  Same pattern as `explore.py:119`: `except Exception: pass` in
  `_extract_design_json` silently discards the specific decode error.
  **Fix:** Change to `except Exception as e:` and log `e` to stderr.

- [x] **[QUALITY] `workflow/nodes/implement/apply.py:33`: exception caught but never logged**
  `except Exception as e: return {"success": False, "error": str(e)}` captures
  the error in the return dict but writes nothing to stderr.  When the implement
  node fails, there is no visible trace in the terminal output.
  **Fix:** Add `print(f"[apply] materializer error: {e}", file=sys.stderr)` before
  the return.

#### Logic / Correctness

- [x] **[BUG] `workflow/nodes/implement/verify.py:34`: `errors="ignore"` silently drops undecodable bytes**
  `Path(written).read_text(errors="ignore")` discards any bytes that cannot be
  decoded, potentially hiding encoding corruption in written config files.  Every
  other file read in the codebase uses `errors="replace"`.
  **Fix:** Change `errors="ignore"` to `errors="replace"` for consistency and
  to surface corruption as replacement characters rather than silent data loss.

#### Test Quality

- [x] **[QUALITY] `tests/test_kde_materializers.py:432,436`: `assertFalse([list])` is non-idiomatic and fragile**
  `self.assertFalse([c for c in calls if "kwriteconfig6" in c])` checks that the
  filtered list is falsy (empty), which works but reads as "assert this list is
  False" — confusing to reviewers.  The preferred form is
  `self.assertEqual([c for c in calls if ...], [])`.
  **Fix:** Replace both `assertFalse([list])` instances with `assertEqual([...], [])`.

- [x] **[QUALITY] `tests/test_palette_extractor.py:239`: `tempfile.mkdtemp()` without cleanup in `_fake_dir`**
  `_fake_dir()` creates a temp directory with `tempfile.mkdtemp()` but never
  cleans it up.  Every test that calls `_fake_dir` leaks a directory under
  `/tmp`, accumulating over repeated test runs.
  **Fix:** Use `tempfile.TemporaryDirectory()` as a class-level or per-test
  context manager and add cleanup via `self.addCleanup`.

- [x] **[QUALITY] `tests/test_kde_lockscreen_materializer.py:71,87,114,129,142,158`: six `tempfile.mkdtemp()` calls without cleanup**
  All six test methods create a temp directory with `mkdtemp()` and never delete
  it.  Each test run leaves up to six orphaned directories.
  **Fix:** Convert each `tmpdir = Path(tempfile.mkdtemp())` to use an
  `addCleanup(shutil.rmtree, tmpdir)` call immediately after creation.

- [x] **[QUALITY] `tests/test_starship_materializer.py:87,98,107,119,133`: five `tempfile.mkdtemp()` calls without cleanup**
  Same pattern as the lockscreen tests: five test methods create temp
  directories that are never removed.
  **Fix:** Same as above — add `addCleanup` or use `TemporaryDirectory`.

- [x] **[QUALITY] `tests/test_kde_undo.py:48`: `read_text()` without `encoding="utf-8"`**
  `manifest_path.read_text()` in `UndoTests.test_undo_*` reads the JSON
  manifest without specifying encoding.  The same path is *written* with
  `encoding="utf-8"` (line 26).
  **Fix:** Add `encoding="utf-8"` to the `read_text()` call.

### Deep Audit Findings (2026-04-29, Round 2)

#### Crash-Risk Bugs

- [x] **[BUG] `workflow/nodes/refine.py`: missing `import sys` causes NameError on JSON parse failure**
  `_extract_design_json()` prints to `sys.stderr` in its exception handler (added in
  the previous fix pass) but `sys` is never imported in this module.  Any JSON
  decode error during refine will therefore raise `NameError: name 'sys' is not
  defined` on top of the original parse failure, completely hiding the real error.
  **Fix:** Add `import sys` to the import block at the top of the file.

- [x] **[BUG] `workflow/nodes/handoff.py:62`: `response.content` may be `None`, causing `AttributeError`**
  `md_content = response.content.strip()` is called without checking whether the
  LLM returned a non-null response.  If the model's response body is empty or the
  API returns a finish-reason that leaves `content` as `None`, this raises
  `AttributeError: 'NoneType' object has no attribute 'strip'`, crashing the
  handoff node and leaving the session without a summary document.
  **Fix:** Guard with `md_content = (response.content or "").strip()`.

#### Logic Bugs

- [x] **[BUG] `workflow/nodes/implement/score.py:36-41`: `all()` on empty generator returns `True` → inflated `shape` score**
  When `files_written > 0` (files were listed as written) but every listed file has
  since been deleted, the generator `(Path(f).expanduser().stat().st_size > 20 for f
  in ... if Path(f).expanduser().exists())` yields nothing.  `all()` on an empty
  iterable returns `True` by Python definition, so `sc["shape"]` is set to `2`
  (excellent) even though zero files remain on disk.
  **Fix:** Collect the existing-file sizes into an explicit list; if the list is empty
  treat the result as failed:
  ```python
  existing_sizes = [
      Path(f).expanduser().stat().st_size
      for f in verify.get("files_written", [])
      if Path(f).expanduser().exists()
  ]
  all_ok = bool(existing_sizes) and all(s > 20 for s in existing_sizes)
  sc["shape"] = 2 if all_ok else 1
  ```

- [x] **[BUG] `scripts/core/snapshots.py:30,34`: broken INI-section regex silently returns `None`**
  The fallback regex patterns `r"^\[General\][^\[]*^ColorScheme=(.+)$"` and
  `r"^\[KDE\][^\[]*^LookAndFeelPackage=(.+)$"` are broken:  `[^\[]*` matches any
  character except `[`, including newlines, so it greedily consumes entire lines
  before the `^` anchor can match.  With `re.MULTILINE` this pattern almost never
  matches, meaning the fallback to file-based snapshot silently returns `None` for
  the colour scheme and look-and-feel, potentially leaving the snapshot incomplete.
  The same `read_text()` call on line 28 also lacks `encoding="utf-8"`.
  **Fix:** Replace with a two-step section-then-key search:
  ```python
  sec = re.search(r"^\[General\](.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
  if sec:
      m = re.search(r"^ColorScheme\s*=\s*(.+)$", sec.group(1), re.MULTILINE)
      if m: scheme = m.group(1).strip()
  ```
  Apply the same pattern for the `[KDE]` / `LookAndFeelPackage` lookup.
  Also add `encoding="utf-8"` to the `read_text()` call on line 28.

#### Silent Exception Swallowing

- [x] **[QUALITY] `scripts/session_manager.py:82-83,85-88`: two silent `except Exception: return []` blocks**
  `_list_workflow_sessions()` silently swallows both subprocess failure and JSON
  decode errors.  When the workflow runner exits unexpectedly or prints non-JSON
  output, callers receive an empty list with no diagnostic information.
  **Fix:** Change to `except Exception as e:` and print to stderr with context, e.g.
  `print(f"[session_manager] Warning: ...: {e}", file=sys.stderr)`.

- [x] **[QUALITY] `scripts/icon_theme_gen.py:423-424,441-442`: two silent `except Exception: return False` blocks**
  The fal-ai icon generation function catches all API and download/resize exceptions
  without logging.  Callers can only detect failure (return `False`) but cannot
  distinguish network errors, API quota exhaustion, or image-processing failures.
  **Fix:** Add `print(f"[icon_theme_gen] ...: {e}", file=sys.stderr)` before each
  `return False` in the two `except Exception` blocks.

#### Missing `encoding=` Arguments

- [x] **[QUALITY] `workflow/config.py:93`: `read_text()` without `encoding="utf-8"` in `_load_hermes_config`**
  `yaml.safe_load(config_path.read_text())` reads `~/.hermes/config.yaml` without
  specifying encoding.  If the YAML file contains non-ASCII characters (e.g. a
  model name with an accent), this raises `UnicodeDecodeError` on non-UTF-8 locales.
  **Fix:** Change to `config_path.read_text(encoding="utf-8")`.

#### LLM Response Robustness

- [x] **[QUALITY] `workflow/nodes/plan.py:120`: `_extract_html()` returns raw non-HTML content as fallback**
  When the LLM response contains no `<!DOCTYPE` or `<html` marker at all, the
  function falls through to `return content` — returning the raw, possibly
  explanatory text to the caller.  `plan_node()` then writes this verbatim to
  `plan.html`, producing an unrenderable preview file with no warning.
  **Fix:** Return `""` instead of `content` on the final fallback, and print a
  warning to stderr so failures are surfaced:
  ```python
  print("[Plan][WARN] No HTML marker found in LLM response — plan.html will be empty", file=sys.stderr)
  return ""
  ```

#### Test Quality

- [x] **[QUALITY] `tests/test_kde_lockscreen_materializer.py` + `tests/test_starship_materializer.py`: non-idiomatic `__import__("shutil")` pattern**
  Every `addCleanup` call uses `__import__("shutil").rmtree` because `shutil` is not
  imported at the module level.  This works but is non-idiomatic, harder to read,
  and triggers linters.
  **Fix:** Add `import shutil` to the import block of each file and replace all
  `__import__("shutil").rmtree` occurrences with `shutil.rmtree`.

- [x] **[QUALITY] `tests/test_palette_extractor.py:241`: inline `import tempfile, shutil` inside `_fake_dir`**
  `import tempfile, shutil` is done inside the test helper method rather than at
  the module level.  Python re-imports are cheap but the inline `import` hides
  the dependency and violates the project's style (all other test files import at
  module level).
  **Fix:** Move both imports to the top of the file.

- [x] **[QUALITY] `tests/test_kde_materializers.py:368,372`: `write_text()` without `encoding="utf-8"`**
  Two `write_text()` calls in `SnapshotKdeStateTests._run()` write fixture data
  (`kvantum.kvconfig` and `plasma-org…appletsrc`) without specifying encoding.
  **Fix:** Add `encoding="utf-8"` to both calls.

- [x] **[QUALITY] `tests/test_kde_lockscreen_materializer.py:169,181`: `write_text()` / `read_text()` without `encoding="utf-8"`**
  Line 169: `config_path.write_text("[Daemon]\nTimeout=15\n")` writes a fixture
  without encoding.  Line 181: `backup_path.read_text()` reads it back without
  encoding.
  **Fix:** Add `encoding="utf-8"` to both calls.

- [x] **[QUALITY] `tests/test_starship_materializer.py:144,153`: `write_text()` / `read_text()` without `encoding="utf-8"`**
  Line 144: `config_path.write_text("# old config\n")` and line 153:
  `backup_path.read_text()` both omit the encoding argument.
  **Fix:** Add `encoding="utf-8"` to both calls.

- [x] **[QUALITY] `tests/test_bug_reproducers.py:42,203`: two `read_text()` calls without `encoding="utf-8"`**
  Line 42 reads `plasma-org…appletsrc` with `errors="replace"` but no encoding.
  Line 203 reads `manifest.json` without any encoding argument.
  **Fix:** Add `encoding="utf-8"` to both `read_text()` calls.

### Deep Audit Findings (2026-04-29, Round 3)

#### Crash-Risk Bugs

- [x] **[BUG] `scripts/icon_theme_gen.py`: missing `import sys` causes NameError when exceptions fire**
  Lines 424 and 443 both call `print(..., file=sys.stderr)` inside exception handlers that
  were added in a previous fix pass — but `sys` is never imported in this module (only
  `os`, `re`, `shutil`, `subprocess`, and `urllib.request` appear in the import block).
  Any fal-ai API failure or icon download failure will raise `NameError: name 'sys' is not
  defined` on top of the original error, hiding the real cause entirely.
  **Fix:** Add `import sys` to the import block.

#### Resource Leaks

- [x] **[BUG] `scripts/capture_theme_references.py:552`: `Image.open()` without context manager**
  ```python
  img = Image.open(image_path)
  cropped = img.crop((0, 0, 3840, 2160))
  resized = cropped.resize((1920, 1080), Image.Resampling.LANCZOS)
  resized.save(image_path)
  ```
  The PIL file handle is never explicitly closed.  If `crop()` or `resize()` raises, the
  handle leaks until the GC collects it — delaying file unlocks on Windows and making
  the code harder to reason about on all platforms.
  **Fix:** Wrap in a `with Image.open(image_path) as img:` context manager.

- [x] **[BUG] `scripts/generate_panel_svg.py:30`: `Image.open()` chained without context manager**
  ```python
  img = Image.open(mockup_path).convert("RGB")
  ```
  The chained `.convert()` call returns a new image object while the original
  `Image.open()` handle is never closed.  This leaks one file descriptor per call.
  **Fix:** Use a `with` block:
  ```python
  with Image.open(mockup_path) as raw:
      img = raw.convert("RGB")
  ```

- [x] **[QUALITY] `scripts/materializers/wallpaper.py:95-96,136`: two `Popen` calls missing `stdin=subprocess.DEVNULL`**
  Both daemon-launch calls specify `stdout` and `stderr` as `DEVNULL` but omit `stdin`.
  The spawned daemons inherit the parent's stdin; if they attempt to read from it they
  will block or consume input intended for the parent process.
  **Fix:** Add `stdin=subprocess.DEVNULL` to both `Popen` calls.

#### Missing `encoding=` Arguments

- [x] **[QUALITY] `scripts/materializers/wallpaper.py:20,56`: two `read_text(errors=…)` calls without `encoding="utf-8"`**
  Line 20: `appletsrc.read_text(errors="replace")` and line 56:
  `fehbg.read_text(errors="replace")` both specify `errors` but omit `encoding`.
  On non-UTF-8 locales the system default codec is used, corrupting non-ASCII paths.
  **Fix:** Change both to `read_text(encoding="utf-8", errors="replace")`.

- [x] **[QUALITY] `workflow/nodes/install/resolver.py:39`: `read_text(errors=…)` without `encoding="utf-8"`**
  `Path("/etc/os-release").read_text(errors="replace")` omits `encoding`.  `/etc/os-release`
  is defined to be UTF-8 by the systemd spec; omitting the argument relies on the locale.
  **Fix:** Add `encoding="utf-8"`.

- [x] **[QUALITY] `workflow/nodes/audit/detectors.py:56,127,142,154`: four `read_text(errors=…)` calls without `encoding="utf-8"`**
  Four separate `read_text(errors="replace")` calls — at line 56 (`/sys/class/dmi/id/chassis_type`),
  line 127 (`hyprpaper.conf`), line 142 (`~/.fehbg`), and line 154 (`nitrogen bg-saved.cfg`) —
  all omit `encoding`.  Paths with non-ASCII characters in wallpaper configs will be
  decoded incorrectly on non-UTF-8 locales.
  **Fix:** Add `encoding="utf-8"` to all four calls.

- [x] **[QUALITY] `workflow/nodes/implement/verify.py:34`: `read_text(errors=…)` without `encoding="utf-8"`**
  `Path(written).read_text(errors="replace")` in the palette-match loop omits encoding.
  Config files written by the materializers always use UTF-8; mismatched decoding
  means color hex strings may not be found in the decoded text.
  **Fix:** Add `encoding="utf-8"`.

- [x] **[QUALITY] `workflow/nodes/implement/score.py:74`: `read_text(errors=…)` without `encoding="utf-8"`**
  `p.read_text(errors="replace")` in `_is_syntactically_valid()` omits encoding.
  **Fix:** Add `encoding="utf-8"`.

- [x] **[QUALITY] `workflow/nodes/cleanup/reloader.py:16`: `read_text(errors=…)` without `encoding="utf-8"`**
  `path.read_text(errors="replace")` in `validate_file()` omits encoding.
  **Fix:** Add `encoding="utf-8"`.

- [x] **[QUALITY] `workflow/session.py:90`: `md.open("a")` without `encoding="utf-8"`**
  In `append_item()`, the append-mode `open()` call at line 90 omits `encoding`.
  All other writes in this file correctly specify `encoding="utf-8"` — this one is
  inconsistent and will use the system locale on the append path.
  **Fix:** Change to `md.open("a", encoding="utf-8")`.

#### Robustness

- [x] **[QUALITY] `workflow/nodes/install/resolver.py:148-154`: four `subprocess.run()` calls without `timeout=`**
  The package-verification loop checks whether each required package is installed via
  `pacman -Q`, `dpkg -s`, or `rpm -q`.  None of these four calls passes `timeout=`,
  so a hung package manager (e.g. a locked dpkg database) will block the entire
  install node indefinitely.
  **Fix:** Add `timeout=30` to each call.

#### Test Quality

- [x] **[QUALITY] `tests/test_kde_lockscreen_materializer.py:170,182`: `write_text()`/`read_text()` without `encoding="utf-8"` (re-open — not applied in previous round)**
  Previous fix attempt targeted incorrect line numbers (before `import shutil` shifted
  the file).  The calls at current lines 170 and 182 still lack `encoding="utf-8"`.
  **Fix:** Add `encoding="utf-8"` to both calls.

- [x] **[QUALITY] `tests/test_starship_materializer.py:145,154`: `write_text()`/`read_text()` without `encoding="utf-8"` (re-open — not applied in previous round)**
  Same root cause as above — line numbers shifted after `import shutil` insertion; the
  encoding arguments were never written to the file.
  **Fix:** Add `encoding="utf-8"` to both calls.

- [x] **[QUALITY] `tests/test_implement_spec.py:21-22`: class-level `_FakeLLM` state shared across tests**
  `_FakeLLM.requested_schema` and `_FakeLLM.structured_response` are class-level
  variables mutated directly by each test method (e.g. lines 38, 45, 58).  Tests run
  in alphabetical order by default, so the class variables carry over from one test to
  the next.  A failing early test can leave stale state that masks failures in later ones.
  **Fix:** Add a `setUp()` method to `ImplementSpecTests` that resets both class
  variables to `None` before each test.

---

### Round 4 — 2026-04-29

#### Atomic File Operations

- [x] **[BUG] `workflow/nodes/refine.py:159-162`: non-atomic write of `design.json`**
  `_write_design_json` calls `path.write_text(...)` directly.  A crash mid-write
  leaves a truncated `design.json`, breaking the entire refine→plan→baseline→install
  pipeline on resume.
  **Fix:** Write to a `NamedTemporaryFile` in the same directory, then
  `Path(tmp.name).replace(path)`.

- [x] **[BUG] `workflow/nodes/plan.py:56-57`: non-atomic write of `plan.html`**
  `html_path.write_text(html_content, encoding="utf-8")` writes directly.  A
  crash during the LLM-generated HTML write leaves a partial file; the
  `html_path.stat().st_size < 500` gate may then pass or fail spuriously.
  **Fix:** Same temp-file-then-rename pattern.

- [x] **[BUG] `workflow/nodes/handoff.py:69-70`: non-atomic writes of `handoff.md` / `handoff.html`**
  Both final session documents are written directly.  A crash after `md_path`
  but before `html_path` leaves the session half-documented.
  **Fix:** Atomic write pattern for both files.

#### LLM Response Robustness

- [x] **[BUG] `workflow/nodes/explore.py:69`: `response.content` accessed without None guard**
  `if DIRECTION_SENTINEL in response.content:` raises `TypeError` when the LLM
  returns `content=None` (e.g. on API error or finish_reason).
  **Fix:** Change to `if response.content and DIRECTION_SENTINEL in response.content:`.

- [x] **[BUG] `workflow/nodes/plan.py:55`: `response.content` passed to `_extract_html()` without None guard**
  `_extract_html(response.content)` calls `.strip()` on the first line, which raises
  `AttributeError: 'NoneType' object has no attribute 'strip'` when content is None.
  **Fix:** Change to `_extract_html(response.content or "")`.

- [x] **[BUG] `workflow/nodes/refine.py:100`: `response.content` accessed without None guard**
  `if DESIGN_SENTINEL in response.content:` raises `TypeError` on None content.
  **Fix:** Change to `if response.content and DESIGN_SENTINEL in response.content:`.

#### Encoding

- [x] **[QUALITY] `tests/test_palette_extractor.py:248`: `write_text()` without `encoding="utf-8"`**
  `(sub / "index.theme").write_text(f"[Icon Theme]\\nName={name}\\n")` in
  `_fake_dir()` fixture helper lacks explicit encoding.
  **Fix:** Add `encoding="utf-8"`.

- [x] **[QUALITY] `tests/test_kde_materializers.py:258,521`: two `read_text()` calls without `encoding="utf-8"`**
  `_run_real()` at line 258 and the list comprehension at line 521 both call
  `read_text()` without encoding, risking `UnicodeDecodeError` on non-UTF-8 locales.
  **Fix:** Add `encoding="utf-8"` to both.

- [x] **[QUALITY] `tests/test_starship_materializer.py:120`: `read_text()` without `encoding="utf-8"`**
  `content = config_path.read_text()` in `test_writes_toml_file` lacks explicit
  encoding.  **Fix:** Add `encoding="utf-8"`.

#### Test Quality

- [x] **[QUALITY] `tests/test_kde_materializers.py:263,265`: non-idiomatic `assertFalse`/`assertTrue` on `re.findall` results**
  `assertFalse(re.findall(...))` and `assertTrue(re.findall(...))` are less
  descriptive than `assertEqual(..., [])` / `assertNotEqual(..., [])`.
  **Fix:** Replace with assertEqual/assertNotEqual.

- [x] **[QUALITY] `tests/test_cleanup_reloader.py:22,31,41,51`: bare `errors` list as assertion message**
  Four calls use `self.assertTrue(any("app" in e for e in errors), errors)` where
  the second argument is the raw list object.  When an assertion fails, the message
  shows an unhelpful `repr(list)`.
  **Fix:** Wrap with `f"Expected 'app' error, got: {errors}"`.

---

### Round 5 — 2026-04-29

#### Resource Leaks — Subprocess stdin

- [x] **[BUG] `scripts/capture_theme_references.py:249`: `restart_plasmashell` Popen missing `stdin=DEVNULL`**
  `subprocess.Popen(["plasmashell", "--replace"], stdout=DEVNULL, stderr=DEVNULL)` does
  not redirect stdin.  The daemon inherits the parent process's stdin, which can block
  on terminal reads or consume interactive input.
  **Fix:** Add `stdin=subprocess.DEVNULL`.

- [x] **[BUG] `scripts/capture_theme_references.py:523`: `launch_reference_window` Popen missing `stdin=DEVNULL`**
  `subprocess.Popen(build_reference_window_command(...), stdout=DEVNULL, stderr=DEVNULL)`
  also inherits stdin from the parent.
  **Fix:** Add `stdin=subprocess.DEVNULL`.

#### Encoding

- [x] **[BUG] `scripts/deterministic_ricing_session.py:316`: `read_text(errors="replace")` without `encoding="utf-8"`**
  `appletsrc.read_text(errors="replace")` in `_get_wallpaper_from_appletsrc()` (or
  equivalent) uses the platform default encoding, so non-ASCII wallpaper paths will be
  mis-decoded on non-UTF-8 locales.
  **Fix:** Change to `read_text(encoding="utf-8", errors="replace")`.

#### Code Quality — Imports

- [x] **[QUALITY] `workflow/nodes/plan.py:125`: `import sys` inside function body**
  The `_extract_html()` function imports `sys` inline at the point of use.  All other
  imports in this file are at module level; the inline import is inconsistent and adds
  a small per-call overhead.
  **Fix:** Move `import sys` to the module-level imports block.

#### LLM Response Robustness

- [x] **[BUG] `workflow/nodes/explore.py:83`: `response.content` passed to `interrupt()` without None guard**
  When the LLM returns `content=None` (API error, finish_reason, etc.) the dict
  `{"message": response.content}` passes `None` to `interrupt()`, which attempts to
  serialize it.  This can raise a `TypeError` inside LangGraph's serializer.
  **Fix:** Change to `"message": response.content or ""`.

#### Atomic Write Safety — Temp-file Leak on `replace()` failure

- [x] **[BUG] `workflow/nodes/refine.py:169`: tmp file leaks if `Path.replace()` raises**
  After the `NamedTemporaryFile` context manager exits, `Path(tmp_path).replace(path)`
  is called bare.  If it raises (e.g. permission error, cross-device link), the `.tmp`
  file is left on disk permanently.
  **Fix:** Wrap the `replace()` in try/except; call `Path(tmp_path).unlink(missing_ok=True)` in the except branch before re-raising.

- [x] **[BUG] `workflow/nodes/plan.py:62`: tmp file leaks if `Path.replace()` raises**
  Same pattern as `refine.py` — `plan.html`'s temp file is not cleaned up on error.
  **Fix:** Same try/except+unlink pattern.

- [x] **[BUG] `workflow/nodes/handoff.py:76`: tmp files leak if `Path.replace()` raises in loop**
  The loop over `(md_path, html_path)` calls `replace()` unguarded.  A failure on the
  second file leaves that file's `.tmp` on disk; a failure on the first leaves the
  session half-written with no cleanup.
  **Fix:** Wrap each `replace()` in try/except+unlink inside the loop.

#### Error Handling

- [x] **[QUALITY] `workflow/run.py:89`: exception handler prints message but not traceback**
  `except Exception as e: print(f"\n[ERROR] {e}")` only prints the exception message.
  For unexpected runtime errors the full traceback is lost, making post-mortem
  debugging very difficult.
  **Fix:** Add `import traceback; traceback.print_exc(file=sys.stderr)` before the
  `raise`.


---

### Deep Audit Findings (Round 4)

#### Missing `timeout=` Arguments in `subprocess.run`

- [x] **[QUALITY] `workflow/nodes/cleanup/reloader.py:43,47,56,65,74,78,87,91`: eight `subprocess.run()` calls without `timeout=`**
  `reload_waybar`, `reload_polybar`, `reload_dunst`, `reload_mako`, and `reload_swaync` all invoke `subprocess.run(["pkill", ...])` and `subprocess.run(["makoctl", ...])` / `subprocess.run(["swaync-client", ...])` without a `timeout=` argument. A hung `pkill` (e.g. stale dbus lock), an unresponsive `makoctl`, or a blocked `swaync-client` will stall the cleanup node indefinitely with no way to recover.
  **Fix:** Add `timeout=5` to all eight calls (5 s is more than enough for signal delivery and daemon reloads).
  **Done:** Added `timeout=5` to all eight `subprocess.run()` calls across `reload_waybar`, `reload_polybar`, `reload_dunst`, `reload_mako`, and `reload_swaync`. All 5 `ReloadErrorPropagationTests` pass.

#### Non-Idiomatic Test Assertions

- [x] **[QUALITY] `tests/test_kde_materializers.py:478`: `assertFalse([list])` is non-idiomatic and fragile**
  `self.assertFalse([c for c in calls if "kwriteconfig6" in c])` in `TestMaterializePlasmaTheme.test_dry_run_returns_single_change` checks that the filtered list is falsy (empty) — the same anti-pattern that was fixed at lines 432 and 436 in a previous round but missed here.
  **Fix:** Replace with `self.assertEqual([c for c in calls if "kwriteconfig6" in c], [])`.
  **Done:** Changed `assertFalse([...])` → `assertEqual([...], [])` at line 478. `TestMaterializePlasmaTheme.test_dry_run_returns_single_change` passes.

#### Missing `encoding=` Arguments

- [x] **[QUALITY] `tests/test_ricer_cli_routing.py:52,156`: two `NamedTemporaryFile(mode="w")` calls without `encoding="utf-8"`**
  Line 52: `tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)` writes a JSON design file for CLI tests.
  Line 156: `tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)` writes a YAML design file.
  Neither specifies `encoding="utf-8"`. Although the content is ASCII-only today, the omission is inconsistent with the rest of the test suite and would silently mis-encode any future non-ASCII theme names on non-UTF-8 locales.
  **Fix:** Add `encoding="utf-8"` to both `NamedTemporaryFile` calls.
  **Done:** Added `encoding="utf-8"` to both calls at lines 52 and 156. All 9 `RicerCliRoutingTests` + `DesignFileLoaderTests` pass.

---

### Round 6 -- 2026-04-29

#### Missing encoding= Arguments

- [x] **[QUALITY] scripts/core/snapshots.py:81: appletsrc.read_text(errors="replace") without encoding="utf-8"**
  appletsrc.read_text(errors="replace") in snapshot_kde_state() omits the encoding
  argument while already specifying errors="replace". The appletsrc file contains
  wallpaper paths and plugin names that may include non-ASCII characters; on non-UTF-8
  locales the system codec is used, corrupting the snapshot data.
  **Fix:** Change to appletsrc.read_text(encoding="utf-8", errors="replace").

- [x] **[QUALITY] scripts/core/snapshots.py:104: konsolerc.read_text(errors="replace") without encoding="utf-8"**
  konsolerc.read_text(errors="replace") in snapshot_konsole_state() has the same
  issue -- encoding omitted while errors are handled.
  **Fix:** Change to konsolerc.read_text(encoding="utf-8", errors="replace").

- [x] **[QUALITY] scripts/session_manager.py:193: write_text(header) without encoding="utf-8" in cmd_init**
  session_md(session_dir).write_text(header) writes the session header (which contains
  the theme name and timestamps) without specifying encoding. Theme names may contain
  non-ASCII characters.
  **Fix:** Change to write_text(header, encoding="utf-8").

- [x] **[QUALITY] scripts/session_manager.py:228: md.read_text() without encoding="utf-8" in cmd_resume_check**
  text = md.read_text() reads session metadata without encoding.
  **Fix:** Change to md.read_text(encoding="utf-8").

- [x] **[QUALITY] scripts/session_manager.py:379: session_md().read_text() without encoding="utf-8" in cmd_status**
  text = session_md(session_dir).read_text() omits encoding.
  **Fix:** Change to session_md(session_dir).read_text(encoding="utf-8").

- [x] **[QUALITY] scripts/session_manager.py:386: session_md().read_text() without encoding="utf-8" in cmd_read**
  print(session_md(session_dir).read_text()) omits encoding.
  **Fix:** Change to print(session_md(session_dir).read_text(encoding="utf-8")).

#### LLM Response Robustness

- [x] **[BUG] workflow/nodes/refine.py:119: response.content passed to interrupt() without None guard**
  "message": response.content inside the interrupt() call passes None to
  LangGraph's serializer when the LLM returns content=None (e.g. on API error or
  finish_reason="stop" with no body), raising TypeError inside the serializer.
  The sibling guard on line 101 already handles the sentinel-check case; this one
  covers the fallback path.
  **Fix:** Change to "message": response.content or "".

---

### Rollback / Undo Hardening Backlog -- 2026-04-30

#### Non-File State Not Fully Restored

- [x] **[BUG] `materializers/system.py` + `ricer_undo.py`: GTK `gsettings` values are not restored**
  `materialize_gtk()` writes `org.gnome.desktop.interface` keys (`gtk-theme`,
  `icon-theme`, `cursor-theme`) and records the new values, but it does not
  snapshot the previous values. `undo()` therefore cannot restore the pre-apply
  GTK desktop state.
  **Done:** `materialize_gtk` calls `gsettings_get` for all three keys before applying
  and records `previous_value` per change record. `_undo_gsettings` is registered as
  the `gtk` undo handler and restores each key. Legacy manifest handling included.

- [x] **[BUG] `materializers/gnome.py` + `ricer_undo.py`: GNOME Shell `gsettings` values are not restored**
  `materialize_gnome_shell()` sets `org.gnome.desktop.interface color-scheme`,
  but only records the new value. Undo cannot return GNOME's color-scheme
  preference to the prior state.
  **Done:** `materialize_gnome_shell` snapshots `color-scheme` via `gsettings_get`
  and stores `previous_value`. `_undo_gsettings` (registered for `gnome_shell`)
  restores it on undo.

- [x] **[BUG] `materializers/gnome.py` + `ricer_undo.py`: GNOME lockscreen `gsettings` values are not restored**
  `materialize_gnome_lockscreen()` sets `org.gnome.desktop.screensaver`
  `primary-color`, `secondary-color`, and `color-shading-type`, but records only
  the new values. Undo leaves those persistent settings behind.
  **Done:** All three screensaver keys are snapshotted via `gsettings_get` before
  apply. `_undo_gsettings` (registered for `gnome_lockscreen`) restores all three.

- [x] **[BUG] `materializers/system.py`: Flatpak GTK/icon overrides are persistent and not undone**
  `materialize_gtk()` may run `flatpak override --user --filesystem ...` for GTK
  config and icon directories. These user overrides persist after undo, and the
  manifest currently records only success/new target state.
  **Done:** See "Recommended Next Tasks" entry above.

#### KDE / Plasma State Gaps

- [x] **[BUG] `materializers/kde_extras.py`: Look-and-Feel (`lnf`) has no undo handler**
  `materialize_lnf()` records `previous_lnf`, `lnf_id`, and `lnf_path`, but
  `_APP_UNDO_HANDLERS` does not include `lnf`. Undo does not reapply the previous
  global theme and leaves the generated package selected or present.
  **Done:** See "Recommended Next Tasks" entry above.

- [ ] **[QUALITY] `materializers/kde_extras.py`: generated icon/LnF/Kvantum assets are not cleaned up on undo**
  Undo restores config pointers for many KDE layers, but generated directories
  such as palette icon themes, FAL icon assets, Look-and-Feel packages, and
  generated Kvantum themes can remain in `~/.local/share` after rollback.
  **Fix:** Record generated directories with a `generated_path` / `generated_paths`
  field. Add safe undo cleanup that deletes only paths under known safe prefixes
  and with Hermes/generated names.

- [ ] **[BUG] `materializers/kde_extras.py`: Papirus folder color changes are not restored**
  `materialize_icon_theme()` can call `papirus-folders`, but the manifest records
  only the new color and success. Undo does not restore the previous Papirus folder
  color state.
  **Fix:** Snapshot the previous Papirus folder color if possible. If the tool does
  not expose reliable readback, mark the action as best-effort/non-reversible in
  the manifest and undo simulation output.

#### Generic File / Injection Cleanup Gaps

- [ ] **[BUG] `ricer_undo.py`: injection-only files created by Hermes can be left empty after undo**
  `_undo_injections()` removes the marker line and following directive, but if
  Hermes created the host file solely for that include/import, undo may leave an
  empty config file behind. Likely affected: `waybar/style.css`, `eww/eww.scss`,
  `eww/eww.yuck`, and similar injection host files.
  **Fix:** Injection change records should include `backup` and/or `created: True`.
  After removing the injected block, delete the file if it becomes empty and was
  created by Hermes.

- [ ] **[QUALITY] `ricer_undo.py`: older manifests cannot restore newly tracked state**
  Manifests created before rollback fixes will not contain GTK CSS entries,
  `backup: None` records, previous `gsettings` values, Flatpak snapshots, or
  generated asset paths. Undo can only restore what the manifest recorded.
  **Fix:** Improve `simulate-undo`/undo reporting to call out missing legacy fields
  and recommend manual cleanup for known legacy gaps.

#### Runtime Reload / Live State Gaps

- [ ] **[QUALITY] `ricer_undo.py`: restored configs are not always live-reloaded after undo**
  Many materializers reload live state on apply (`qdbus6 KWin reconfigure`,
  `pkill -SIGUSR2 waybar`, `pkill -HUP picom`, `eww reload`, `hyprctl keyword ...`),
  but generic file restoration does not consistently trigger matching reloads.
  **Fix:** Add post-restore reload hooks for Hyprland, Waybar, Picom, EWW, and
  other runtime-managed apps, or record explicit previous runtime values where the
  config file alone is insufficient.

- [x] **[BUG] `materializers/hyprland.py`: live border keywords are not explicitly reverted by undo**
  `materialize_hyprland()` applies border colors via `hyprctl keyword` immediately
  and also patches `hyprland.conf` when present. Generic undo restores the config,
  but it does not necessarily reset the live Hyprland keywords immediately.
  **Done:** `_hyprctl_getoption_gradient` snapshots both border options via
  `hyprctl getoption` before apply. `previous_active_border` /
  `previous_inactive_border` are stored in the manifest. `_undo_hyprland` reissues
  `hyprctl keyword` with the previous values. Legacy manifests (no previous values)
  are skipped gracefully with a note that the config-file restore still applies.
  Tests: `HyprlandGeoptionSnapshotTests` (2 materializer tests),
  `TestUndoHyprland` (3 undo tests), `TestDescribeChangeNewHandlers` (2 describe tests).

#### Dry-Run / Simulation Parity

- [ ] **[QUALITY] Materializer dry-run output should list all files/actions that would be touched**
  Some dry-run records are less detailed than real apply records, especially for
  non-file state, generated directories, `gsettings`, Flatpak overrides, and LnF.
  This makes `--dry-run` and undo simulation less useful for risk review.
  **Fix:** Ensure dry-run emits one change-like record per planned file write,
  generated path, persistent setting, and external state mutation, without writing
  anything.
