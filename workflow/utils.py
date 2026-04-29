"""workflow/utils.py — Shared utilities used across multiple workflow nodes."""
from __future__ import annotations


def css_braces_balanced(text: str) -> bool:
    """Return True if CSS braces are balanced outside string literals and comments.

    A naive ``text.count('{') == text.count('}')`` check fails when braces
    appear inside string literals (e.g. ``content: "{ icon }"``) or inside
    block comments.  This function skips both regions before counting, making
    it safe for all valid CSS including Jinja2-templated files.
    """
    opens = closes = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in ('"', "'"):
            # Skip over string literal — honour backslash escapes
            quote = ch
            i += 1
            while i < n:
                c = text[i]
                if c == "\\":
                    i += 2  # escaped char: skip both the \ and the next char
                    continue
                if c == quote:
                    break
                i += 1
        elif ch == "/" and i + 1 < n and text[i + 1] == "*":
            # Skip block comment  /* … */
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2  # skip closing */
            continue
        elif ch == "{":
            opens += 1
        elif ch == "}":
            closes += 1
        i += 1
    return opens == closes


def strip_jsonc_comments(text: str) -> str:
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
