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
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable

HOME = Path.home()
SKILL_DIR = HOME / ".hermes" / "skills" / "creative" / "linux-ricing"
CATALOG_DIR = SKILL_DIR / "assets" / "catalog"
CACHE_DIR = HOME / ".cache" / "linux-ricing" / "capture_theme_references"
REFERENCE_WINDOW_SCRIPT = SKILL_DIR / "scripts" / "reference_capture_window.py"
DESKTOP_DIR = HOME / "Desktop"

KDE_CAPTURE_BASELINE = {
    "colorscheme": "BreezeDark",
    "look_and_feel": "org.kde.breezedark.desktop",
    "plasma_theme": "default",
    "cursor_theme": "breeze_cursors",
    "icon_theme": "breeze-dark",
    "widget_style": "Breeze",
    "wallpaper": "/usr/share/wallpapers/Next/contents/images_dark/5120x2880.png",
    "capture_output": "DP-1",
}

DEFAULT_KVANTUM_OPTIONS = [
    "catppuccin-mocha-teal",
    "catppuccin-mocha-mauve",
    "catppuccin-mocha-peach",
    "catppuccin-mocha-yellow",
]

DEFAULT_CURSOR_OPTIONS = [
    "catppuccin-macchiato-teal-cursors",
    "catppuccin-macchiato-mauve-cursors",
    "catppuccin-macchiato-yellow-cursors",
    "catppuccin-macchiato-red-cursors",
]

REFERENCE_PANEL_LAUNCHERS = \
    "applications:firefox.desktop," \
    "applications:org.kde.dolphin.desktop," \
    "applications:systemsettings.desktop," \
    "applications:org.kde.discover.desktop," \
    "applications:org.kde.konsole.desktop"

REFERENCE_PANEL_APPS = [
    "Firefox",
    "Dolphin",
    "System Settings",
    "Discover",
    "Konsole",
]

REFERENCE_DESKTOP_ITEMS = [
    "Home.desktop",
    "Trash.desktop",
    "Firefox.desktop",
    "Dolphin.desktop",
    "System Settings.desktop",
    "Discover.desktop",
]

REFERENCE_DESKTOP_SHORTCUTS = {
    "Home.desktop": {
        "Name": "Home",
        "Icon": "user-home",
        "Type": "Link",
        "URL": "file:///home/neos",
    },
    "Trash.desktop": {
        "Name": "Trash",
        "Icon": "user-trash",
        "Type": "Link",
        "URL": "trash:/",
    },
    "Firefox.desktop": {
        "Name": "Firefox",
        "Icon": "firefox",
        "Type": "Application",
        "Exec": "firefox",
    },
    "Dolphin.desktop": {
        "Name": "Dolphin",
        "Icon": "system-file-manager",
        "Type": "Application",
        "Exec": "dolphin",
    },
    "System Settings.desktop": {
        "Name": "System Settings",
        "Icon": "preferences-system",
        "Type": "Application",
        "Exec": "systemsettings",
    },
    "Discover.desktop": {
        "Name": "Discover",
        "Icon": "plasmadiscover",
        "Type": "Application",
        "Exec": "plasma-discover",
    },
}

SCENE_NOTES = """Reference baseline intent:
- Breeze Dark colorscheme
- default Plasma theme
- Breeze cursor and Breeze dark icons
- standard KDE wallpaper
- simplified panel launchers representing a basic KDE PC
- showcase standard app icons in the panel and on the desktop
- desktop kept on a neutral default-like state while captures focus on the active reference window
- capture uses active reference window instead of whole-screen shot
"""


def option_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def catalog_preview_path(category: str, option_name: str) -> Path:
    return CATALOG_DIR / category / option_slug(option_name) / "preview.png"


