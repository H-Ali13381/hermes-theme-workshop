"""implement/score.py — 5-category scorecard for one implemented element."""
from __future__ import annotations

import json
import re
from pathlib import Path

from ...logging import get_logger
from ...utils import strip_jsonc_comments as _strip_jsonc_comments
from ...utils import css_braces_balanced as _css_braces_balanced

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
    if files_written == 0:
        # No files written at all (either nothing expected, or everything missing).
        sc["shape"] = 0
    else:
        existing_sizes = [
            Path(f).expanduser().stat().st_size
            for f in verify.get("files_written", [])
            if Path(f).expanduser().exists()
        ]
        all_ok = bool(existing_sizes) and all(s > 20 for s in existing_sizes)
        sc["shape"] = 2 if all_ok else 1

    # diegesis — does the element fit the design? (heuristic: files exist)
    sc["diegesis"] = 2 if files_written > 0 else 0

    # usability — no syntax errors in written files
    sc["usability"] = 2 if _syntax_ok(verify.get("files_written", [])) else 1

    # preview_match — correct palette keys used and files written.
    # Previously this was floored at 1, meaning a completely failed element
    # could never score 0 here.  A correct floor is 0.
    if palette_match and files_written > 0:
        sc["preview_match"] = 2
    elif files_written > 0:
        sc["preview_match"] = 1
    else:
        sc["preview_match"] = 0

    # Effective-state gate: a KDE colorscheme file existing is not enough if KDE
    # is actively using a different scheme.
    if verify.get("active_match") is False:
        sc["usability"] = min(sc["usability"], 1)
        sc["preview_match"] = 0

    sc["total"] = sum(v for k, v in sc.items() if k != "total")
    return sc


def format_scorecard(sc: dict) -> str:
    return " ".join(f"{k}={v}" for k, v in sc.items() if k != "total")


def _syntax_ok(files: list[str]) -> bool:
    for f in files:
        p = Path(f).expanduser()
        if not p.exists():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False

        if p.suffix in (".json", ".jsonc"):
            try:
                json.loads(_strip_jsonc_comments(text))
            except Exception:
                return False

        elif p.suffix == ".toml":
            try:
                import tomllib  # Python 3.11+
                tomllib.loads(text)
            except ImportError:
                get_logger("implement.score").warning("tomllib unavailable; skipping TOML validation for %s", p.name)
            except Exception:
                return False

        elif p.suffix == ".css":
            if not _css_braces_balanced(text):
                return False

    return True
