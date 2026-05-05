"""KDE/Plasma post-implementation finalization.

This module keeps KDE cleanup deterministic so agents do not improvise after the
core element queue completes.  Only safe/idempotent actions belong here; config
mutation with rollback requirements should remain in materializers.
"""
from __future__ import annotations

import os
import re
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
    _reapply_kvantum_theme(home, design, elements, actions, reloaded, errors)
    _apply_wallpaper(state, design, actions, reloaded, errors)
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


def _reapply_kvantum_theme(home: Path, design: dict, elements: set[str], actions: list[dict], reloaded: list[str], errors: list[str]) -> None:
    """Persist the active Kvantum theme after look-and-feel application churn."""
    if "kvantum_theme" not in elements:
        return
    theme = str(design.get("kvantum_theme") or "").strip()
    if not theme:
        _record(actions, "kvantum-reapply", "skipped", reason="design has no kvantum_theme")
        return
    kvconfig = home / ".config" / "Kvantum" / "kvantum.kvconfig"
    try:
        kvconfig.parent.mkdir(parents=True, exist_ok=True)
        kvconfig.write_text(f"[General]\ntheme={theme}\n", encoding="utf-8")
    except OSError as exc:
        errors.append(f"Kvantum theme reapply failed for {theme}: {exc}")
        _record(actions, "kvantum-reapply", "error", theme=theme, error=str(exc))
        return
    if shutil.which("kwriteconfig6"):
        _run(["kwriteconfig6", "--file", "kdeglobals", "--group", "KDE", "--key", "widgetStyle", "kvantum"], timeout=5)
    reloaded.append("kvantum-theme")
    _record(actions, "kvantum-reapply", "ok", theme=theme, path=str(kvconfig))


def _apply_wallpaper(state: dict, design: dict, actions: list[dict], reloaded: list[str], errors: list[str]) -> None:
    raw = _resolve_wallpaper_path(design)
    if not raw:
        return
    path = Path(_expand_wallpaper_path(raw).replace("file://", "")).expanduser()
    preview_url = str(state.get("visualize_image_url") or "")
    if not path.exists() and _wallpaper_declared_in_visual_plan(design):
        _generate_atmospheric_wallpaper(path, design, actions, errors)
    if not path.exists():
        reason = "local wallpaper file missing"
        if preview_url:
            reason = "local wallpaper file missing; desktop preview URL is not a wallpaper source"
            errors.append(f"wallpaper artifact missing for {path}; refusing desktop preview URL as wallpaper")
        _record(actions, "wallpaper-apply", "skipped", path=str(path), reason=reason)
        return
    if not shutil.which("plasma-apply-wallpaperimage"):
        _record(actions, "wallpaper-apply", "skipped", path=str(path), reason="plasma-apply-wallpaperimage missing")
        return
    r = _run(["plasma-apply-wallpaperimage", str(path)])
    if r and r.returncode == 0:
        reloaded.append("kde-wallpaper")
        _record(actions, "wallpaper-apply", "ok", path=str(path))
    else:
        errors.append(f"plasma-apply-wallpaperimage failed for {path}")
        _record(actions, "wallpaper-apply", "error", path=str(path))


def _resolve_wallpaper_path(design: dict) -> str:
    """Find the local wallpaper target promised by the design contract."""
    for key in ("wallpaper_path", "wallpaper"):
        raw = design.get(key)
        if raw:
            return str(raw)

    chrome = design.get("chrome_strategy") if isinstance(design.get("chrome_strategy"), dict) else {}
    for key in ("wallpaper_path", "wallpaper"):
        raw = chrome.get(key)
        if raw:
            return str(raw)

    for target in chrome.get("implementation_targets") or []:
        text = str(target)
        if "wallpaper" not in text.lower():
            continue
        match = re.search(r"(/(?:home/\$USER|home/[^\s:]+|[A-Za-z0-9_.$~-]+)[^\s:]*)", text)
        if match:
            return match.group(1)

    for item in design.get("visual_element_plan") or []:
        if not isinstance(item, dict):
            continue
        if "wallpaper" not in str(item.get("desktop_element", "")).lower():
            continue
        for target in item.get("config_targets") or []:
            text = str(target).strip()
            if not text:
                continue
            if text.endswith(("/", "\\")) or not Path(text).suffix:
                return str(Path(text) / "wallpaper.png")
            if text.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                return text
        slug = str(design.get("name") or design.get("theme_name") or "linux-rice").strip().lower()
        slug = re.sub(r"[^a-z0-9._-]+", "-", slug).strip("-._") or "linux-rice"
        return f"~/.local/share/wallpapers/{slug}/wallpaper.png"
    return ""


