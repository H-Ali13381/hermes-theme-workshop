"""Read-only effective desktop state audit for cleanup/handoff."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

_KITTY_COLOR_KEYS = {
    "background", "foreground", "cursor", "cursor_text_color", "url_color",
    "selection_background", "selection_foreground", "active_tab_background",
    "active_tab_foreground", "inactive_tab_background", "inactive_tab_foreground",
    "tab_bar_background", *{f"color{i}" for i in range(16)},
}


def audit_effective_state(state: dict) -> dict:
    """Return a read-only snapshot of the visible/effective state after apply."""
    profile = state.get("device_profile", {})
    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "").lower()
    if "kde" not in wm and "plasma" not in wm:
        return {}
    home = Path.home()
    return {
        "desktop": "kde",
        "kde": _audit_kde(home),
        "konsole": _audit_konsole(home),
        "kitty": _audit_kitty(home),
        "fastfetch": _audit_fastfetch(home),
        "processes": _audit_processes(),
    }


def _run(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return -1, ""


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _section_key(text: str, section: str, key: str) -> str | None:
    m = re.search(rf"^\[{re.escape(section)}\]\s*$(.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return None
    km = re.search(rf"^{re.escape(key)}\s*=\s*(.+)$", m.group(1), re.MULTILINE)
    return km.group(1).strip() if km else None


def _kread(file: str, group: str, key: str, home: Path) -> str | None:
    for tool in ("kreadconfig6", "kreadconfig5"):
        rc, out = _run([tool, "--file", file, "--group", group, "--key", key])
        if rc == 0 and out:
            return out
    return _section_key(_read(home / ".config" / file), group, key)


def _audit_kde(home: Path) -> dict:
    appletsrc = _read(home / ".config" / "plasma-org.kde.plasma.desktop-appletsrc")
    wallpaper = None
    m = re.search(r"^Image\s*=\s*(.+)$", appletsrc, re.MULTILINE)
    if m:
        wallpaper = m.group(1).strip()
    return {
        "colorscheme": _kread("kdeglobals", "General", "ColorScheme", home),
        "cursor_kcminputrc": _kread("kcminputrc", "Mouse", "cursorTheme", home),
        "cursor_kdeglobals": _kread("kdeglobals", "General", "cursorTheme", home),
        "wallpaper": wallpaper,
    }


def _audit_konsole(home: Path) -> dict:
    konsolerc = _read(home / ".config" / "konsolerc")
    default_profile = _section_key(konsolerc, "Desktop Entry", "DefaultProfile")
    result = {"default_profile": default_profile, "colorscheme": None, "profile_path": None}
    if not default_profile:
        return result
    profile_path = home / ".local" / "share" / "konsole" / Path(default_profile).name
    result["profile_path"] = str(profile_path)
    result["colorscheme"] = _section_key(_read(profile_path), "Appearance", "ColorScheme")
    return result


def _parse_kitty_palette(text: str) -> dict[str, str]:
    palette = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(maxsplit=1)
        if len(parts) == 2 and parts[0] in _KITTY_COLOR_KEYS:
            palette[parts[0]] = parts[1].split()[0]
    return palette


def _audit_kitty(home: Path) -> dict:
    kitty_dir = home / ".config" / "kitty"
    main = _read(kitty_dir / "kitty.conf")
    theme = _read(kitty_dir / "theme.conf")
    includes_theme = any(line.strip().startswith("include theme.conf") for line in main.splitlines())
    theme_palette = _parse_kitty_palette(theme)
    main_palette = _parse_kitty_palette(main)
    return {
        "include_theme_conf": includes_theme,
        "main_palette_keys": sorted(main_palette),
        "theme_palette_keys": sorted(theme_palette),
        "effective_palette": theme_palette if includes_theme and theme_palette else main_palette,
    }


def _audit_fastfetch(home: Path) -> dict:
    cfg = home / ".config" / "fastfetch" / "config.jsonc"
    compat = home / ".config" / "fastfetch" / "config.json"
    target = str(compat.readlink()) if compat.is_symlink() else None
    return {
        "config_jsonc_exists": cfg.exists(),
        "config_json_exists": compat.exists() or compat.is_symlink(),
        "config_json_is_symlink": compat.is_symlink(),
        "config_json_target": target,
        "compat_ok": cfg.exists() and compat.is_symlink() and target == "config.jsonc",
    }


def _audit_processes() -> dict:
    result = {}
    for name in ("plasmashell", "kwin_wayland", "kwin_x11"):
        rc, out = _run(["pgrep", "-x", name])
        result[name] = {"running": rc == 0, "pids": out.split() if out else []}
    return result