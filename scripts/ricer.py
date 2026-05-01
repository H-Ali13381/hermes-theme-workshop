#!/usr/bin/env python3
"""
Hermes Ricer — AI-Native Desktop Theming Engine
Thin dispatcher: imports all sub-modules and exposes the CLI.

Sub-module layout
-----------------
  materializers/   — per-app materialize_<app>() implementations
  presets.py       — PRESETS dict and load_preset()
  ricer_undo.py    — undo(), _describe_change(), per-app undo handlers
  core/            — shared utilities (backup, discovery, process, …)
"""

# ── stdlib ───────────────────────────────────────────────────────────────────
import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── bootstrap: ensure scripts/ is importable regardless of cwd ───────────────
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# ── core utilities ────────────────────────────────────────────────────────────
from core.constants import BACKUP_DIR, CURRENT_DIR, require_linux  # noqa: E402
from core.discovery import discover_apps, discover         # noqa: E402
from core.session_io import load_design_file               # noqa: E402
from core.snapshots import snapshot_kde_state              # noqa: E402

# ── materializers ─────────────────────────────────────────────────────────────
from materializers import (                                # noqa: E402
    APP_MATERIALIZERS,
    materialize_kde, materialize_kvantum, materialize_plasma_theme,
    materialize_cursor, materialize_icon_theme, materialize_kde_lockscreen,
    materialize_lnf, _lockscreen_lnf_for_palette,
    materialize_kitty, materialize_alacritty, materialize_konsole,
    materialize_waybar, materialize_polybar,
    materialize_rofi, materialize_wofi,
    materialize_dunst, materialize_mako, materialize_swaync,
    materialize_gnome_shell, materialize_gnome_lockscreen,
    materialize_hyprland, materialize_hyprlock,
    materialize_gtk, materialize_picom, materialize_fastfetch,
    materialize_starship, _build_starship_toml,
    materialize_wallpaper,
)

# ── presets ───────────────────────────────────────────────────────────────────
from presets import PRESETS, load_preset                   # noqa: E402

# ── undo / rollback ───────────────────────────────────────────────────────────
from ricer_undo import (                                   # noqa: E402
    undo, undo_session, simulate_undo_session, _describe_change,
    collect_deletable_artifacts, _collect_session_manifests, _active_theme_name,
)


def _confirm_artifact_deletion(manifest_paths: list, assume_yes: bool) -> bool:
    """Show files that undo would delete and prompt the user (unless --yes).

    Returns True if undo should proceed with deletion, False to keep
    artifacts on disk.  Returns True with no prompt when nothing would be
    deleted, when --yes is set, or when stdin is not a TTY (non-interactive
    runs default to deletion to match prior behaviour).
    """
    artifacts: list[dict] = []
    for mp in manifest_paths:
        for a in collect_deletable_artifacts(mp):
            artifacts.append({**a, "manifest": str(mp)})
    if not artifacts:
        return True
    if assume_yes:
        return True
    print("\nThe following generated files will be DELETED on undo "
          "(no backup exists, so they cannot be restored):", file=sys.stderr)
    for a in artifacts:
        print(f"  [{a['app']:>14s}] {a['path']}", file=sys.stderr)
    print(f"\n{len(artifacts)} file(s) will be removed. "
          "Pass --keep-artifacts to leave them in place.", file=sys.stderr)
    if not sys.stdin.isatty():
        print("(non-interactive stdin: defaulting to delete; "
              "use --yes to silence or --keep-artifacts to preserve)",
              file=sys.stderr)
        return True
    try:
        ans = input("Proceed with deletion? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nAborted.", file=sys.stderr)
        return False
    return ans in ("y", "yes")

