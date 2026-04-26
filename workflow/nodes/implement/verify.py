"""implement/verify.py — File-level checks after ricer.py has run."""
from __future__ import annotations

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

    palette_match = True
    for written in result["files_written"]:
        try:
            content = Path(written).read_text(errors="ignore")
            for key in spec.get("palette_keys", []):
                color = design.get("palette", {}).get(key, "")
                if color and color.lower() not in content.lower():
                    palette_match = False
                    break
        except Exception:
            pass

    result["palette_match"] = palette_match
    return result
