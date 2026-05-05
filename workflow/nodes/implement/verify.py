"""implement/verify.py — File-level checks after ricer.py has run."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


def verify_element(element: str, spec: dict, design: dict) -> dict:
    """Check that target files were written and contain expected palette colors."""
    result: dict = {"files_written": [], "files_missing": []}

    for target in spec.get("targets", []):
        path = Path(target).expanduser()
        if path.exists():
            result["files_written"].append(str(path))
        else:
            result["files_missing"].append(str(path))

    for alias in _fallback_targets(element, design):
        if alias.exists() and str(alias) not in result["files_written"]:
            result["files_written"].append(str(alias))
            resolved = [m for m in result["files_missing"] if _fallback_resolves_missing(element, m, alias)]
            if resolved:
                result.setdefault("resolved_missing_targets", {})[str(alias)] = resolved
                result["files_missing"] = [m for m in result["files_missing"] if m not in resolved]

    palette_keys = spec.get("palette_keys", [])
    files_written = result["files_written"]

    # No files written means there is nothing to verify against
    if not files_written:
        result["palette_match"] = False
        return result

    # No palette keys declared → no color requirements, so match is satisfied
    if not palette_keys:
        result["palette_match"] = True
        return result

    combined_content = ""
    for written in files_written:
        written_path = Path(written)
        if written_path.is_dir():
            continue
        try:
            combined_content += "\n" + written_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            result["palette_match"] = False
            return result

    combined_lower = combined_content.lower()
    missing_palette_keys = []
    matched_palette_keys = []
    for key in palette_keys:
        color = design.get("palette", {}).get(key, "")
        if not color:
            continue
        if _palette_color_present(color, combined_lower):
            matched_palette_keys.append(key)
        else:
            missing_palette_keys.append(key)

    result["palette_match"] = not missing_palette_keys
    result["palette_keys_matched"] = matched_palette_keys
    if missing_palette_keys:
        result["palette_keys_missing"] = missing_palette_keys
    if element == "window_decorations:kde":
        _attach_kde_active_colorscheme(result, design)
    return result


def _fallback_targets(element: str, design: dict) -> list[Path]:
    """Known deterministic outputs for specs that used stale filenames."""
    if element == "terminal:kitty":
        kitty_dir = Path.home() / ".config" / "kitty"
        return [kitty_dir / "theme.conf", kitty_dir / "kitty.conf"]
    if element == "launcher:rofi":
        rofi_dir = Path.home() / ".config" / "rofi"
        return [rofi_dir / "hermes-theme.rasi", rofi_dir / "config.rasi"]
    if element == "icon_theme":
        names = [str(design.get("icon_theme") or "").strip(), str(design.get("name") or "").strip()]
        roots: list[Path] = []
        for name in names:
            if not name:
                continue
            for candidate in (name, f"{name}-icons"):
                root = Path.home() / ".local" / "share" / "icons" / candidate
                if root not in roots:
                    roots.append(root)
        targets: list[Path] = []
        for root in roots:
            targets.append(root / "index.theme")
            if root.exists():
                targets.extend(sorted(root.rglob("*.svg"))[:40])
        return targets
    if element == "window_decorations:kde":
        name = design.get("name", "ricer")
        return [Path.home() / ".local" / "share" / "color-schemes" / f"hermes-{name}.colors"]
    if element == "widgets:eww":
        eww_dir = Path.home() / ".config" / "eww"
        return [
            eww_dir / "hermes-palette.scss",
            eww_dir / "hermes-theme.yuck",
            eww_dir / "eww.scss",
            eww_dir / "eww.yuck",
        ]
    if element == "fastfetch":
        fastfetch_dir = Path.home() / ".config" / "fastfetch"
        return [
            fastfetch_dir / "config.jsonc",
            fastfetch_dir / "config.json",
        ]
    return []


def _palette_color_present(color: str, combined_lower: str) -> bool:
    """Match palette colors written either as #rrggbb or KDE r,g,b triplets."""
    color = str(color).strip().lower()
    if not color:
        return False
    if color in combined_lower:
        return True
    m = re.fullmatch(r"#([0-9a-f]{6})", color)
    if not m:
        return False
    raw = m.group(1)
    rgb = ",".join(str(int(raw[i:i + 2], 16)) for i in (0, 2, 4))
    return rgb in combined_lower


def _fallback_resolves_missing(element: str, missing: str, alias: Path) -> bool:
    """Whether a deterministic fallback output satisfies a stale LLM target."""
    missing_path = Path(missing).expanduser()
    if element == "window_decorations:kde":
        return _is_kde_colorscheme_spec(missing)
    if element == "terminal:kitty":
        return ".config" in missing_path.parts and "kitty" in missing_path.parts
    if element == "launcher:rofi":
        return ".config" in missing_path.parts and "rofi" in missing_path.parts
    if element == "icon_theme":
        return ".local" in missing_path.parts and "icons" in missing_path.parts
    if element == "fastfetch":
        return ".config" in missing_path.parts and "fastfetch" in missing_path.parts
    if element == "widgets:eww":
        return ".config" in missing_path.parts and "eww" in missing_path.parts
    return False


def _is_kde_colorscheme_spec(path: str) -> bool:
    p = Path(path).expanduser()
    return p.suffix == ".colors" and "color-schemes" in p.parts


def _attach_kde_active_colorscheme(result: dict, design: dict) -> None:
    expected = f"hermes-{design.get('name', 'ricer')}"
    active = _active_kde_colorscheme()
    if not active:
        return
    result["expected_active_colorscheme"] = expected
    result["active_colorscheme"] = active
    result["active_match"] = active == expected


def _active_kde_colorscheme() -> str | None:
    for tool in ("kreadconfig6", "kreadconfig5"):
        try:
            r = subprocess.run(
                [tool, "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True, encoding="utf-8", timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()

    path = Path.home() / ".config" / "kdeglobals"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"^\[General\]\s*$(.*?)(?=^\[|\Z)", text, re.MULTILINE | re.DOTALL)
    if not m:
        return None
    km = re.search(r"^ColorScheme\s*=\s*(.+)$", m.group(1), re.MULTILINE)
    return km.group(1).strip() if km else None
