"""Step 8 — Generate handoff.md + handoff.html documenting every change."""
from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from ..config import get_llm
from ..log_setup import get_logger
from ..session import mark_complete
from ..state import RiceSessionState

SYSTEM_PROMPT = """\
You are writing the final session handoff document for a Linux desktop rice.
Given the design_system JSON and the implementation log, produce a complete \
handoff document in Markdown.

Structure:
# [Theme Name] — Rice Handoff

## Design
- Stance, mood, reference anchor
- Palette table (slot | hex | role)

## What Changed
Table: Element | Files Modified | Verdict | Score

## How to Rollback
`ricer undo` — restores all files to pre-session state

## Changed Hotkeys / Behaviors
List any new keybindings added or changed during the session.

## Known Deviations
List any elements that scored below 8/10 or were skipped, with reason.

Be concise and practical. This is a reference document the user will keep.
"""


def handoff_node(state: RiceSessionState) -> dict:
    """Generate handoff.md and handoff.html from the session data."""
    log = get_logger("handoff", state)
    log.info("generating handoff documentation")

    design = state.get("design", {})
    impl_log = state.get("impl_log", [])
    session_dir = state.get("session_dir", "")

    # Generate markdown via LLM
    llm = get_llm(0.1)
    payload = {
        "design": design,
        "implementation_log": impl_log,
        "cleanup_actions": state.get("cleanup_actions", []),
        "effective_state": state.get("effective_state", {}),
        "capability_report": state.get("capability_report", {}),
        "visual_artifacts": state.get("visual_artifacts", []),
        "errors": state.get("errors", []),
    }
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Session data:\n```json\n{json.dumps(payload, indent=2)}\n```"),
    ])

    md_content = (response.content or "").strip()
    html_content = _md_to_html(md_content, design)

    # Write files
    if session_dir:
        md_path = Path(session_dir) / "handoff.md"
        html_path = Path(session_dir) / "handoff.html"
        for dest, content in ((md_path, md_content), (html_path, html_content)):
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", dir=dest.parent, encoding="utf-8", delete=False, suffix=".tmp"
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                Path(tmp_path).replace(dest)
            except Exception:
                if tmp_path:
                    Path(tmp_path).unlink(missing_ok=True)
                raise
        log.info("handoff.md   → %s", md_path)
        log.info("handoff.html → %s", html_path)

        # Mark session complete
        mark_complete(session_dir)

    log.info("session complete")
    return {"current_step": 8}


def _md_to_html(md: str, design: dict) -> str:
    """Convert markdown to a styled HTML document."""
    bg = design.get("palette", {}).get("background", "#1a1a2e")
    fg = design.get("palette", {}).get("foreground", "#e0e0e0")
    primary = design.get("palette", {}).get("primary", "#7ad4f0")
    surface = design.get("palette", {}).get("surface", "#1c1e2a")

    # Minimal markdown→HTML conversion
    def _convert_table(match: re.Match) -> str:
        """Convert a Markdown pipe table block to an HTML <table>."""
        lines = [line.strip() for line in match.group(0).strip().splitlines()]
        rows = [line for line in lines if not re.match(r"^\|[-| :]+\|$", line)]
        html_rows = []
        for i, row in enumerate(rows):
            cells = [c.strip() for c in row.strip("|").split("|")]
            tag = "th" if i == 0 else "td"
            html_rows.append(
                "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"
            )
        return "<table>" + "".join(html_rows) + "</table>"

    body = md
    # Tables: a block of consecutive |-lines that contains a separator row
    # (|---|---|). Requiring the separator prevents matching code-block lines
    # that happen to contain pipe characters (e.g. `cat foo | grep bar`).
    body = re.sub(
        r"(?:(?:\|.+\n)*\|[-| :]+\|\n(?:\|.+\n)*)+",
        _convert_table,
        body,
    )
    body = re.sub(r"^# (.+)$", r"<h1>\1</h1>", body, flags=re.MULTILINE)
    body = re.sub(r"^## (.+)$", r"<h2>\1</h2>", body, flags=re.MULTILINE)
    body = re.sub(r"^### (.+)$", r"<h3>\1</h3>", body, flags=re.MULTILINE)
    body = re.sub(r"`([^`]+)`", r"<code>\1</code>", body)
    body = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", body)
    # Split on code fences so paragraph tags don't get inserted inside them
    parts = re.split(r"(```[\s\S]*?```)", body)
    converted = []
    for part in parts:
        if part.startswith("```"):
            converted.append(part)
        else:
            converted.append(part.replace("\n\n", "</p><p>"))
    body = "".join(converted)
    body = f"<p>{body}</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{design.get('name','Rice')} — Handoff</title>
<style>
  body {{ background:{bg}; color:{fg}; font-family:monospace; max-width:800px;
          margin:40px auto; padding:0 20px; line-height:1.6; }}
  h1,h2,h3 {{ color:{primary}; }}
  code {{ background:{surface}; padding:2px 6px; border-radius:4px; }}
  table {{ border-collapse:collapse; width:100%; }}
  th,td {{ border:1px solid {primary}44; padding:8px 12px; text-align:left; }}
  th {{ background:{surface}; color:{primary}; }}
</style>
</head>
<body>
{body}
</body>
</html>"""
