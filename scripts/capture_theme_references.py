#!/usr/bin/env python3
"""
Capture real KDE theme reference screenshots for the ricer catalog.

Workflow:
1. Restore a deterministic KDE baseline
2. Apply exactly one customization
3. Standardize panel + desktop to resemble a basic KDE PC
4. Open a standardized reference window for that category
5. Capture the active window with Spectacle
6. Save to assets/catalog/<category>/<option>/preview.png
7. Restore baseline

Current supported categories:
- kvantum
- cursors
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable

from capture_constants import (
    KDE_CAPTURE_BASELINE, DEFAULT_KVANTUM_OPTIONS, DEFAULT_CURSOR_OPTIONS,
    # Re-export constants accessed directly by tests
    REFERENCE_PANEL_LAUNCHERS, REFERENCE_PANEL_APPS, REFERENCE_DESKTOP_ITEMS,
    REFERENCE_DESKTOP_SHORTCUTS, SCENE_NOTES,
)
from capture_helpers import (
    ensure_requirements, catalog_preview_path, option_slug,
    # Re-export helpers accessed directly by tests
    CATALOG_DIR, build_spectacle_command, build_reference_window_command,
    desktop_shortcut_path, desktop_shortcut_text,
    panel_scene_summary, desktop_and_panel_state_payload, scene_metadata_payload,
    standard_scene_human_summary, extended_scene_payload,
    write_standard_scene_readme, reference_scene_notes_text,
)
from capture_apply import (
    apply_reference_baseline, apply_kvantum_theme, apply_cursor_theme,
    category_capture_mode, screenshot_mode_description, category_human_summary,
    close_stray_windows, raise_window_by_title, launch_reference_window,
    close_reference_window, focus_settle_delay, crop_to_primary_monitor,
    capture_screenshot, ensure_preview_parent, real_capture_notes,
    write_option_readme, write_option_metadata,
)


def standard_scene_readme_text() -> str:
    """Re-export compatibility shim for tests that call this function directly."""
    from capture_helpers import panel_scene_summary, desktop_scene_summary
    return (
        "Standard KDE reference scene\n"
        f"Panel apps: {panel_scene_summary()}\n"
        f"Desktop items: {desktop_scene_summary()}\n"
    )


# All low-level helpers in capture_helpers.py and capture_apply.py.


def default_options_for(category: str) -> list[str]:
    if category == "kvantum":
        return list(DEFAULT_KVANTUM_OPTIONS)
    if category == "cursors":
        return list(DEFAULT_CURSOR_OPTIONS)
    raise ValueError(category)


def supported_category(category: str) -> None:
    if category not in {"kvantum", "cursors"}:
        raise ValueError(f"Unsupported category: {category}")


def apply_customization(category: str, option_name: str) -> None:
    supported_category(category)
    if category == "kvantum":
        apply_kvantum_theme(option_name)
    elif category == "cursors":
        apply_cursor_theme(option_name)


def reset_between_captures() -> None:
    apply_reference_baseline()


def perform_capture(category: str, option_name: str) -> Path:
    preview = ensure_preview_parent(category, option_name)
    mode, include_pointer = category_capture_mode(category)
    proc = None
    try:
        close_stray_windows()
        proc = launch_reference_window(category, option_name)
        focus_settle_delay(category)
        raise_window_by_title("Hermes Ricer Reference")
        time.sleep(0.5)
        capture_screenshot(preview, mode=mode, include_pointer=include_pointer)
        crop_to_primary_monitor(preview)
    finally:
        close_reference_window(proc)
        time.sleep(0.5)
    write_option_readme(category, option_name, real_capture_notes(category))
    write_option_metadata(category, option_name)
    return preview


def verify_preview_exists(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Preview was not created: {path}")


def run_capture(category: str, option_name: str) -> Path:
    reset_between_captures()
    apply_customization(category, option_name)
    preview = perform_capture(category, option_name)
    verify_preview_exists(preview)
    reset_between_captures()
    return preview


def capture_many(category: str, options: Iterable[str]) -> list[Path]:
    return [run_capture(category, option_name) for option_name in options]


def dry_run_payload(category: str, options: list[str]) -> dict:
    return {
        "baseline": KDE_CAPTURE_BASELINE,
        "category": category,
        "options": options,
        "outputs": [str(catalog_preview_path(category, name)) for name in options],
        "mode": screenshot_mode_description(category),
        "scene": category_human_summary(category),
        "standard_scene": extended_scene_payload(),
    }


def capture_result_payload(category: str, outputs: list[Path]) -> dict:
    return {
        "status": "success",
        "category": category,
        "capture_output": KDE_CAPTURE_BASELINE["capture_output"],
        "mode": screenshot_mode_description(category),
        "scene": category_human_summary(category),
        "standard_scene": extended_scene_payload(),
        "captured": [str(p) for p in outputs],
    }


def execute(category: str, options: list[str], dry_run: bool) -> int:
    if dry_run:
        print(json.dumps(dry_run_payload(category, options), indent=2))
        return 0
    outputs = capture_many(category, options)
    print(json.dumps(capture_result_payload(category, outputs), indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture real theme reference screenshots for the ricer catalog.")
    parser.add_argument("--category", choices=["kvantum", "cursors"], required=True)
    parser.add_argument("--option", action="append", default=[], help="Specific option(s) to capture. Repeatable.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be captured without changing anything.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_requirements()
    options = args.option or default_options_for(args.category)
    return execute(args.category, options, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
