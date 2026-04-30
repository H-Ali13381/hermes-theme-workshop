# Audit Report — 2026-04-29

Systematic audit of dead code, redundant logic, resource management issues, and
non-idiomatic patterns across the full codebase. Findings follow the `[TAG]`
style from `dev/TODO.md`.

---

## [BUG] Missing `encoding="utf-8"` on `text=True` subprocess calls

`text=True` decodes subprocess output with the **system locale** encoding
(e.g. `LANG=C` ⇒ ASCII).  On those locales a non-ASCII path or error message
from any KDE tool will raise `UnicodeDecodeError` at runtime.

### `scripts/core/process.py:9` — central `run_cmd` helper

Every materializer funnels subprocess calls through `run_cmd`.  Fixing it here
fixes every caller simultaneously.

```
- result = subprocess.run(
-     cmd, capture_output=True, text=True, timeout=timeout
- )
+ result = subprocess.run(
+     cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout
+ )
```

### `workflow/nodes/baseline.py:28` — baseline capture

```
- result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
+ result = subprocess.run(cmd, capture_output=True, text=True,
+                         encoding="utf-8", timeout=30)
```

### `workflow/nodes/cleanup/reloader.py:101` — hyprctl reload

```
- r = subprocess.run(["hyprctl", "reload"], capture_output=True, text=True, timeout=10)
+ r = subprocess.run(["hyprctl", "reload"], capture_output=True, text=True,
+                    encoding="utf-8", timeout=10)
```

---

## [QUALITY] Visually ambiguous variable name `l` in `adjust_lightness`

**File:** `scripts/core/colors.py:82-83`

The single-letter variable `l` (lowercase L) is indistinguishable from `1`
(digit one) in most terminal and editor fonts.

```python
# Before
h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
l = max(0.0, min(1.0, l * factor))
nr, ng, nb = colorsys.hls_to_rgb(h, l, s)

# After
h, lightness, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
lightness = max(0.0, min(1.0, lightness * factor))
nr, ng, nb = colorsys.hls_to_rgb(h, lightness, s)
```

---

## [QUALITY] Redundant f-string prefix on plain string literals

**File:** `scripts/generate_panel_svg.py:61-62`

Both values are plain string literals with no `{...}` interpolation; the `f`
prefix is misleading noise.

```python
# Before (inside the `else` branch of generate_svg)
center_fill = f"url(#grad-center)"
edge_fill   = f"url(#grad-center)"

# After
center_fill = "url(#grad-center)"
edge_fill   = "url(#grad-center)"
```

---

## [QUALITY] Non-idiomatic `assertTrue(any(...))` in test assertions

**File:** `tests/test_cleanup_reloader.py:22, 31, 41, 51`

The generator expression inside `assertTrue` is syntactically valid but obscures
intent.  Extracting the matching errors list makes the assertion purpose
self-documenting and produces the same failure message on failure.

```python
# Before (pattern repeated four times for waybar / dunst / mako / swaync)
self.assertTrue(any("waybar" in e for e in errors),
                f"Expected 'waybar' error, got: {errors}")

# After
matching = [e for e in errors if "waybar" in e]
self.assertTrue(matching, f"Expected 'waybar' error, got: {errors}")
```

---

## Summary table

| # | Tag | File | Lines | Fix |
|---|-----|------|-------|-----|
| 1 | BUG | `scripts/core/process.py` | 9 | Add `encoding="utf-8"` to `run_cmd` |
| 2 | BUG | `workflow/nodes/baseline.py` | 28 | Add `encoding="utf-8"` to `subprocess.run` |
| 3 | BUG | `workflow/nodes/cleanup/reloader.py` | 101 | Add `encoding="utf-8"` to `subprocess.run` |
| 4 | QUALITY | `scripts/core/colors.py` | 82–83 | Rename `l` → `lightness` |
| 5 | QUALITY | `scripts/generate_panel_svg.py` | 61–62 | Drop redundant `f` prefix |
| 6 | QUALITY | `tests/test_cleanup_reloader.py` | 22, 31, 41, 51 | Extract matching list before `assertTrue` |

Items 1–3 are the only runtime risks; 4–6 are readability improvements with no
behavioural change.

---

## Deep-Dive Findings — Round 2

The following were found by auditing all remaining files in
`scripts/materializers/`, `scripts/core/`, `workflow/nodes/`, and `tests/`
after the initial report above.

### Confirmed clean

| Area | Verdict |
|------|---------|
| `Image.open()` resource management | ✅ All 4 call sites use `with Image.open(...) as` |
| `jinja2.Environment` `StrictUndefined` | ✅ Both environments (`core/templates.py:30`, `materializers/terminals.py:182`) enforce it |

