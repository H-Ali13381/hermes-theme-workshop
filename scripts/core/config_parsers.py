"""INI and desktop-config parsing helpers used by snapshots and materializers."""
import configparser
import re
from pathlib import Path


def _ini_section_key(text: str, section_header_pattern: str, key: str) -> str | None:
    """Read *key* from the first INI section whose header matches *section_header_pattern*.

    The search is constrained to within that section's bounds so cross-section
    false-matches are impossible.  *section_header_pattern* is matched with
    re.MULTILINE against the full file text.
    """
    m = re.search(section_header_pattern, text, re.MULTILINE)
    if not m:
        return None
    start = m.end()
    next_section = re.search(r"^\[", text[start:], re.MULTILINE)
    section_text = text[start: start + next_section.start()] if next_section else text[start:]
    km = re.search(rf"^{re.escape(key)}\s*=\s*(.+)$", section_text, re.MULTILINE)
    return km.group(1).strip() if km else None


def _appletsrc_image(text: str) -> str | None:
    """Return the active wallpaper ``Image=`` path from appletsrc.

    Iterates every ``[Containments][N][Wallpaper][plugin][General]`` section
    and returns the *last* image found — the active desktop containment appears
    last in the file.
    """
    image: str | None = None
    section_re = re.compile(
        r"^\[Containments\]\[\d+\]\[Wallpaper\]\[[^\]]+\]\[General\]\s*$",
        re.MULTILINE,
    )
    for m in section_re.finditer(text):
        start = m.end()
        next_section = re.search(r"^\[", text[start:], re.MULTILINE)
        section_text = text[start: start + next_section.start()] if next_section else text[start:]
        img_m = re.search(r"^Image\s*=\s*(.+)$", section_text, re.MULTILINE)
        if img_m:
            image = img_m.group(1).strip()
    return image


def _read_kvantum_theme(path: Path) -> str | None:
    """Return the active Kvantum theme name from *kvantum.kvconfig*.

    Uses configparser so the read is section-aware and case-insensitive.
    Returns None when the file is absent or the key is unset.
    """
    if not path.exists():
        return None
    cp = configparser.ConfigParser(strict=False)
    cp.read_string(path.read_text(encoding="utf-8", errors="replace"))
    return cp.get("General", "theme", fallback=None) or None


def _patch_hypr_conf_key(content: str, key: str, value: str) -> tuple[str, bool]:
    """Rewrite ``key = …`` in a Hyprland block-format conf, skipping comment lines.

    Returns *(new_content, was_found)*.  If the key was not present the
    original content is returned unchanged and *was_found* is False.
    """
    lines = content.splitlines(keepends=True)
    new_lines: list[str] = []
    found = False
    pattern = re.compile(rf"^(\s*{re.escape(key)}\s*=\s*).*$")
    for line in lines:
        if line.lstrip().startswith("#"):
            new_lines.append(line)
            continue
        m = pattern.match(line.rstrip("\n"))
        if m:
            new_lines.append(f"{m.group(1)}{value}\n")
            found = True
        else:
            new_lines.append(line)
    return "".join(new_lines), found


def _hyprlock_background_path(text: str) -> str | None:
    """Return the ``path =`` value from the first ``background { }`` block in
    a hyprlock.conf string.

    Uses brace-counting to stay within the block so ``path =`` keys in
    ``image {}`` or other blocks are not matched.
    """
    m = re.search(r"^\s*background\s*\{", text, re.MULTILINE)
    if not m:
        return None
    i = m.end()
    depth = 1
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    block_text = text[m.end(): i - 1]
    pm = re.search(r"^\s*path\s*=\s*(.+)$", block_text, re.MULTILINE)
    return pm.group(1).strip() if pm else None
