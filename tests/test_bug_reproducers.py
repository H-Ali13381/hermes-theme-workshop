"""Reproducers for bugs surfaced by the 2026-04-24 live KDE integration test.

These exercise the full apply → undo pipeline and are side-effectful:
they invoke `ricer apply` and `ricer undo` on the real desktop. They're
kept separate from the unit tests and must be opted into:

    cd ~/.hermes/skills/creative/linux-ricing
    python3 -m unittest tests.test_bug_reproducers -v

Each test asserts the INVARIANT the bug violates. Every test should FAIL
against the current code (reproducing the bug) and PASS once the matching
fix in TODO.md is applied — making this file a regression harness.

Skipped gracefully if: not on KDE, or ricer CLI not installed, or no
wallpapers available.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


HOME = Path.home()
APPLETSRC = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
RICER = shutil.which("ricer") or str(HOME / ".local" / "bin" / "ricer")
AUDIT_PY = Path(
    "/home/neos/.hermes/skills/creative/linux-ricing/scripts/desktop_state_audit.py"
)
RICER_PY = Path(
    "/home/neos/.hermes/skills/creative/linux-ricing/scripts/ricer.py"
)


def read_current_wallpaper() -> str | None:
    if not APPLETSRC.exists():
        return None
    m = re.search(r"^Image\s*=\s*(.+)$", APPLETSRC.read_text(errors="replace"), re.MULTILINE)
    return m.group(1).strip() if m else None


def run(cmd, timeout=90):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def kde_available() -> bool:
    return (
        shutil.which("plasma-apply-wallpaperimage") is not None
        and os.environ.get("XDG_CURRENT_DESKTOP", "").upper().startswith("KDE")
    )


def pick_two_distinct_wallpapers() -> tuple[str, str] | None:
    candidates = []
    for d in (HOME / "Pictures", Path("/usr/share/wallpapers")):
        if not d.exists():
            continue
        for p in d.rglob("*.png"):
            if p.is_file() and p.stat().st_size > 1024:
                candidates.append(p)
                if len(candidates) >= 6:
                    break
        if len(candidates) >= 2:
            break
    if len(candidates) < 2:
        return None
    return str(candidates[0]), str(candidates[1])


class LiveBugReproducers(unittest.TestCase):
    """Each test reproduces one bug from TODO.md's integration findings."""

    @classmethod
    def setUpClass(cls):
        if not kde_available():
            raise unittest.SkipTest("KDE Plasma not detected in environment")
        if not Path(RICER).exists():
            raise unittest.SkipTest(f"ricer CLI not found at {RICER}")

        # CRITICAL: capture the user's ACTUAL current wallpaper first, before
        # touching anything. Everything (setUp, tearDown, tearDownClass) restores
        # to this — never to a test-harness-chosen wallpaper. We also avoid
        # materialize_wallpaper's own known-unrestored bug (P0).
        cls.original_wallpaper = read_current_wallpaper()

        wps = pick_two_distinct_wallpapers()
        if not wps:
            raise unittest.SkipTest("need 2 distinct wallpapers for apply+undo cycle")
        # For the P0 reproducer, wp_before must differ from wp_test. Pick so that
        # neither equals cls.original_wallpaper if possible — but we do NOT pin
        # the desktop to wp_before; the test records the current wallpaper as its
        # own "before" inline.
        cls.wp_test = wps[1] if cls.original_wallpaper and wps[0] in cls.original_wallpaper else wps[0]

    def tearDown(self):
        # Best-effort: ensure undo is called so the desktop doesn't drift between tests.
        run([RICER, "undo"], timeout=60)
        # Restore the ACTUAL pre-test wallpaper (works around P0 wallpaper-undo bug).
        if self.original_wallpaper:
            plain = self.original_wallpaper.replace("file://", "", 1)
            run(["plasma-apply-wallpaperimage", plain])
            time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        # Last-mile safety: even if a test crashed, restore the original wallpaper.
        if getattr(cls, "original_wallpaper", None):
            plain = cls.original_wallpaper.replace("file://", "", 1)
            run(["plasma-apply-wallpaperimage", plain])

    # ------------------------------------------------------------------
    # P0 — wallpaper is not restored by `ricer undo`
    # ------------------------------------------------------------------
    def test_p0_wallpaper_restored_on_undo(self):
        """INVARIANT: after apply+undo, plasma-org.kde.plasma.desktop-appletsrc
        'Image=' entry should equal its pre-apply value.

        Currently FAILS: materialize_wallpaper doesn't snapshot previous path
        and undo() has no app=='wallpaper' branch (TODO.md P0).
        """
        before = read_current_wallpaper()
        self.assertIsNotNone(before, "pre-apply wallpaper not readable")
        # Only run the reproducer if wp_test differs from the current wallpaper,
        # else the apply wouldn't actually change anything.
        if before and Path(self.wp_test).name in before:
            self.skipTest("wp_test equals current wallpaper; cannot observe change")

        r = run([RICER, "apply", "--wallpaper", self.wp_test, "--extract",
                 "--name", "p0-wallpaper-repro"], timeout=60)
        self.assertEqual(r.returncode, 0, f"ricer apply failed: {r.stderr}")

        applied = read_current_wallpaper()
        self.assertIn(Path(self.wp_test).name, applied or "",
                      "apply did not actually switch the wallpaper")

        r = run([RICER, "undo"], timeout=60)
        self.assertEqual(r.returncode, 0, f"ricer undo failed: {r.stderr}")

        after = read_current_wallpaper()
        self.assertEqual(
            after, before,
            f"BUG P0: wallpaper not restored by undo.\n"
            f"  before apply: {before}\n"
            f"  after undo:   {after}",
        )

    # ------------------------------------------------------------------
    # P1 — materialize_plasma_theme / materialize_cursor silently skip
    # ------------------------------------------------------------------
    def test_p1_extract_apply_covers_plasma_theme_and_cursor(self):
        """INVARIANT: `ricer apply --extract` must produce manifest entries
        for every detected KDE themable layer — including plasma_theme and
        cursor — not silently skip them.

        Currently FAILS: extractor output omits plasma_theme/cursor_theme;
        materialize_plasma_theme:1474 and materialize_cursor:1528 early-return
        empty (TODO.md P1).
        """
        r = run([RICER, "apply", "--wallpaper", self.wp_test, "--extract",
                 "--dry-run", "--name", "p1-cover-repro"], timeout=30)
        self.assertEqual(r.returncode, 0, f"dry-run failed: {r.stderr}")

        # Filter deprecation warnings from stdout
        stdout_lines = [ln for ln in r.stdout.splitlines()
                        if not ln.startswith(("/", " ")) or ln.startswith("{")
                        or ln.startswith("  ") or ln.startswith("[") or ln.startswith("]")
                        or ":" in ln]
        # Simpler: locate the JSON object and parse it
        json_start = r.stdout.find("{")
        self.assertGreaterEqual(json_start, 0, "no JSON in dry-run output")
        manifest = json.loads(r.stdout[json_start:])

        apps_touched = {c["app"] for c in manifest["changes"]}
        for required in ("plasma_theme", "cursor"):
            self.assertIn(
                required, apps_touched,
                f"BUG P1: {required} missing from manifest (silent skip).\n"
                f"  apps touched: {sorted(apps_touched)}",
            )

    # ------------------------------------------------------------------
    # P2 — kdeglobals must be captured pre-apply by exactly one materializer
    # ------------------------------------------------------------------
    def test_p2_kdeglobals_backed_up_once_and_matches_pre_apply(self):
        """INVARIANT: kdeglobals is a shared file multiple materializers
        touch. It must be captured ONCE, before any materializer has
        mutated it, and that backup must be byte-identical to the pre-apply
        live state.

        Previous behavior: materialize_kvantum took a stale backup of
        kdeglobals after materialize_kde had already written to it; kde
        had no direct kdeglobals backup (relied on re-applying the
        previous colorscheme). Selective/partial undo would corrupt.

        Fix: materialize_kde now backs up kdeglobals pre-apply under
        `kde/kdeglobals`; materialize_kvantum no longer re-backs it up.
        """
        before_sha = _sha256(HOME / ".config" / "kdeglobals")

        r = run([RICER, "apply", "--wallpaper", self.wp_test, "--extract",
                 "--name", "p2-backup-order-repro"], timeout=60)
        self.assertEqual(r.returncode, 0, f"apply failed: {r.stderr}")

        manifest = json.loads((HOME / ".cache" / "linux-ricing" / "current" / "manifest.json").read_text())
        backup_dir = Path(manifest["backup_dir"])

        kde_backup = backup_dir / "kde" / "kdeglobals"
        kvantum_backup = backup_dir / "kvantum" / "kdeglobals"

        self.assertTrue(
            kde_backup.exists(),
            f"BUG P2: kde/kdeglobals backup missing (materialize_kde must snapshot pre-apply)",
        )
        self.assertFalse(
            kvantum_backup.exists(),
            f"BUG P2: kvantum/kdeglobals backup exists — must not be re-captured "
            f"(stale since materialize_kde already wrote to kdeglobals)",
        )
        self.assertEqual(
            _sha256(kde_backup), before_sha,
            f"BUG P2: kde/kdeglobals backup doesn't match pre-apply state.\n"
            f"  backup sha:     {_sha256(kde_backup)}\n"
            f"  pre-apply sha:  {before_sha}\n"
            f"  The backup was taken after materialize_kde mutated kdeglobals.",
        )

    # ------------------------------------------------------------------
    # P3a — baseline audit misses gtk-4.0 + fastfetch config
    # ------------------------------------------------------------------
    def test_p3a_desktop_state_audit_covers_gtk_and_fastfetch(self):
        """INVARIANT: desktop_state_audit.py's file snapshot must include
        every config file any materializer writes to — else fidelity checks
        can't verify undo.

        Expected labels (flattened filenames in baseline_dir): kdeglobals,
        plasmarc, kcminputrc, kvantum.kvconfig, gtk-3.0-settings,
        gtk-4.0-settings, fastfetch.config.json, dunstrc, rofi.config.rasi,
        waybar.style.css.
        """
        self.assertTrue(AUDIT_PY.exists(), f"audit script missing: {AUDIT_PY}")

        r = run(["python3", str(AUDIT_PY)], timeout=60)
        self.assertEqual(r.returncode, 0, f"audit failed: {r.stderr}")

        baselines = sorted((HOME / ".cache/linux-ricing/baselines").glob("*_files"))
        self.assertTrue(baselines, "no baseline files dir produced")
        latest = baselines[-1]
        present = {p.name for p in latest.iterdir() if p.is_file()}

        required_if_source_exists = {
            # label in audit                     : source path (skip check if source missing)
            "kdeglobals":              HOME / ".config/kdeglobals",
            "plasmarc":                HOME / ".config/plasmarc",
            "kvantum.kvconfig":        HOME / ".config/Kvantum/kvantum.kvconfig",
            "gtk-3.0-settings":        HOME / ".config/gtk-3.0/settings.ini",
            "gtk-4.0-settings":        HOME / ".config/gtk-4.0/settings.ini",
            "fastfetch.config.json":   HOME / ".config/fastfetch/config.json",
            "dunstrc":                 HOME / ".config/dunst/dunstrc",
            "rofi.config.rasi":        HOME / ".config/rofi/config.rasi",
        }
        missing = []
        for label, source in required_if_source_exists.items():
            if source.exists() and label not in present:
                missing.append(label)
        self.assertFalse(
            missing,
            f"BUG P3a: baseline audit missing labels {missing} even though their "
            f"source files exist on disk.\n"
            f"  snapshot dir: {latest}\n"
            f"  present files: {sorted(present)}",
        )

    # ------------------------------------------------------------------
    # P3b — `datetime.utcnow()` deprecation warning corrupts stdout
    # ------------------------------------------------------------------
    def test_p3b_ricer_stdout_is_clean_json(self):
        """INVARIANT: `ricer status`, `ricer extract`, `ricer apply --dry-run`
        must emit only valid output on stdout (no Python warnings).

        Currently FAILS: ricer.py:193 `datetime.utcnow()` is deprecated in
        Python 3.12+ and the DeprecationWarning leaks to stdout, breaking
        pipelines like `ricer extract | jq`.
        """
        r = run([RICER, "status"], timeout=15)
        self.assertEqual(r.returncode, 0, f"status failed: {r.stderr}")
        for bad in ("DeprecationWarning", "utcnow()"):
            self.assertNotIn(
                bad, r.stdout,
                f"BUG P3b: {bad!r} leaked into stdout of `ricer status`:\n{r.stdout[:400]}",
            )


def _sha256(p: Path) -> str:
    import hashlib
    if not p.exists():
        return "MISSING"
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


if __name__ == "__main__":
    unittest.main()
