"""KDE/Plasma post-implementation finalization.

This module keeps KDE cleanup deterministic so agents do not improvise after the
core element queue completes.  Only safe/idempotent actions belong here; config
mutation with rollback requirements should remain in materializers.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_TERMINAL_PROCESS_NAMES = {"kitty", "konsole", "alacritty", "wezterm", "foot"}


def finalize_kde(state: dict, reloaded: list[str], errors: list[str]) -> list[dict]:
    """Run conservative KDE finalization actions and return action records."""
    profile = state.get("device_profile", {})
    wm = str(profile.get("wm") or profile.get("desktop_recipe") or "").lower()
    if "kde" not in wm and "plasma" not in wm:
        return []

    actions: list[dict] = []
    impl_log = state.get("impl_log", [])
    elements = {str(r.get("element", "")) for r in impl_log}
    design = state.get("design", {})
    home = Path.home()

    _ensure_fastfetch_compat(home, elements, actions, errors)
    _reload_kitty(elements, actions, reloaded, errors)
    _reapply_colorscheme(home, design, elements, actions, reloaded, errors)
    _apply_wallpaper(design, actions, reloaded, errors)
    _reconfigure_kwin_for_cursor(elements, actions, reloaded, errors)
    _check_plasmashell(actions, errors)
    return actions


def _run(cmd: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str] | None:
    if _forbidden_command_reason(cmd):
        return None
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _forbidden_command_reason(cmd: list[str]) -> str | None:
    """Return a reason when a cleanup command is unsafe to execute."""
    if not cmd:
        return "empty command"
    base = Path(cmd[0]).name
    args = cmd[1:]
    if base == "kwin_wayland" and "--replace" in args:
        return "raw kwin_wayland --replace is forbidden; use a safe wrapper"
    if base in {"pkill", "killall"}:
        targets = {arg for arg in args if not arg.startswith("-")}
        if targets & _TERMINAL_PROCESS_NAMES:
            return "broad terminal process signal is forbidden"
    return None


def _record(actions: list[dict], name: str, status: str, **extra) -> None:
    actions.append({"app": "kde_finalize", "action": name, "status": status, **extra})


def _ensure_fastfetch_compat(home: Path, elements: set[str], actions: list[dict], errors: list[str]) -> None:
    if "fastfetch" not in elements:
        return
    cfg = home / ".config" / "fastfetch" / "config.jsonc"
    compat = home / ".config" / "fastfetch" / "config.json"
    if not cfg.exists():
        _record(actions, "fastfetch-compat", "skipped", reason="config.jsonc missing")
        return
    try:
        if compat.is_symlink() and compat.readlink() == Path("config.jsonc"):
            _record(actions, "fastfetch-compat", "already-ok", path=str(compat))
            return
        if compat.exists() or compat.is_symlink():
            _record(actions, "fastfetch-compat", "skipped", reason="config.json exists and is not managed")
            return
        compat.symlink_to(Path("config.jsonc"))
        _record(actions, "fastfetch-compat", "ok", path=str(compat), target="config.jsonc")
    except OSError as exc:
        errors.append(f"fastfetch compat symlink failed: {exc}")
        _record(actions, "fastfetch-compat", "error", error=str(exc))


def _reload_kitty(elements: set[str], actions: list[dict], reloaded: list[str], errors: list[str]) -> None:
    if "terminal:kitty" not in elements:
        return
    _record(
        actions,
        "kitty-reload",
        "deferred",
        reason="live reload would require signalling terminal processes; config applies on next launch",
    )


def _reapply_colorscheme(home: Path, design: dict, elements: set[str], actions: list[dict], reloaded: list[str], errors: list[str]) -> None:
    if "window_decorations:kde" not in elements or not shutil.which("plasma-apply-colorscheme"):
        return
    scheme = f"hermes-{design.get('name', 'ricer')}"
    scheme_path = home / ".local" / "share" / "color-schemes" / f"{scheme}.colors"
    if not scheme_path.exists():
        _record(actions, "colorscheme-reapply", "skipped", scheme=scheme, reason="scheme file missing")
        return
    r = _run(["plasma-apply-colorscheme", scheme])
    if r and r.returncode == 0:
        reloaded.append("kde-colorscheme")
        _record(actions, "colorscheme-reapply", "ok", scheme=scheme)
    else:
        errors.append(f"plasma-apply-colorscheme failed for {scheme}")
        _record(actions, "colorscheme-reapply", "error", scheme=scheme)


def _apply_wallpaper(design: dict, actions: list[dict], reloaded: list[str], errors: list[str]) -> None:
    raw = design.get("wallpaper_path") or design.get("wallpaper")
    if not raw or not shutil.which("plasma-apply-wallpaperimage"):
        return
    path = Path(str(raw).replace("file://", "")).expanduser()
    if not path.exists():
        _record(actions, "wallpaper-apply", "skipped", path=str(path), reason="local file missing")
        return
    r = _run(["plasma-apply-wallpaperimage", str(path)])
    if r and r.returncode == 0:
        reloaded.append("kde-wallpaper")
        _record(actions, "wallpaper-apply", "ok", path=str(path))
    else:
        errors.append(f"plasma-apply-wallpaperimage failed for {path}")
        _record(actions, "wallpaper-apply", "error", path=str(path))


def _reconfigure_kwin_for_cursor(elements: set[str], actions: list[dict], reloaded: list[str], errors: list[str]) -> None:
    if "cursor_theme" not in elements or not shutil.which("qdbus6"):
        return
    r = _run(["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"], timeout=5)
    if r and r.returncode == 0:
        reloaded.append("kwin-reconfigure")
        _record(actions, "kwin-reconfigure", "ok")
    else:
        errors.append("KWin reconfigure failed after cursor theme apply")
        _record(actions, "kwin-reconfigure", "error")


def _check_plasmashell(actions: list[dict], errors: list[str]) -> None:
    r = _run(["pgrep", "-x", "plasmashell"], timeout=5)
    if r and r.returncode == 0:
        _record(actions, "plasmashell-health", "ok", pids=r.stdout.split())
    else:
        errors.append("plasmashell is not running after cleanup")
        _record(actions, "plasmashell-health", "error")