# ---------------------------------------------------------------------------
# ORCHESTRATOR
# ---------------------------------------------------------------------------
def materialize(
    design: dict,
    apps: dict | None = None,
    wallpaper: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Materialize the design system across all detected apps."""
    if apps is None:
        apps = discover_apps()

    # ONE shared timestamp for ALL materializers — no race condition
    backup_ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    all_changes = []

    for app_name, mat_fn in APP_MATERIALIZERS.items():
        if app_name in apps:
            try:
                changes = mat_fn(design, backup_ts=backup_ts, dry_run=dry_run)
                all_changes.extend(changes)
            except Exception as e:
                all_changes.append({"app": app_name, "action": "error", "error": str(e)})

    if wallpaper:
        # Inject resolved wallpaper path into a design copy so materialize_wallpaper
        # can conform to the standard Materializer Contract (design, backup_ts, dry_run).
        design_with_wallpaper = {**design, "wallpaper_path": wallpaper}
        all_changes.extend(
            materialize_wallpaper(design_with_wallpaper, backup_ts, dry_run=dry_run)
        )

    manifest = {
        "timestamp": backup_ts,
        "design_system": design,
        "changes": all_changes,
        "dry_run": dry_run,
        "backup_dir": str(BACKUP_DIR / backup_ts),
    }

    if not dry_run:
        CURRENT_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = CURRENT_DIR / "manifest.json"

        # Archive previous manifest to history
        if manifest_path.exists():
            history_dir = CURRENT_DIR / "history"
            history_dir.mkdir(exist_ok=True)
            prev = json.loads(manifest_path.read_text(encoding="utf-8"))
            prev_ts = prev.get("timestamp", backup_ts + "_prev")
            shutil.move(str(manifest_path), str(history_dir / f"manifest_{prev_ts}.json"))

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return manifest

# (Undo helpers and rollback logic live in ricer_undo.py)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    require_linux()
    parser = argparse.ArgumentParser(description="Hermes Ricer — AI-Native Desktop Theming")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("discover", help="Detect desktop stack")

    apply_parser = subparsers.add_parser("apply", help="Apply a design system JSON")
    apply_parser.add_argument("--design", default=None, help="Path to design_system.json (omit with --extract)")
    apply_parser.add_argument("--wallpaper", default=None, help="Wallpaper image path")
    apply_parser.add_argument("--extract", action="store_true",
                              help="Derive palette from --wallpaper instead of reading --design")
    apply_parser.add_argument("--name", default=None, help="Theme name override when using --extract")
    apply_parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    apply_parser.add_argument("--only", default=None,
                              help="Restrict to this app key or element category (e.g. 'kitty', 'terminal')")
    apply_parser.add_argument("--app", default=None,
                              help="Specific sub-app to materialize (e.g. 'kitty' within 'terminal')")

    preset_parser = subparsers.add_parser("preset", help="Apply a named preset")
    preset_parser.add_argument("name", choices=list(PRESETS.keys()), help="Preset name")
    preset_parser.add_argument("--dry-run", action="store_true")

    extract_parser = subparsers.add_parser("extract", help="Extract a design system from an image")
    extract_parser.add_argument("--image", required=True, help="Path to image (wallpaper/reference)")
    extract_parser.add_argument("--out", default=None, help="Write JSON here (default: stdout)")
    extract_parser.add_argument("--name", default=None, help="Theme name (default: image stem)")

    undo_p = subparsers.add_parser("undo", help="Undo last theme application")
    undo_p.add_argument("-y", "--yes", action="store_true",
                        help="Skip the artifact-deletion confirmation prompt")
    undo_p.add_argument("--keep-artifacts", action="store_true",
                        help="Restore backed-up files but keep generated artifacts (no-backup files) on disk")
    undo_session_p = subparsers.add_parser("undo-session", help="Roll back every apply of the current session (active manifest + history)")
    undo_session_p.add_argument("--all", action="store_true", help="Walk every manifest in history regardless of theme (default: scope to active session's theme)")
    undo_session_p.add_argument("-y", "--yes", action="store_true",
                                help="Skip the artifact-deletion confirmation prompt")
    undo_session_p.add_argument("--keep-artifacts", action="store_true",
                                help="Restore backed-up files but keep generated artifacts (no-backup files) on disk")
    subparsers.add_parser("status", help="Show detected stack and active theme")
    subparsers.add_parser("presets", help="List available presets")
    subparsers.add_parser("simulate-undo", help="Show exactly what undo would restore, without applying anything")
    sim_session_p = subparsers.add_parser("simulate-undo-session", help="Show exactly what undo-session would restore across the full session, without applying anything")
    sim_session_p.add_argument("--all", action="store_true", help="Walk every manifest in history regardless of theme (default: scope to active session's theme)")

    args = parser.parse_args()

    if args.command == "discover":
        result = discover()
        print(json.dumps(result, indent=2, default=str))
        return

    if args.command == "presets":
        for name, preset in PRESETS.items():
            print(f"  {name:25s} — {preset['description']}")
        return

    if args.command == "status":
        result = discover()
        print("=== Desktop Stack ===")
        print(f"  WM/DE   : {result['desktop']['wm']}")
        print(f"  Session : {result['desktop']['session_type']}")
        print(f"  Env     : {result['desktop']['desktop_env']}")
        print("\n=== Detected Apps ===")
        for app in sorted(result["apps"]):
            print(f"  {app}")
        manifest_path = CURRENT_DIR / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            ds = manifest.get("design_system", {})
            print("\n=== Active Theme ===")
            print(f"  Name        : {ds.get('name', 'unknown')}")
            print(f"  Description : {ds.get('description', '')}")
            print(f"  Applied at  : {manifest.get('timestamp', '')}")
            if manifest.get("undone"):
                print(f"  Status      : UNDONE at {manifest.get('undone_at')}")
            print(f"  Backup dir  : {manifest.get('backup_dir', '')}")
        else:
            print("\n=== Active Theme ===")
            print("  None (no theme applied yet)")
        return

    if args.command == "preset":
        design = load_preset(args.name)
        if not design:
            print(f"Unknown preset: {args.name}", file=sys.stderr)
            sys.exit(1)
        manifest = materialize(design, dry_run=args.dry_run)
        print(json.dumps(manifest, indent=2, default=str))
        return

    if args.command == "extract":
        try:
            from palette_extractor import extract_palette
        except ImportError as e:
            print(f"extract: {e}", file=sys.stderr)
            sys.exit(1)
        try:
            design = extract_palette(args.image, name=args.name)
        except (FileNotFoundError, RuntimeError) as e:
            print(f"extract: {e}", file=sys.stderr)
            sys.exit(1)
        output = json.dumps(design, indent=2)
        if args.out:
            Path(args.out).expanduser().write_text(output + "\n", encoding="utf-8")
            print(f"wrote {args.out}", file=sys.stderr)
        else:
            print(output)
        return

    if args.command == "apply":
        if args.extract:
            if not args.wallpaper:
                print("apply --extract requires --wallpaper", file=sys.stderr)
                sys.exit(2)
            try:
                from palette_extractor import extract_palette
            except ImportError as e:
                print(f"apply --extract: {e}", file=sys.stderr)
                sys.exit(1)
            try:
                design = extract_palette(args.wallpaper, name=args.name)
            except (FileNotFoundError, RuntimeError) as e:
                print(f"apply --extract: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            if not args.design:
                print("apply requires --design (or --extract with --wallpaper)", file=sys.stderr)
                sys.exit(2)
            design = load_design_file(args.design)
        # --app / --only: restrict materialization to a specific materializer key.
        # Fail closed: an unknown target must never fall back to applying all apps.
        only_app = args.app or args.only  # --app takes precedence
        if not only_app:
            print("apply requires --only or --app to target exactly one materializer", file=sys.stderr)
            sys.exit(2)
        if only_app not in APP_MATERIALIZERS:
            print(f"Unknown materializer: {only_app}", file=sys.stderr)
            sys.exit(2)
        all_detected = discover_apps()
        if only_app not in all_detected:
            print(f"Materializer not detected: {only_app}", file=sys.stderr)
            sys.exit(2)
        only_apps = {only_app: all_detected[only_app]}
        manifest = materialize(design, apps=only_apps, wallpaper=args.wallpaper, dry_run=args.dry_run)
        print(json.dumps(manifest, indent=2, default=str))
        return

    if args.command == "undo":
        delete = not args.keep_artifacts
        if delete:
            delete = _confirm_artifact_deletion([CURRENT_DIR / "manifest.json"], args.yes)
        result = undo(delete_artifacts=delete)
        print(json.dumps(result, indent=2, default=str))
        if result["status"] == "success":
            print("\nUndo complete.", file=sys.stderr)
        elif result["status"] == "partial":
            print(f"\nPartial undo — {len(result['failed'])} failure(s). Check 'failed' in output.", file=sys.stderr)
        return

    if args.command == "simulate-undo":
        manifest_path = CURRENT_DIR / "manifest.json"
        if not manifest_path.exists():
            print("No manifest found — no theme has been applied yet.")
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("dry_run"):
            print("Last run was a dry-run — nothing to undo.")
            return
        print("=== Simulate Undo ===")
        print(f"Theme applied  : {manifest.get('design_system', {}).get('name', 'unknown')}")
        print(f"Applied at     : {manifest.get('timestamp', 'unknown')}")
        print(f"Backup dir     : {manifest.get('backup_dir', 'unknown')}")
        print(f"Undone already : {manifest.get('undone', False)}")
        print()
        for change in manifest.get("changes", []):
            for line in _describe_change(change):
                print(line)
        print()
        print("Run 'ricer undo' to execute the above.")
        return

    if args.command == "undo-session":
        delete = not args.keep_artifacts
        if delete:
            theme = None if args.all else _active_theme_name()
            session_manifests = _collect_session_manifests(theme)
            delete = _confirm_artifact_deletion(session_manifests, args.yes)
        result = undo_session(all_history=args.all, delete_artifacts=delete)
        print(json.dumps(result, indent=2, default=str))
        if result.get("status") == "success":
            print(f"\nSession rollback complete — {result.get('manifests_executed', 0)} "
                  f"manifest(s) undone, {result.get('total_restored', 0)} restore(s). "
                  f"Scope: {result.get('scope')}.", file=sys.stderr)
        elif result.get("status") == "partial":
            print(f"\nPartial session rollback — {result.get('total_failed', 0)} "
                  f"failure(s) across {result.get('manifests_executed', 0)} manifest(s). "
                  f"Check 'per_manifest' in output. Scope: {result.get('scope')}.", file=sys.stderr)
        return

    if args.command == "simulate-undo-session":
        result = simulate_undo_session(all_history=args.all)
        manifests = result.get("manifests", [])
        if not manifests:
            print("No manifests found — no session to roll back.")
            return
        print("=== Simulate Session Undo ===")
        print(f"Scope                : {result.get('scope')}")
        print(f"Manifests in session : {result.get('manifests_total', 0)}")
        print(f"Order                : newest \u2192 oldest")
        print()
        for i, m in enumerate(manifests, 1):
            tag = "WOULD UNDO" if m.get("status") == "would_undo" else f"SKIP ({m.get('reason', m.get('status'))})"
            print(f"--- [{i}/{len(manifests)}] {tag} ---")
            print(f"  manifest   : {m.get('manifest')}")
            print(f"  theme      : {m.get('theme')}")
            print(f"  timestamp  : {m.get('timestamp')}")
            print(f"  apps       : {', '.join(m.get('apps', [])) or '(none)'}")
            print(f"  backup_dir : {m.get('backup_dir')}")
            for line in m.get("change_descriptions", []):
                print(f"    {line}")
            print()
        print("Run 'ricer undo-session' to execute the above.")
        return

    parser.print_help()

if __name__ == "__main__":
    main()