def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_cmd(cmd: list[str], timeout: int = 30, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def build_spectacle_command(output_path: Path, mode: str = "activewindow", include_pointer: bool = False) -> list[str]:
    cmd = ["spectacle", "--background", "--nonotify"]
    if mode == "activewindow":
        cmd.append("--activewindow")
    elif mode == "fullscreen":
        cmd.append("--fullscreen")
    elif mode == "current":
        cmd.append("--current")
    else:
        raise ValueError(f"Unsupported spectacle capture mode: {mode}")
    cmd += ["--output", str(output_path), "--delay", "800"]
    if include_pointer:
        cmd.append("--pointer")
    return cmd


def build_reference_window_command(category: str, option_name: str) -> list[str]:
    return [
        "python3",
        str(REFERENCE_WINDOW_SCRIPT),
        "--category",
        category,
        "--theme-name",
        option_name,
    ]


def ensure_reference_window_script_exists() -> None:
    if not REFERENCE_WINDOW_SCRIPT.exists():
        raise RuntimeError(f"Reference window script not found: {REFERENCE_WINDOW_SCRIPT}")


def ensure_requirements() -> None:
    required = [
        "spectacle",
        "qdbus6",
        "plasma-apply-colorscheme",
        "plasma-apply-cursortheme",
        "plasma-apply-desktoptheme",
        "plasma-apply-lookandfeel",
        "plasma-apply-wallpaperimage",
        "kwriteconfig6",
        "kreadconfig6",
        "kscreen-doctor",
        "kquitapp6",
        "plasmashell",
        "python3",
    ]
    missing = [name for name in required if not cmd_exists(name)]
    if missing:
        raise RuntimeError(f"Missing required commands: {', '.join(missing)}")
    ensure_reference_window_script_exists()


def kwin_reconfigure() -> None:
    run_cmd(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=10)


def set_kde_icon_theme(theme: str) -> None:
    run_cmd(["kwriteconfig6", "--file", "kdeglobals", "--group", "Icons", "--key", "Theme", theme])


def set_widget_style(style: str) -> None:
    run_cmd(["kwriteconfig6", "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", style])


def set_wallpaper(path: str) -> None:
    run_cmd(["plasma-apply-wallpaperimage", path], timeout=30)


def set_look_and_feel() -> None:
    run_cmd(["plasma-apply-lookandfeel", "--apply", KDE_CAPTURE_BASELINE["look_and_feel"]], timeout=40)


def set_reference_panel_launchers() -> None:
    appletsrc = HOME / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
    if not appletsrc.exists():
        return
    text = appletsrc.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"(^launchers=).*?$", r"\1" + REFERENCE_PANEL_LAUNCHERS, text, flags=re.MULTILINE)
    appletsrc.write_text(text, encoding="utf-8")


