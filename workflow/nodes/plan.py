"""Step 4 — Generate HTML visual preview. User must open and approve it."""
from __future__ import annotations

import json
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt

from ..config import MODEL
from ..state import RiceSessionState

SYSTEM_PROMPT = """\
You are generating a static HTML mockup for a Linux desktop theme preview.

Given a design_system JSON, produce a complete, self-contained HTML file that shows:
1. A palette board — swatches for all 10 color slots with labels and hex values
2. A terminal window mockup using the palette colors (background, foreground, primary)
3. A status bar mockup (background=surface, text=foreground, accent highlights)
4. A launcher/rofi row mockup
5. The theme name and stance as a header

Requirements:
- Single self-contained HTML file (no external dependencies)
- Use inline CSS with actual hex values from the palette
- Use monospace fonts for terminal areas
- Make it beautiful enough to judge color harmony at a glance
- The body background should be the theme's background color

Output ONLY the HTML — no explanation, no markdown fences.
"""


def plan_node(state: RiceSessionState) -> dict:
    """Generate HTML mockup and wait for user approval."""
    design = state.get("design", {})
    session_dir = state.get("session_dir", "")
    messages = list(state.get("messages", []))

    # Generate HTML if not already done
    html_path = _get_html_path(session_dir)

    if not html_path.exists() or html_path.stat().st_size < 500:
        print("[Step 4] Generating visual preview...", flush=True)
        llm = ChatAnthropic(model=MODEL, temperature=0.2, max_tokens=8192)

        prompt_messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Design system:\n```json\n{json.dumps(design, indent=2)}\n```"),
        ]
        response = llm.invoke(prompt_messages)
        html_content = _extract_html(response.content)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_content, encoding="utf-8")
        print(f"  Preview written: {html_path}\n")

    # Interrupt: ask user to open and approve
    decision = interrupt({
        "step": 4,
        "type": "approval",
        "message": (
            f"Visual preview generated at:\n  {html_path}\n\n"
            "Open it in your browser, then type:\n"
            "  'approve' to proceed\n"
            "  'regenerate' to try again\n"
            "  or describe changes you want"
        ),
    })

    decision_str = str(decision).lower().strip()

    if decision_str == "approve":
        # Update session.md
        _append_step_to_session(session_dir, 4, str(html_path))
        return {
            "plan_html_path": str(html_path),
            "current_step": 4,
        }

    if decision_str == "regenerate":
        # Delete and retry
        html_path.unlink(missing_ok=True)
        return {}  # Graph will re-enter plan_node via conditional edge

    # User wants changes — add feedback to messages and retry
    html_path.unlink(missing_ok=True)
    return {
        "messages": messages + [
            HumanMessage(content=f"Regenerate the preview with these changes: {decision}"),
        ],
    }


def _get_html_path(session_dir: str) -> Path:
    if session_dir:
        return Path(session_dir) / "plan.html"
    return Path.home() / ".config" / "rice-sessions" / "_tmp_plan.html"


def _extract_html(content: str) -> str:
    """Strip markdown fences if the model wrapped the HTML."""
    import re
    content = content.strip()
    # Remove ```html ... ``` wrapping
    match = re.search(r"```(?:html)?\s*(<!DOCTYPE.*?)</?\s*```", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    if content.startswith("<!DOCTYPE") or content.startswith("<html"):
        return content
    # Try to find the HTML block
    start = content.find("<!DOCTYPE")
    if start == -1:
        start = content.find("<html")
    if start != -1:
        return content[start:]
    return content


def _append_step_to_session(session_dir: str, step: int, note: str) -> None:
    import sys, subprocess
    from ..config import SCRIPTS_DIR
    if not session_dir:
        return
    subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "session_manager.py"),
         "append-step", str(step), note, "--session-dir", session_dir],
        capture_output=True,
    )