---

## [BUG] Additional `text=True` subprocess calls missing `encoding="utf-8"`

The same locale-encoding bug documented in items 1–3 above exists in six more
helper modules.  Each one is a private `run` / `run_cmd` wrapper that every
caller in its module inherits.

### `scripts/session_helpers.py:49` — phases 0-3 of deterministic ricing

```python
- result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
+ result = subprocess.run(cmd, capture_output=True, text=True,
+                         encoding="utf-8", timeout=timeout)
```

### `scripts/capture_helpers.py:31` — KDE capture pipeline

```python
- result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
+ result = subprocess.run(cmd, capture_output=True, text=True,
+                         encoding="utf-8", timeout=timeout)
```

### `scripts/session_manager.py:83-85` — workflow session listing

```python
- result = subprocess.run(
-     [sys.executable, str(WORKFLOW_RUN_PY), "--list", "--json"],
-     capture_output=True, text=True, timeout=15,
- )
+ result = subprocess.run(
+     [sys.executable, str(WORKFLOW_RUN_PY), "--list", "--json"],
+     capture_output=True, text=True, encoding="utf-8", timeout=15,
+ )
```

### `scripts/desktop_utils.py:41-43` — `discover_desktop()` parses `ps aux`

Called on startup by every materializer path via `ricer.py`.

```python
- result = subprocess.run(
-     ["ps", "aux"], capture_output=True, text=True, timeout=3
- )
+ result = subprocess.run(
+     ["ps", "aux"], capture_output=True, text=True,
+     encoding="utf-8", timeout=3
+ )
```

### `workflow/nodes/audit/detectors.py:27` — WM/GPU/screen detection

```python
- r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
+ r = subprocess.run(cmd, capture_output=True, text=True,
+                    encoding="utf-8", timeout=timeout)
```

### `workflow/nodes/install/resolver.py:97-101, 106-109, 120-123` — package install

Three call sites in `_sudo_run()` and `_try_arch()`.  Because `input=` is also
used (sudo password piped via stdin), a locale mismatch could corrupt the
password handshake on systems where `sudo` emits a non-ASCII prompt.

```python
# _sudo_run — password path (lines 97-101)
- r = subprocess.run(
-     ["sudo", "-S", "-p", "", "-k"] + cmd,
-     input=sudo_password + "\n",
-     capture_output=True, text=True, timeout=300,
- )
+ r = subprocess.run(
+     ["sudo", "-S", "-p", "", "-k"] + cmd,
+     input=sudo_password + "\n",
+     capture_output=True, text=True, encoding="utf-8", timeout=300,
+ )

# _sudo_run — no-password path (lines 106-109)  and  _try_arch yay (lines 120-123):
# same pattern — add encoding="utf-8" to each call.
```

---

## [BUG] `subprocess.Popen` missing `stdin=subprocess.DEVNULL`

**File:** `scripts/ricer_undo.py:233-234`

When `hyprpaper` is restarted during undo it inherits the parent process's
stdin (a terminal in interactive use).  If `hyprpaper` blocks reading stdin the
`ricer undo` command hangs.  The matching spawn in `materializers/wallpaper.py`
already sets all three stdio redirects; the undo path should match.

```python
# Before
subprocess.Popen(["hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                 start_new_session=True)

# After
subprocess.Popen(["hyprpaper"], stdin=subprocess.DEVNULL,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                 start_new_session=True)
```

---

## [QUALITY] Additional redundant f-string prefixes

The grep revealed nine more call sites where an f-string carries no `{…}`
expression.

### `scripts/desktop_state_audit.py:76, 173`

```python
# Line 76
- print(f"=== HERMES-RICER DESKTOP STATE AUDIT ===")
+ print("=== HERMES-RICER DESKTOP STATE AUDIT ===")

# Line 173
- print(f"=== AUDIT COMPLETE ===")
+ print("=== AUDIT COMPLETE ===")
```

### `scripts/icon_theme_gen.py:140, 142, 211, 213`

These are adjacent lines in two nearly-identical `index.theme` builders (one
per code path).  Only the lines **without** `{…}` expressions need the `f`
removed.

```python
# Lines 139-146 (first builder) — remove f on lines 140 and 142
  content = (
-     f"[Icon Theme]\n"
+     "[Icon Theme]\n"
      f"Name={display_name}\n"
-     f"Comment=Palette-matched icon theme generated by linux-ricing\n"
+     "Comment=Palette-matched icon theme generated by linux-ricing\n"
      f"Inherits={inherits}\n"
      ...
  )
# Lines 210-217 (second builder) — same fix for lines 211 and 213
```

