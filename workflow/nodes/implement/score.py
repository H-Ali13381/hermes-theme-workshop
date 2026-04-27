"""implement/score.py — 5-category scorecard for one implemented element."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _strip_jsonc_comments(text: str) -> str:
    """Remove // line comments from JSONC text, skipping // inside string literals."""
    result: list[str] = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if in_string:
            if ch == "\\":
                result.append(ch)
                i += 1
                if i < len(text):
                    result.append(text[i])
            elif ch == '"':
                in_string = False
                result.append(ch)
            else:
                result.append(ch)
        else:
            if ch == '"':
                in_string = True
                result.append(ch)
            elif ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue
            else:
                result.append(ch)
        i += 1
    return "".join(result)

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

    # preview_match — correct palette keys used and files written.
    # Previously this was floored at 1, meaning a completely failed element
    # could never score 0 here.  A correct floor is 0.
    if palette_match and files_written > 0:
        sc["preview_match"] = 2
    elif files_written > 0:
        sc["preview_match"] = 1
    else:
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
            text = p.read_text(errors="replace")
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
                print(f"[WARN] tomllib unavailable; skipping TOML validation for {p.name}", file=sys.stderr)
            except Exception:
                return False

        elif p.suffix in (".conf", ".ini", ".cfg"):
            opens  = text.count("{") + text.count("[")
            closes = text.count("}") + text.count("]")
            if opens != closes:
                return False

        elif p.suffix == ".css":
            if text.count("{") != text.count("}"):
                return False

    return True