def restart_plasmashell() -> None:
    run_cmd(["kquitapp6", "plasmashell"], timeout=10, check=False)
    time.sleep(1.0)
    subprocess.Popen(["plasmashell", "--replace"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)


def ensure_capture_output_is_present() -> None:
    result = run_cmd(["kscreen-doctor", "-o"], timeout=15)
    if KDE_CAPTURE_BASELINE["capture_output"] not in result.stdout:
        raise RuntimeError(
            f"Capture output {KDE_CAPTURE_BASELINE['capture_output']} not present.\n{result.stdout}"
        )


def verify_baseline_state() -> None:
    checks = [
        (["kreadconfig6", "--file", "kdeglobals", "--group", "Icons", "--key", "Theme"], KDE_CAPTURE_BASELINE["icon_theme"]),
        (["kreadconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme"], KDE_CAPTURE_BASELINE["cursor_theme"]),
        (["kreadconfig6", "--file", "plasmarc", "--group", "Theme", "--key", "name"], KDE_CAPTURE_BASELINE["plasma_theme"]),
    ]
    for cmd, expected in checks:
        result = run_cmd(cmd, timeout=10)
        if result.stdout.strip() != expected:
            raise RuntimeError(
                f"Baseline verification failed for {' '.join(cmd)}: expected {expected!r}, got {result.stdout.strip()!r}"
            )


def desktop_shortcut_path(filename: str) -> Path:
    return DESKTOP_DIR / filename


def desktop_shortcut_text(filename: str, spec: dict[str, str]) -> str:
    lines = ["[Desktop Entry]"]
    for key in ["Name", "Icon", "Type", "Exec", "URL"]:
        if key in spec:
            lines.append(f"{key}={spec[key]}")
    lines.append("Terminal=false")
    return "\n".join(lines) + "\n"


def ensure_reference_desktop_shortcuts() -> None:
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    # Remove any old placeholder files
    for junk in ["README.txt", "HOME_REFERENCE.txt", "TRASH_REFERENCE.txt"]:
        (DESKTOP_DIR / junk).unlink(missing_ok=True)
    for filename, spec in REFERENCE_DESKTOP_SHORTCUTS.items():
        path = desktop_shortcut_path(filename)
        path.write_text(desktop_shortcut_text(filename, spec), encoding="utf-8")
        path.chmod(0o755)
        # Mark as trusted so KDE renders the icon instead of showing a text file
        subprocess.run(
            ["setfattr", "-n", "user.xdg.origin.url", "-v", f"file://{path}", str(path)],
            capture_output=True, timeout=5,
        )


def ensure_reference_desktop_items_manifest() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = CACHE_DIR / "desktop_reference_items.txt"
    manifest.write_text("\n".join(REFERENCE_DESKTOP_ITEMS) + "\n", encoding="utf-8")


def ensure_reference_panel_manifest() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = CACHE_DIR / "panel_reference_apps.txt"
    manifest.write_text("\n".join(REFERENCE_PANEL_APPS) + "\n", encoding="utf-8")


def desktop_scene_summary() -> str:
    return ", ".join(REFERENCE_DESKTOP_ITEMS)


def panel_scene_summary() -> str:
    return ", ".join(REFERENCE_PANEL_APPS)


def basic_kde_pc_summary() -> str:
    return f"Panel apps: {panel_scene_summary()} | Desktop items: {desktop_scene_summary()}"


def panel_and_desktop_notes() -> str:
    return "Basic KDE panel/desktop reference: " + basic_kde_pc_summary()


def reference_scene_notes_text() -> str:
    return SCENE_NOTES + "\n" + panel_and_desktop_notes() + "\n"


def desktop_and_panel_state_payload() -> dict:
    return {
        "panel_apps": REFERENCE_PANEL_APPS,
        "desktop_items": REFERENCE_DESKTOP_ITEMS,
        "desktop_shortcuts": REFERENCE_DESKTOP_SHORTCUTS,
    }


def extended_scene_payload() -> dict:
    payload = desktop_and_panel_state_payload()
    payload["summary"] = standard_scene_human_summary()
    return payload


def standard_scene_human_summary() -> str:
    return basic_kde_pc_summary()


def scene_metadata_payload(category: str) -> dict:
    data = extended_scene_payload()
    data["category"] = category
    return data


def write_scene_notes() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "scene_notes.txt").write_text(reference_scene_notes_text(), encoding="utf-8")


def write_standard_scene_readme() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "standard_scene.txt").write_text(standard_scene_readme_text(), encoding="utf-8")


def standard_scene_readme_text() -> str:
    return (
        "Standard KDE reference scene\n"
        f"Panel apps: {panel_scene_summary()}\n"
        f"Desktop items: {desktop_scene_summary()}\n"
    )


def write_scene_metadata(category: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"scene_{category}.json").write_text(json.dumps(scene_metadata_payload(category), indent=2), encoding="utf-8")


def ensure_reference_desktop_content() -> None:
    ensure_reference_desktop_shortcuts()
    ensure_reference_desktop_items_manifest()
    ensure_reference_panel_manifest()


def ensure_reference_desktop_files() -> None:
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)


def post_apply_wait(seconds: float = 1.5) -> None:
    time.sleep(seconds)
    kwin_reconfigure()
    time.sleep(1.0)


def apply_capture_baseline() -> None:
    run_cmd(["plasma-apply-colorscheme", KDE_CAPTURE_BASELINE["colorscheme"]])
    run_cmd(["plasma-apply-desktoptheme", KDE_CAPTURE_BASELINE["plasma_theme"]])
    run_cmd(["plasma-apply-cursortheme", KDE_CAPTURE_BASELINE["cursor_theme"]])
    set_kde_icon_theme(KDE_CAPTURE_BASELINE["icon_theme"])
    set_widget_style(KDE_CAPTURE_BASELINE["widget_style"])

    kvantum_config = HOME / ".config" / "Kvantum" / "kvantum.kvconfig"
    if kvantum_config.exists():
        kvantum_config.parent.mkdir(parents=True, exist_ok=True)
        kvantum_config.write_text("[General]\ntheme=KvArcDark\n", encoding="utf-8")

    post_apply_wait()


