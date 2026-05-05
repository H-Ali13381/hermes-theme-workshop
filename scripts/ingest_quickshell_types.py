#!/usr/bin/env python3
"""Ingest Quickshell type docs into a local source-of-truth snapshot.

The online docs are the canonical reference; this script creates a pinned,
reviewable local snapshot that craft/widget codegen can load without relying on
live web access during a rice run.
"""
from __future__ import annotations

import argparse
import datetime as dt
from html.parser import HTMLParser
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

BASE_URL = "https://quickshell.org"
DEFAULT_VERSION = "v0.3.0"
USER_AGENT = "linux-ricing-quickshell-doc-ingest/1.0"

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "references" / "quickshell-v0.3.0-types"

CRITICAL_TYPES = {
    "Quickshell/ShellRoot",
    "Quickshell/PanelWindow",
    "Quickshell/PopupWindow",
    "Quickshell/FloatingWindow",
    "Quickshell/QsWindow",
    "Quickshell/ExclusionMode",
    "Quickshell/Edges",
    "Quickshell.Io/Process",
    "Quickshell.Services.SystemTray/SystemTray",
    "Quickshell.Services.SystemTray/SystemTrayItem",
    "Quickshell.Services.Notifications/NotificationServer",
    "Quickshell.Services.Notifications/Notification",
    "Quickshell.Services.Mpris/Mpris",
    "Quickshell.Services.Mpris/MprisPlayer",
    "Quickshell.Services.UPower/UPower",
    "Quickshell.Services.Pipewire/Pipewire",
    "Quickshell.Widgets/IconImage",
    "Quickshell.Widgets/WrapperMouseArea",
    "Quickshell.Wayland/WlrLayer",
    "Quickshell.Wayland/WlrLayershell",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self._href = href
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            text = " ".join("".join(self._text).split())
            self.links.append((self._href, text))
            self._href = None
            self._text = []


class MarkdownParser(HTMLParser):
    """Small dependency-free HTML-to-Markdown converter for docs snapshots."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._href_stack: list[str | None] = []
        self._skip_depth = 0
        self._pre_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "svg"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        attrs_dict = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4"}:
            level = int(tag[1])
            self._append("\n" + "#" * level + " ")
        elif tag == "p":
            self._append("\n")
        elif tag == "li":
            self._append("\n* ")
        elif tag == "br":
            self._append("\n")
        elif tag == "code":
            self._append("`")
        elif tag == "pre":
            self._pre_depth += 1
            self._append("\n```\n")
        elif tag == "a":
            self._href_stack.append(attrs_dict.get("href"))
            self._append("[")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "svg"}:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "p", "li", "section", "article", "div"}:
            self._append("\n")
        elif tag == "code":
            self._append("`")
        elif tag == "pre":
            self._pre_depth = max(0, self._pre_depth - 1)
            self._append("\n```\n")
        elif tag == "a":
            href = self._href_stack.pop() if self._href_stack else None
            self._append("]("
                         + href
                         + ")" if href else "]")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._pre_depth:
            self._append(data)
        else:
            text = " ".join(data.split())
            if text:
                self._append(text + " ")

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"

    def _append(self, text: str) -> None:
        self.parts.append(text)


def fetch_text(url: str, *, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed public docs URL by default
        return response.read().decode("utf-8", "replace")


def markdown_from_html(html: str) -> str:
    parser = MarkdownParser()
    parser.feed(html)
    return parser.markdown()


def clean_markdown_page(markdown: str, type_name: str) -> str:
    """Remove duplicated site navigation and retain the actual type page body."""
    patterns = [
        rf"^##\s+{re.escape(type_name)}\b.*$",
        rf"^##\s+.*\b{re.escape(type_name)}\b.*$",
    ]
    starts: list[int] = []
    for pattern in patterns:
        starts.extend(match.start() for match in re.finditer(pattern, markdown, re.MULTILINE))
    if starts:
        body = markdown[max(starts) :]
    else:
        breadcrumb = f"6. [ {type_name} ]"
        idx = markdown.rfind(breadcrumb)
        body = markdown[idx:] if idx >= 0 else markdown
    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"


def type_rel_from_url(url: str, version: str) -> str | None:
    path = urlparse(url).path.rstrip("/")
    prefix = f"/docs/{version}/types/"
    if not path.startswith(prefix):
        return None
    rel = path[len(prefix) :]
    if not rel or "/" not in rel:
        return None
    return rel


def extract_index_links(index_html: str, version: str) -> tuple[list[str], list[str]]:
    parser = LinkParser()
    parser.feed(index_html)
    modules: set[str] = set()
    types: set[str] = set()
    prefix = f"/docs/{version}/types/"
    for href, _text in parser.links:
        absolute = urljoin(BASE_URL, href)
        path = urlparse(absolute).path.rstrip("/")
        if not path.startswith(prefix):
            continue
        rel = path[len(prefix) :]
        if not rel:
            continue
        if "/" in rel:
            types.add(rel)
            modules.add(rel.split("/", 1)[0])
        else:
            modules.add(rel)
    return sorted(modules), sorted(types)


def extract_properties(markdown: str) -> list[dict[str, str]]:
    section = _section(markdown, "Properties")
    properties: list[dict[str, str]] = []
    for raw_line in section.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line.startswith("* "):
            continue
        match = re.match(r"\*\s+([A-Za-z_][\w-]*)\s*:\s*(.+?)(?:\s{2,}|$)(.*)", line)
        if not match:
            continue
        name, type_text, description = match.groups()
        properties.append({
            "name": name,
            "type": _strip_md_links(type_text).strip(),
            "description": _strip_md_links(description).strip(),
        })
    return properties


def extract_functions(markdown: str) -> list[dict[str, str]]:
    section = _section(markdown, "Functions") or _section(markdown, "Methods")
    functions: list[dict[str, str]] = []
    for raw_line in section.splitlines():
        line = " ".join(raw_line.strip().split())
        if not line.startswith("* "):
            continue
        match = re.match(r"\*\s+`?([A-Za-z_][\w-]*)`?\s*(?:\((.*?)\))?\s*(.*)", line)
        if match:
            name, args, description = match.groups()
            functions.append({"name": name, "args": args or "", "description": _strip_md_links(description).strip()})
    return functions


def extract_variants(markdown: str) -> list[str]:
    section = _section(markdown, "Variants") or _section(markdown, "Values")
    variants: list[str] = []
    seen: set[str] = set()
    for raw_line in section.splitlines():
        line = " ".join(raw_line.strip().split())
        if line.startswith("* "):
            value = _strip_md_links(line[2:]).strip()
            if value and value not in seen:
                variants.append(value)
                seen.add(value)
    return variants


def _section(markdown: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\b.*$", markdown, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    next_heading = re.search(r"^##\s+", markdown[match.end() :], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(markdown)
    return markdown[match.end() : end]


def _strip_md_links(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = text.replace("`", "")
    return text


def parse_type_page(rel: str, url: str, markdown: str) -> dict[str, Any]:
    module, type_name = rel.split("/", 1)
    title_match = re.search(r"^##\s+(.+)$", markdown, re.MULTILINE)
    title = _strip_md_links(title_match.group(1)).strip() if title_match else type_name
    import_match = re.search(r"`import\s+([^`]+)`", markdown)
    imports = import_match.group(1).strip() if import_match else module
    desc = ""
    if import_match:
        after = markdown[import_match.end() :]
        for line in after.splitlines():
            line = _strip_md_links(line).strip()
            if not line or line.startswith("#") or line.startswith("*"):
                continue
            if line.endswith("{") or line in {"}", "```"}:
                continue
            desc = line
            break
    return {
        "name": type_name,
        "module": module,
        "qualified_name": f"{module}.{type_name}" if not module.endswith(type_name) else module,
        "import": imports,
        "url": url,
        "markdown_path": f"pages/{module}/{type_name}.md",
        "title": title,
        "description": desc,
        "properties": extract_properties(markdown),
        "functions": extract_functions(markdown),
        "variants": extract_variants(markdown),
    }


def write_summary(out_dir: Path, index: dict[str, Any]) -> None:
    by_rel = {f"{entry['module']}/{entry['name']}": entry for entry in index["types"]}
    lines = [
        "# Quickshell v0.3.0 Type Docs Source of Truth",
        "",
        "This directory is a pinned local snapshot of https://quickshell.org/docs/v0.3.0/types/.",
        "Use it when generating, editing, statically validating, or reviewing Quickshell QML.",
        "",
        "Machine-readable index: `index.json`.",
        "Full scraped Markdown pages: `pages/<module>/<type>.md`.",
        "Refresh command: `python3 scripts/ingest_quickshell_types.py --version v0.3.0`.",
        "",
        "## Non-negotiable linux-ricing rules",
        "",
        "- Use `PanelWindow` for bars, launchers, notification/quest cards, menus, HUDs, and visually floating shell widgets.",
        "- Do not use `FloatingWindow` for KDE/Wayland shell chrome; it can appear as a decorated app window.",
        "- Use `PopupWindow` for child popups/menus anchored to another item/window, not for the root panel surface.",
        "- Use `Quickshell.Io.Process` with argv arrays for command actions when possible; reject hidden shell-string interpolation unless explicitly required.",
        "- Keep preview-texture artifacts non-promotable; this docs source is for component-mode QML correctness.",
        "",
        "## Critical types for widget/dashboard generation",
        "",
    ]
    for rel in sorted(CRITICAL_TYPES):
        entry = by_rel.get(rel)
        if not entry:
            continue
        props = ", ".join(prop["name"] for prop in entry.get("properties", [])[:12])
        variants = ", ".join(entry.get("variants", [])[:12])
        lines.append(f"### {rel}")
        lines.append("")
        lines.append(f"- Import: `{entry.get('import', '')}`")
        lines.append(f"- URL: {entry['url']}")
        if entry.get("description"):
            lines.append(f"- Description: {entry['description']}")
        if props:
            lines.append(f"- Properties: {props}")
        if variants:
            lines.append(f"- Variants: {variants}")
        lines.append(f"- Snapshot: `{entry['markdown_path']}`")
        lines.append("")
    out_dir.joinpath("summary.md").write_text("\n".join(lines), encoding="utf-8")


def ingest(version: str, out_dir: Path, *, limit: int | None = None, delay: float = 0.05) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    index_url = f"{BASE_URL}/docs/{version}/types/"
    index_html = fetch_text(index_url)
    modules, type_rels = extract_index_links(index_html, version)
    if limit is not None:
        type_rels = type_rels[:limit]

    entries: list[dict[str, Any]] = []
    for rel in type_rels:
        module, type_name = rel.split("/", 1)
        url = f"{BASE_URL}/docs/{version}/types/{rel}/"
        html = fetch_text(url)
        md = clean_markdown_page(markdown_from_html(html), type_name)
        page_path = pages_dir / module / f"{type_name}.md"
        page_path.parent.mkdir(parents=True, exist_ok=True)
        page_path.write_text(md, encoding="utf-8")
        entries.append(parse_type_page(rel, url, md))
        if delay:
            time.sleep(delay)

    index = {
        "schema_version": 1,
        "source": "quickshell-docs-types",
        "version": version,
        "base_url": BASE_URL,
        "index_url": index_url,
        "ingested_at_utc": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "module_count": len(modules),
        "type_count": len(entries),
        "modules": modules,
        "critical_types": sorted(CRITICAL_TYPES),
        "types": entries,
    }
    (out_dir / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(out_dir, index)
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=None, help="debug: ingest only the first N type pages")
    parser.add_argument("--delay", type=float, default=0.05, help="polite delay between page fetches")
    args = parser.parse_args()

    index = ingest(args.version, args.out, limit=args.limit, delay=args.delay)
    print(json.dumps({
        "out": str(args.out),
        "version": index["version"],
        "module_count": index["module_count"],
        "type_count": index["type_count"],
        "index_json": str(args.out / "index.json"),
        "summary_md": str(args.out / "summary.md"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