### `scripts/generate_panel_svg.py:282-285`

```python
# In the __main__ block — none of these contain {…}
- print(f"  plasma-apply-desktoptheme void-dragon")
- print(f"  qdbus6 org.kde.KWin /KWin reconfigure")
- print(f"\nTo undo:")
- print(f"  plasma-apply-desktoptheme default")
+ print("  plasma-apply-desktoptheme void-dragon")
+ print("  qdbus6 org.kde.KWin /KWin reconfigure")
+ print("\nTo undo:")
+ print("  plasma-apply-desktoptheme default")
```

### `workflow/run.py:75, 115`

```python
# Line 75
- print(f"  Linux Ricing Session")
+ print("  Linux Ricing Session")

# Line 115
- print(f"  Rollback: ricer undo")
+ print("  Rollback: ricer undo")
```

---

## [QUALITY] Dead sub-expression in test assertion

**File:** `tests/test_kde_undo.py:72`

`"" in c` evaluates to `True` for **every** string `c` (the empty string is
always a substring), so the entire condition collapses to `"--delete" not in c`.
The `"" in c` arm is dead code that misleads readers into thinking it guards
something.

```python
# Before — "in c" is always True; it does not filter anything
self.assertFalse([c for c in widget if "" in c and "--delete" not in c])

# After — express the actual intent
self.assertTrue(all("--delete" in c for c in widget),
                f"Expected every widgetStyle call to use --delete; got: {widget}")
```

---

## [QUALITY] Additional `assertTrue(any(...))` pattern

**File:** `tests/test_install_resolver.py:53`

Same readability concern as items already documented for `test_cleanup_reloader.py`.

```python
# Before
self.assertTrue(any("-n" in cmd for cmd in calls))

# After
matching = [cmd for cmd in calls if "-n" in cmd]
self.assertTrue(matching, f"Expected a sudo -n call; got calls: {calls}")
```

---

## Updated summary table

| # | Tag | File | Lines | Fix |
|---|-----|------|-------|-----|
| 1 | BUG | `scripts/core/process.py` | 9 | Add `encoding="utf-8"` to `run_cmd` |
| 2 | BUG | `workflow/nodes/baseline.py` | 28 | Add `encoding="utf-8"` |
| 3 | BUG | `workflow/nodes/cleanup/reloader.py` | 101 | Add `encoding="utf-8"` |
| 4 | BUG | `scripts/session_helpers.py` | 49 | Add `encoding="utf-8"` |
| 5 | BUG | `scripts/capture_helpers.py` | 31 | Add `encoding="utf-8"` |
| 6 | BUG | `scripts/session_manager.py` | 83 | Add `encoding="utf-8"` |
| 7 | BUG | `scripts/desktop_utils.py` | 41 | Add `encoding="utf-8"` |
| 8 | BUG | `workflow/nodes/audit/detectors.py` | 27 | Add `encoding="utf-8"` |
| 9 | BUG | `workflow/nodes/install/resolver.py` | 97, 106, 120 | Add `encoding="utf-8"` (3 sites) |
| 10 | BUG | `scripts/ricer_undo.py` | 233 | Add `stdin=subprocess.DEVNULL` |
| 11 | QUALITY | `scripts/core/colors.py` | 82–83 | Rename `l` → `lightness` |
| 12 | QUALITY | `scripts/generate_panel_svg.py` | 61–62, 282–285 | Drop redundant `f` prefix (6 sites) |
| 13 | QUALITY | `scripts/desktop_state_audit.py` | 76, 173 | Drop redundant `f` prefix |
| 14 | QUALITY | `scripts/icon_theme_gen.py` | 140, 142, 211, 213 | Drop redundant `f` prefix |
| 15 | QUALITY | `workflow/run.py` | 75, 115 | Drop redundant `f` prefix |
| 16 | QUALITY | `tests/test_kde_undo.py` | 72 | Remove dead `"" in c` sub-expression |
| 17 | QUALITY | `tests/test_cleanup_reloader.py` | 22, 31, 41, 51 | Extract list before `assertTrue` |
| 18 | QUALITY | `tests/test_install_resolver.py` | 53 | Extract list before `assertTrue` |

Items 1–10 are runtime risks.  Items 11–18 are readability improvements.
The highest-leverage single fix is item 1 (`core/process.py`) because
`run_cmd` is the central subprocess gateway; fixing it eliminates the locale
encoding hazard from every materializer simultaneously.
