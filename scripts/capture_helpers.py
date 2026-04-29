"""capture_helpers.py — KDE shell ops and scene setup for capture_theme_references.

Extracted from scripts/capture_theme_references.py to keep that file within
the 300-line budget.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import time
from pathlib import Path

from capture_constants import (
    HOME, CATALOG_DIR, CACHE_DIR, DESKTOP_DIR, REFERENCE_WINDOW_SCRIPT,
    KDE_CAPTURE_BASELINE, REFERENCE_PANEL_LAUNCHERS,
    REFERENCE_PANEL_APPS, REFERENCE_DESKTOP_ITEMS,
    REFERENCE_DESKTOP_SHORTCUTS, SCENE_NOTES,
)


# ---------------------------------------------------------------------------
# Shell utilities
# ---------------------------------------------------------------------------

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
    return ["python3", str(REFERENCE_WINDOW_SCRIPT), "--category", category, "--theme-name", option_name]


# ---------------------------------------------------------------------------
# KDE config write ops
# ---------------------------------------------------------------------------

def ensure_reference_window_script_exists() -> None:
    if not REFERENCE_WINDOW_SCRIPT.exists():
        raise RuntimeError(f"Reference window script not found: {REFERENCE_WINDOW_SCRIPT}")


def ensure_requirements() -> None:
    required = [
        "spectacle", "qdbus6", "plasma-apply-colorscheme", "plasma-apply-cursortheme",
        "plasma-apply-desktoptheme", "plasma-apply-lookandfeel", "plasma-apply-wallpaperimage",
        "kwriteconfig6", "kreadconfig6", "kscreen-doctor", "kquitapp6", "plasmashell", "python3",
    ]
    missing = [n for n in required if not cmd_exists(n)]
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
    subprocess.Popen(["plasmashell", "--replace"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3.0)


def ensure_capture_output_is_present() -> None:
    result = run_cmd(["kscreen-doctor", "-o"], timeout=15)
    if KDE_CAPTURE_BASELINE["capture_output"] not in result.stdout:
        raise RuntimeError(f"Capture output {KDE_CAPTURE_BASELINE['capture_output']} not present.\n{result.stdout}")


def verify_baseline_state() -> None:
    checks = [
        (["kreadconfig6", "--file", "kdeglobals", "--group", "Icons", "--key", "Theme"], KDE_CAPTURE_BASELINE["icon_theme"]),
        (["kreadconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme"], KDE_CAPTURE_BASELINE["cursor_theme"]),
        (["kreadconfig6", "--file", "plasmarc", "--group", "Theme", "--key", "name"], KDE_CAPTURE_BASELINE["plasma_theme"]),
    ]
    for cmd, expected in checks:
        result = run_cmd(cmd, timeout=10)
        if result.stdout.strip() != expected:
            raise RuntimeError(f"Baseline verification failed for {' '.join(cmd)}: expected {expected!r}, got {result.stdout.strip()!r}")


def post_apply_wait(seconds: float = 1.5) -> None:
    time.sleep(seconds)
    kwin_reconfigure()
    time.sleep(1.0)



# ---------------------------------------------------------------------------
# Desktop scene setup
# ---------------------------------------------------------------------------

def option_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def catalog_preview_path(category: str, option_name: str) -> Path:
    return CATALOG_DIR / category / option_slug(option_name) / "preview.png"


def desktop_shortcut_path(filename: str) -> Path:
    return DESKTOP_DIR / filename


def desktop_shortcut_text(filename: str, spec: dict) -> str:
    lines = ["[Desktop Entry]"]
    for key in ["Name", "Icon", "Type", "Exec", "URL"]:
        if key in spec:
            lines.append(f"{key}={spec[key]}")
    lines.append("Terminal=false")
    return "\n".join(lines) + "\n"


def ensure_reference_desktop_shortcuts() -> None:
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    for junk in ["README.txt", "HOME_REFERENCE.txt", "TRASH_REFERENCE.txt"]:
        (DESKTOP_DIR / junk).unlink(missing_ok=True)
    for filename, spec in REFERENCE_DESKTOP_SHORTCUTS.items():
        path = desktop_shortcut_path(filename)
        path.write_text(desktop_shortcut_text(filename, spec), encoding="utf-8")
        path.chmod(0o755)
        subprocess.run(
            ["setfattr", "-n", "user.xdg.origin.url", "-v", f"file://{path}", str(path)],
            capture_output=True, timeout=5,
        )


def ensure_reference_desktop_items_manifest() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "desktop_reference_items.txt").write_text("\n".join(REFERENCE_DESKTOP_ITEMS) + "\n", encoding="utf-8")


def ensure_reference_panel_manifest() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "panel_reference_apps.txt").write_text("\n".join(REFERENCE_PANEL_APPS) + "\n", encoding="utf-8")


def ensure_reference_desktop_content() -> None:
    ensure_reference_desktop_shortcuts()
    ensure_reference_desktop_items_manifest()
    ensure_reference_panel_manifest()


def panel_scene_summary() -> str:
    return ", ".join(REFERENCE_PANEL_APPS)


def desktop_scene_summary() -> str:
    return ", ".join(REFERENCE_DESKTOP_ITEMS)


def standard_scene_human_summary() -> str:
    return f"Panel apps: {panel_scene_summary()} | Desktop items: {desktop_scene_summary()}"


def reference_scene_notes_text() -> str:
    return SCENE_NOTES + "\nBasic KDE panel/desktop reference: " + standard_scene_human_summary() + "\n"


def desktop_and_panel_state_payload() -> dict:
    return {"panel_apps": REFERENCE_PANEL_APPS, "desktop_items": REFERENCE_DESKTOP_ITEMS,
            "desktop_shortcuts": REFERENCE_DESKTOP_SHORTCUTS}


def extended_scene_payload() -> dict:
    payload = desktop_and_panel_state_payload()
    payload["summary"] = standard_scene_human_summary()
    return payload


def scene_metadata_payload(category: str) -> dict:
    data = extended_scene_payload()
    data["category"] = category
    return data


def write_scene_notes() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "scene_notes.txt").write_text(reference_scene_notes_text(), encoding="utf-8")


def write_standard_scene_readme() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / "standard_scene.txt").write_text(
        f"Standard KDE reference scene\nPanel apps: {panel_scene_summary()}\nDesktop items: {desktop_scene_summary()}\n",
        encoding="utf-8",
    )


def write_scene_metadata(category: str) -> None:
    import json
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"scene_{category}.json").write_text(json.dumps(scene_metadata_payload(category), indent=2), encoding="utf-8")
