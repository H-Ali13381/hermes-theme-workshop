"""capture_apply.py — Theme apply + window management for capture_theme_references.

Extracted from scripts/capture_theme_references.py to keep that file within
the 300-line budget.  Handles apply operations and the actual screenshot capture.
"""
from __future__ import annotations

import json
import subprocess

import time
from pathlib import Path

from capture_constants import (
    HOME, CATALOG_DIR, CACHE_DIR, KDE_CAPTURE_BASELINE,
)
from capture_helpers import (
    run_cmd, build_spectacle_command, build_reference_window_command,
    set_kde_icon_theme, set_widget_style, set_wallpaper, set_look_and_feel,
    set_reference_panel_launchers, restart_plasmashell,
    verify_baseline_state, ensure_capture_output_is_present,
    post_apply_wait, ensure_reference_desktop_content,
    catalog_preview_path, option_slug, standard_scene_human_summary,
    extended_scene_payload,
    write_scene_notes, write_standard_scene_readme, write_scene_metadata,
)


# ---------------------------------------------------------------------------
# Baseline + theme apply
# ---------------------------------------------------------------------------

def apply_capture_baseline() -> None:
    run_cmd(["plasma-apply-colorscheme", KDE_CAPTURE_BASELINE["colorscheme"]])
    run_cmd(["plasma-apply-desktoptheme", KDE_CAPTURE_BASELINE["plasma_theme"]])
    run_cmd(["plasma-apply-cursortheme", KDE_CAPTURE_BASELINE["cursor_theme"]])
    set_kde_icon_theme(KDE_CAPTURE_BASELINE["icon_theme"])
    set_widget_style(KDE_CAPTURE_BASELINE["widget_style"])
    kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
    kvantum_config.parent.mkdir(parents=True, exist_ok=True)
    kvantum_config.write_text("[General]\ntheme=KvArcDark\n", encoding="utf-8")
    post_apply_wait()


def apply_default_desktop_state() -> None:
    (HOME / "Desktop").mkdir(parents=True, exist_ok=True)
    ensure_reference_desktop_content()
    set_look_and_feel()
    set_wallpaper(KDE_CAPTURE_BASELINE["wallpaper"])
    set_reference_panel_launchers()
    restart_plasmashell()
    verify_baseline_state()
    ensure_capture_output_is_present()
    write_scene_notes()
    write_standard_scene_readme()
    write_scene_metadata("baseline")
    post_apply_wait(2.0)


def apply_reference_baseline() -> None:
    apply_capture_baseline()
    apply_default_desktop_state()


def apply_kvantum_theme(theme: str) -> None:
    kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
    kvantum_config.parent.mkdir(parents=True, exist_ok=True)
    kvantum_config.write_text(f"[General]\ntheme={theme}\n", encoding="utf-8")
    set_widget_style("kvantum")
    post_apply_wait(2.0)


def apply_cursor_theme(theme: str) -> None:
    run_cmd(["plasma-apply-cursortheme", theme])
    run_cmd(["kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", theme])
    post_apply_wait(1.5)


# ---------------------------------------------------------------------------
# Capture + window management
# ---------------------------------------------------------------------------

def category_capture_mode(category: str) -> tuple[str, bool]:
    if category == "cursors":
        return ("fullscreen", True)
    return ("fullscreen", False)


def screenshot_mode_description(category: str) -> str:
    mode, include_pointer = category_capture_mode(category)
    return f"{mode}{' with pointer' if include_pointer else ''}"


def category_human_summary(category: str) -> str:
    if category == "kvantum":
        return "Qt widget reference window"
    if category == "cursors":
        return "cursor reference board window"
    return "reference window"


def close_stray_windows() -> None:
    for proc_name in ["gwenview", "okular", "eog", "feh"]:
        subprocess.run(["pkill", "-f", proc_name], capture_output=True, timeout=5)
    subprocess.run(["qdbus6", "org.kde.dolphin", "/dolphin/Dolphin_1", "close"], capture_output=True, timeout=5)
    time.sleep(0.5)


