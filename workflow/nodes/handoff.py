"""Step 8 — Generate handoff.md + handoff.html documenting every change."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic

from ..config import MODEL, SCRIPTS_DIR
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
    print("[Step 8] Generating handoff documentation...", flush=True)

    design = state.get("design", {})
    impl_log = state.get("impl_log", [])
    session_dir = state.get("session_dir", "")

    # Generate markdown via LLM
    llm = ChatAnthropic(model=MODEL, temperature=0.1)
    payload = {
        "design": design,
        "implementation_log": impl_log,
        "errors": state.get("errors", []),
    }
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Session data:\n```json\n{json.dumps(payload, indent=2)}\n```"),
    ])

    md_content = response.content.strip()
    html_content = _md_to_html(md_content, design)

    # Write files
    if session_dir:
        md_path = Path(session_dir) / "handoff.md"
        html_path = Path(session_dir) / "handoff.html"
        md_path.write_text(md_content, encoding="utf-8")
        html_path.write_text(html_content, encoding="utf-8")
        print(f"  handoff.md   → {md_path}")
        print(f"  handoff.html → {html_path}")

        # Mark session complete
        _complete_session(session_dir)

    print("\nSession complete!\n")
    return {"current_step": 8}


def _md_to_html(md: str, design: dict) -> str:
    """Convert markdown to a styled HTML document."""
    bg = design.get("palette", {}).get("background", "#1a1a2e")
    fg = design.get("palette", {}).get("foreground", "#e0e0e0")
    primary = design.get("palette", {}).get("primary", "#7ad4f0")
    surface = design.get("palette", {}).get("surface", "#1c1e2a")

    # Minimal markdown→HTML conversion
    import re
    body = md
    body = re.sub(r"^# (.+)$", r"<h1>\1</h1>", body, flags=re.MULTILINE)
    body = re.sub(r"^## (.+)$", r"<h2>\1</h2>", body, flags=re.MULTILINE)
    body = re.sub(r"^### (.+)$", r"<h3>\1</h3>", body, flags=re.MULTILINE)
    body = re.sub(r"`([^`]+)`", r"<code>\1</code>", body)
    body = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", body)
    body = re.sub(r"\n\n", "</p><p>", body)
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


def _complete_session(session_dir: str) -> None:
    try:
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "session_manager.py"),
             "complete", "--session-dir", session_dir],
            capture_output=True, timeout=5,
        )
    except Exception:
        pass
