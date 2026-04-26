"""implement/score.py — 5-category scorecard for one implemented element."""
from __future__ import annotations

import json
import re
from pathlib import Path

CATEGORIES = ["palette", "shape", "diegesis", "usability", "preview_match"]


def score_element(element: str, spec: dict, design: dict, verify: dict) -> dict:
    """Return a scorecard dict with scores 0-2 per category and a total (max 10)."""
    sc: dict[str, int] = {}

    files_written = len(verify.get("files_written", []))
    files_missing = len(verify.get("files_missing", []))
    palette_match = verify.get("palette_match", False)

    # palette — are palette colors present in the written files?
    if files_written == 0:
        sc["palette"] = 0
    elif palette_match:
        sc["palette"] = 2
    else:
        sc["palette"] = 1

    # shape — did files get written and are they non-trivially sized?
    if files_missing > 0 and files_written == 0:
        sc["shape"] = 0
    elif files_written > 0:
        all_ok = all(
            Path(f).expanduser().stat().st_size > 20
            for f in verify.get("files_written", [])
            if Path(f).expanduser().exists()
        )
        sc["shape"] = 2 if all_ok else 1
    else:
        sc["shape"] = 1

    # diegesis — does the element fit the design? (heuristic: files exist)
    sc["diegesis"] = 2 if files_written > 0 else 0

    # usability — no syntax errors in written files
    sc["usability"] = 2 if _syntax_ok(verify.get("files_written", [])) else 1

    # preview_match — correct palette keys used and files written
    sc["preview_match"] = 2 if (palette_match and files_written > 0) else 1

    sc["total"] = sum(v for k, v in sc.items() if k != "total")
    return sc


def format_scorecard(sc: dict) -> str:
    return " ".join(f"{k}={v}" for k, v in sc.items() if k != "total")


def _syntax_ok(files: list[str]) -> bool:
    for f in files:
        p = Path(f).expanduser()
        if not p.exists():
            continue
        if p.suffix in (".json", ".jsonc"):
            try:
                content = re.sub(r"//.*", "", p.read_text())
                json.loads(content)
            except Exception:
                return False
    return True