def raise_window_by_title(title_substring: str) -> None:
    js_literal = json.dumps(title_substring)  # safe: escapes " and \ in title
    kwin_script = f"""
    var clients = workspace.windowList();
    for (var i = 0; i < clients.length; i++) {{
        if (clients[i].caption.indexOf({js_literal}) !== -1) {{
            var c = clients[i];
            var newX = Math.round((1920 - c.width) / 2);
            var newY = Math.round((1080 - c.height) / 2);
            c.frameGeometry = {{x: newX, y: newY, width: c.width, height: c.height}};
            c.minimized = false;
            workspace.activeWindow = c;
            break;
        }}
    }}
    """
    script_path = CACHE_DIR / "raise_window.js"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    script_path.write_text(kwin_script, encoding="utf-8")
    result = subprocess.run(
        ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript", str(script_path), "hermes_raise"],
        capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    script_id = result.stdout.strip()
    if script_id:
        subprocess.run(["qdbus6", "org.kde.KWin", f"/Scripting/Script{script_id}", "run"], capture_output=True, timeout=10)
        time.sleep(0.5)
        subprocess.run(["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", "hermes_raise"], capture_output=True, timeout=10)


def launch_reference_window(category: str, option_name: str) -> subprocess.Popen:
    return subprocess.Popen(build_reference_window_command(category, option_name),
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def close_reference_window(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    try:
        proc.terminate(); proc.wait(timeout=5)
    except (OSError, TimeoutError):
        try:
            proc.kill()
        except OSError:
            pass


def focus_settle_delay(category: str) -> None:
    time.sleep(1.5 if category == "cursors" else 2.5)


def crop_to_primary_monitor(image_path: Path) -> None:
    """Crop a fullscreen capture to DP-1 (2×DPR, 3840×2160) and resize to 1920×1080."""
    from PIL import Image
    with Image.open(image_path) as img:
        cropped = img.crop((0, 0, 3840, 2160))
        resized = cropped.resize((1920, 1080), Image.Resampling.LANCZOS)
        resized.save(image_path)


def capture_screenshot(output_path: Path, mode: str = "fullscreen", include_pointer: bool = False) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_cmd(build_spectacle_command(output_path, mode=mode, include_pointer=include_pointer), timeout=30)


def ensure_preview_parent(category: str, option_name: str) -> Path:
    preview = catalog_preview_path(category, option_name)
    preview.parent.mkdir(parents=True, exist_ok=True)
    return preview


def real_capture_notes(category: str) -> str:
    return (
        f"Real screenshot captured against the Breeze Dark baseline. "
        f"Capture mode: {screenshot_mode_description(category)}. "
        f"Primary reference output target: {KDE_CAPTURE_BASELINE['capture_output']}. "
        f"Captured from a standardized reference window."
    )


def write_option_readme(category: str, option_name: str, notes: str) -> None:
    option_dir = CATALOG_DIR / category / option_slug(option_name)
    option_dir.mkdir(parents=True, exist_ok=True)
    text = (f"# {option_name}\n\nCategory: {category}\n\nPreview: `preview.png`\n\n{notes}\n\n"
            f"Standard scene: {category_human_summary(category)} | {standard_scene_human_summary()}\n")
    (option_dir / "README.md").write_text(text, encoding="utf-8")


def write_option_metadata(category: str, option_name: str) -> None:
    option_dir = CATALOG_DIR / category / option_slug(option_name)
    option_dir.mkdir(parents=True, exist_ok=True)
    payload = {"category": category, "option": option_name, "baseline": KDE_CAPTURE_BASELINE,
               "mode": screenshot_mode_description(category), "scene": category_human_summary(category),
               "standard_scene": extended_scene_payload(),
               "scene_description": f"{category_human_summary(category)} | {standard_scene_human_summary()}"}
    (option_dir / "metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
