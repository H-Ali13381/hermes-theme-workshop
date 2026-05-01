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
            resolved = [m for m in result["files_missing"] if _is_kde_colorscheme_spec(m)]
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

    palette_match = True
    for written in files_written:
        try:
            content = Path(written).read_text(encoding="utf-8", errors="replace")
            for key in palette_keys:
                color = design.get("palette", {}).get(key, "")
                if color and color.lower() not in content.lower():
                    palette_match = False
                    break
        except OSError:
            palette_match = False

    result["palette_match"] = palette_match
    if element == "window_decorations:kde":
        _attach_kde_active_colorscheme(result, design)
    return result


def _fallback_targets(element: str, design: dict) -> list[Path]:
    """Known deterministic outputs for specs that used stale filenames."""
    if element != "window_decorations:kde":
        return []
    name = design.get("name", "ricer")
    return [Path.home() / ".local" / "share" / "color-schemes" / f"hermes-{name}.colors"]


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
