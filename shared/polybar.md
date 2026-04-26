# Polybar Theming

Polybar reads a monolithic INI config (`~/.config/polybar/config.ini` or `~/.config/polybar/config`). The ricer writes a **separate colors fragment** and injects an `include-file` line rather than rewriting the whole config.

---

## How ricer.py Applies the Theme

1. Writes `~/.config/polybar/hermes-colors.ini` from `templates/polybar/hermes-colors.ini.template`
2. Injects `include-file = ~/.config/polybar/hermes-colors.ini` at the top of the `[colors]` section in the main config (if not already present)
3. Reloads polybar: `pkill polybar && sleep 0.5 && polybar &` (or the user's launch script)

**Template variables used:**

| Variable | Role |
|----------|------|
| `{{name}}` | Theme name — written as a comment header |
| `{{background}}` | Bar background |
| `{{foreground}}` | Default text color |
| `{{primary}}` | Active workspace, highlight |
| `{{secondary}}` | Secondary accent |
| `{{accent}}` | Indicators, icons |
| `{{surface}}` | Module backgrounds |
| `{{muted}}` | Inactive/dimmed text |
| `{{danger}}` | Alerts, battery low |
| `{{success}}` | OK indicators |
| `{{warning}}` | Warnings |

---

## Using Colors in Modules

Reference the colors via `${colors.<slot>}` in your polybar config:

```ini
[bar/main]
background = ${colors.background}
foreground = ${colors.foreground}

[module/workspaces]
label-active-background = ${colors.primary}
label-occupied-foreground = ${colors.muted}
label-urgent-background = ${colors.danger}
```

---

## Include Injection vs Full Rewrite

The include approach works when the main config uses `${colors.*}` references. If your config has hardcoded hex values inline, the include won't override them — do a full config rewrite instead (load `shared/design-system.md` for the palette values, rewrite manually).

**Detection:** `grep -c '#[0-9a-fA-F]\{6\}' ~/.config/polybar/config.ini` — if high (>20), likely hardcoded.

---

## Reload After Apply

```bash
# Standard reload (kills all bars, restarts):
pkill polybar && sleep 0.3 && ~/.config/polybar/launch.sh

# Or if no launch script:
polybar main &
```

Polybar doesn't hot-reload config — a full restart is required after any color change.

---

## Pitfalls

- **`include-file` ordering matters.** It must appear before any `${colors.*}` reference in the same section. The ricer injects it at the top of `[colors]`.
- **Multiple bars:** if the config defines `[bar/main]` and `[bar/secondary]`, both share the same `[colors]` block. The include covers both.
- **i3 module labels:** use `%{F{{primary}}}` polybar format codes for inline color — these need the hex value directly, not `${colors.primary}`. The ricer writes them from the design_system palette.