def _expand_wallpaper_path(raw: str) -> str:
    user = os.environ.get("USER") or Path.home().name
    return raw.replace("$USER", user).replace("${USER}", user)


def _wallpaper_declared_in_visual_plan(design: dict) -> bool:
    plan = design.get("visual_element_plan") if isinstance(design, dict) else []
    if not isinstance(plan, list):
        return False
    return any(isinstance(item, dict) and "wallpaper" in str(item.get("desktop_element", "")).lower() for item in plan)


def _generate_atmospheric_wallpaper(path: Path, design: dict, actions: list[dict], errors: list[str]) -> None:
    """Generate a local wallpaper artifact instead of using the desktop preview mockup as wallpaper."""
    try:
        from PIL import Image, ImageDraw, ImageFilter  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - depends on optional Pillow availability
        errors.append(f"wallpaper artifact generation unavailable: {exc}")
        _record(actions, "wallpaper-generate", "error", path=str(path), error=str(exc))
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        width, height = 3840, 2160
        palette = design.get("palette", {}) if isinstance(design, dict) else {}
        bg = _hex_to_rgb(str(palette.get("background", "#050607")), (5, 6, 7))
        amber = _hex_to_rgb(str(palette.get("accent", palette.get("primary", "#d78331"))), (215, 131, 49))
        bone = _hex_to_rgb(str(palette.get("foreground", "#d7c9a7")), (215, 201, 167))
        img = Image.new("RGB", (width, height), bg)
        draw = ImageDraw.Draw(img)
        for y in range(height):
            t = y / max(1, height - 1)
            glow = max(0.0, 1.0 - abs(t - 0.68) * 4.8)
            color = tuple(min(255, int(bg[i] * (1 - t * 0.35) + amber[i] * glow * 0.22 + bone[i] * t * 0.04)) for i in range(3))
            draw.line([(0, y), (width, y)], fill=color)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        horizon = int(height * 0.66)
        pts = [(-80, height)]
        for x in range(-80, width + 160, 120):
            y = horizon - int(120 + 80 * ((x // 240) % 3))
            pts.append((x, y))
        pts.append((width + 160, height))
        od.polygon(pts, fill=(1, 3, 4, 220))
        for cx, scale in ((int(width * 0.52), 1.0), (int(width * 0.66), 0.72), (int(width * 0.37), 0.55)):
            ground = int(height * 0.84)
            col = (1, 3, 4, 235)
            od.rectangle([cx - int(42 * scale), ground - int(370 * scale), cx + int(42 * scale), height], fill=col)
            od.polygon([(cx - int(58 * scale), ground - int(370 * scale)), (cx, ground - int(540 * scale)), (cx + int(58 * scale), ground - int(370 * scale))], fill=col)
        for radius, alpha in ((900, 18), (540, 32), (260, 54)):
            od.ellipse([width * 0.50 - radius, height * 0.78 - radius * 0.34, width * 0.50 + radius, height * 0.78 + radius * 0.34], fill=(*amber, alpha))
        overlay = overlay.filter(ImageFilter.GaussianBlur(24))
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
        ed = ImageDraw.Draw(img)
        for i in range(280):
            x = (i * 997) % width
            y = int(height * 0.47 + ((i * 577) % int(height * 0.44)))
            r = 1 + (i % 3 == 0)
            ed.ellipse([x - r, y - r, x + r, y + r], fill=(*amber, 80 + (i % 90)))
        img.convert("RGB").save(path)
        _record(actions, "wallpaper-generate", "ok", path=str(path), reason="visual_element_plan wallpaper artifact")
    except Exception as exc:  # pragma: no cover - exact image errors vary
        errors.append(f"wallpaper artifact generation failed for {path}: {exc}")
        _record(actions, "wallpaper-generate", "error", path=str(path), error=str(exc))


def _hex_to_rgb(value: str, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    if not m:
        return fallback
    raw = m.group(1)
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


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