def apply_default_desktop_state() -> None:
    ensure_reference_desktop_files()
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


def category_capture_mode(category: str) -> tuple[str, bool]:
    # Use --fullscreen and crop to DP-1 region afterward.
    # Spectacle --current captures the monitor of the *focused* window, which is
    # often the terminal that launched the script (on HDMI-A-1), not the reference
    # window on DP-1. Fullscreen + crop guarantees we get the right monitor.
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
    """Close GUI apps that might obscure the reference window on DP-1."""
    for proc_name in ["gwenview", "okular", "eog", "feh"]:
        subprocess.run(["pkill", "-f", proc_name], capture_output=True, timeout=5)
    # Close Dolphin windows but not the daemon
    subprocess.run(["qdbus6", "org.kde.dolphin", "/dolphin/Dolphin_1", "close"], capture_output=True, timeout=5)
    time.sleep(0.5)


def raise_window_by_title(title_substring: str) -> None:
    """Use KWin scripting to move a window to DP-1 and activate it.

    On Wayland, Qt's raise_() and move() are ignored by the compositor.
    KWin scripting via D-Bus is the only reliable way to reposition and
    focus a window.
    """
    # KWin JS: find window, move to DP-1 center, activate
    kwin_script = f"""
    var clients = workspace.windowList();
    for (var i = 0; i < clients.length; i++) {{
        if (clients[i].caption.indexOf("{title_substring}") !== -1) {{
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
        ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript",
         str(script_path), "hermes_raise"],
        capture_output=True, text=True, timeout=10,
    )
    script_id = result.stdout.strip()
    if script_id:
        subprocess.run(
            ["qdbus6", "org.kde.KWin", f"/Scripting/Script{script_id}", "run"],
            capture_output=True, timeout=10,
        )
        time.sleep(0.5)
        subprocess.run(
            ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", "hermes_raise"],
            capture_output=True, timeout=10,
        )


def launch_reference_window(category: str, option_name: str) -> subprocess.Popen:
    return subprocess.Popen(build_reference_window_command(category, option_name), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def close_reference_window(proc: subprocess.Popen | None) -> None:
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def focus_settle_delay(category: str) -> None:
    time.sleep(1.5 if category == "cursors" else 2.5)


def crop_to_primary_monitor(image_path: Path) -> None:
    """Crop a fullscreen capture to DP-1 and resize to 1920x1080.

    Spectacle fullscreen on Wayland captures all monitors at 2x DPR.
    DP-1 is at logical geometry (0,0) 1920x1080, so in the capture buffer
    it occupies pixels (0,0) to (3840, 2160). We crop that region and
    resize to 1920x1080 for a standard 1080p catalog preview.
    """
    from PIL import Image
    img = Image.open(image_path)
    # DP-1 at logical (0,0) 1920x1080 → 2x DPR → pixel region (0,0,3840,2160)
    cropped = img.crop((0, 0, 3840, 2160))
    resized = cropped.resize((1920, 1080), Image.LANCZOS)
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
    text = (
        f"# {option_name}\n\n"
        f"Category: {category}\n\n"
        f"Preview: `preview.png`\n\n"
        f"{notes}\n\n"
        f"Standard scene: {category_human_summary(category)} | {standard_scene_human_summary()}\n"
    )
    (option_dir / "README.md").write_text(text, encoding="utf-8")


def write_option_metadata(category: str, option_name: str) -> None:
    option_dir = CATALOG_DIR / category / option_slug(option_name)
    option_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "category": category,
        "option": option_name,
        "baseline": KDE_CAPTURE_BASELINE,
        "mode": screenshot_mode_description(category),
        "scene": category_human_summary(category),
        "standard_scene": extended_scene_payload(),
        "scene_description": f"{category_human_summary(category)} | {standard_scene_human_summary()}",
    }
    (option_dir / "metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


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
