"""Step 4 — Generate HTML visual preview. User must open and approve it."""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt

from ..config import (
    get_llm,
    MAX_LOOP_ITERATIONS,
    PLAN_FEEDBACK_CLASSIFIER_PROMPT,
    PLAN_FEEDBACK_LABELS,
    PLAN_FEEDBACK_SUMMARIZER_PROMPT,
    PLAN_FEEDBACK_VERBATIM_TURNS,
)
from ..session import append_step
from ..state import RiceSessionState

# Marker prefixed onto every plan-feedback HumanMessage so subsequent invocations
# of plan_node can identify and re-use prior user critiques without entangling
# them with unrelated conversation turns from explore/refine.
PLAN_FEEDBACK_MARKER = "[PLAN_FEEDBACK] "

SYSTEM_PROMPT = """\
You are generating a static HTML mockup for a Linux desktop theme preview.

Given a design_system JSON, produce a complete, self-contained HTML file that shows a full desktop composition:
1. A palette board — swatches for all 10 color slots with labels and hex values
2. A terminal mockup using the palette colors (background, foreground, primary)
3. A non-stock composition based on originality_strategy and chrome_strategy — never a plain KDE/Breeze toolbar
4. A launcher/rofi row mockup
5. Optional widgets/overlays from widget_layout when they serve the user's vision
6. The theme name and stance as a header

Requirements:
- Single self-contained HTML file (no external dependencies)
- Use inline CSS with actual hex values from the palette
- Use monospace fonts for terminal areas
- Make it beautiful enough to judge color harmony at a glance
- The body background should be the theme's background color
- If this is KDE, the preview must make the originality_strategy obvious enough to reject "palette swap" designs
- Do not center the preview on a generic status bar; make user-specific custom chrome/composition dominate the scene

Preview honesty contract:
- Do NOT draw macOS traffic-light window controls (red/yellow/green circles at the top-left) unless the design explicitly includes an implemented macOS-style window-decoration materializer. This workflow does not currently implement those controls.
- Terminal previews should be frameless, embedded in custom widget chrome, or use Linux/KDE-realistic top-right window controls only.
- Rounded terminal/window corners, custom borders, and ornamental titlebars are allowed only when chrome_strategy declares an implementable method such as eww_frame/custom_overlay/kvantum/terminal_config.
- Never preview app/window chrome that the implementation will not actually change.

Output ONLY the HTML — no explanation, no markdown fences.
"""

_MACOS_TRAFFIC_LIGHT_HEXES = {
    "#ff5f56", "#ff5f57", "#ff605c", "#ff6159",
    "#ffbd2e", "#ffbd44", "#febc2e", "#ffbe2e",
    "#27c93f", "#28c840", "#00ca4e", "#29cc41",
}

_MACOS_CHROME_TERMS = (
    "traffic-light", "traffic light", "trafficlights", "traffic_lights",
    "macos", "mac-os", "mac window", "mac controls", "mac-controls",
    "window-dot", "window dots", "red yellow green",
)


def plan_node(state: RiceSessionState) -> dict:
    """Generate HTML mockup, gather feedback, and dispatch to plan/refine/explore."""
    design = state.get("design", {})
    session_dir = state.get("session_dir", "")
    messages = list(state.get("messages", []))

    # Track invocations so routing.after_plan can abort if the loop diverges.
    loop_counts = dict(state.get("loop_counts") or {})
    loop_counts["plan"] = loop_counts.get("plan", 0) + 1

    feedback_block = _format_feedback_block(_get_feedback_messages(messages))

    html_path = _get_html_path(session_dir)
    if not html_path.exists() or html_path.stat().st_size < 500:
        _render_preview(html_path, design, feedback_block)

    contract_violations = _existing_contract_violations(html_path, design)

    violation_note = ""
    if contract_violations:
        violation_note = (
            "\n\nPREVIEW CONTRACT VIOLATION — do not approve this preview.\n"
            f"Reason: {'; '.join(contract_violations)}\n"
            "Type 'regenerate' so the workflow produces an honest preview."
        )
    decision = interrupt({
        "step": 4,
        "type": "approval",
        "message": (
            f"Visual preview generated at:\n  {html_path}\n\n"
            "Open it in your browser, then type:\n"
            "  'approve' to proceed\n"
            "  'regenerate' to try again\n"
            "  or describe changes you want"
            f"{violation_note}"
        ),
    })

    decision_str = str(decision).strip()
    decision_lower = decision_str.lower()

    if decision_lower == "approve" and contract_violations:
        html_path.unlink(missing_ok=True)
        return {
            "plan_html_path": "",
            "plan_feedback_route": "render",
            "messages": [_make_feedback_message(
                "Regenerate the preview without unimplemented macOS traffic-light chrome."
            )],
            "loop_counts": loop_counts,
        }

    if decision_lower == "approve":
        append_step(session_dir, 4, str(html_path))
        return {
            "plan_html_path": str(html_path),
            "plan_feedback_route": "approve",
            "current_step": 4,
            "loop_counts": loop_counts,
        }

    if decision_lower == "regenerate":
        html_path.unlink(missing_ok=True)
        return {
            "plan_html_path": "",
            "plan_feedback_route": "render",
            "loop_counts": loop_counts,
        }

    # Freeform feedback — classify and dispatch.
    label, reason = _classify_feedback(decision_str)
    if label == "ambiguous":
        clarifier = interrupt({
            "step": 4,
            "type": "approval",
            "message": (
                "Just to be sure I revise the right thing: is this feedback about "
                "(a) the colors / layout / specific design pieces, or "
                "(b) the overall vibe and direction?\n"
                "Reply 'design', 'direction', 'render', or 'approve'."
            ),
        })
        clar_lower = str(clarifier).strip().lower()
        if clar_lower.startswith("approve"):
            label = "approve"
        elif clar_lower.startswith("design") or clar_lower.startswith("refine"):
            label = "refine"
        elif clar_lower.startswith("direction") or clar_lower.startswith("explore"):
            label = "explore"
        else:
            label = "render"
        reason = f"clarified by user: {clar_lower}"

    return _dispatch_feedback(
        label=label,
        reason=reason,
        feedback_text=decision_str,
        html_path=html_path,
        session_dir=session_dir,
        loop_counts=loop_counts,
        explore_intake=dict(state.get("explore_intake") or {}),
        prior_design=design,
    )


def _render_preview(html_path: Path, design: dict, feedback_block: str) -> None:
    """Generate the preview HTML and write it atomically to *html_path*."""
    print("[Step 4] Generating visual preview...", flush=True)
    llm = get_llm(0.2, max_tokens=8192)

    user_content = f"Design system:\n```json\n{json.dumps(design, indent=2)}\n```"
    if feedback_block:
        user_content += f"\n\nUser feedback so far on prior previews:\n{feedback_block}"

    prompt_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]
    response = llm.invoke(prompt_messages)
    html_content = _extract_html(response.content or "")
    contract_violations = _preview_contract_violations(html_content, design)
    if contract_violations:
        print(f"[Plan][WARN] Preview contract violation: {'; '.join(contract_violations)}", file=sys.stderr)
        html_content = _contract_violation_html(design, contract_violations)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=html_path.parent, encoding="utf-8", delete=False, suffix=".tmp"
        ) as tmp:
            tmp.write(html_content)
            tmp_path = tmp.name
        Path(tmp_path).replace(html_path)
    except Exception:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        raise
    print(f"  Preview written: {html_path}\n")


def _get_feedback_messages(messages: list) -> list[str]:
    """Return prior plan-feedback strings (marker stripped) in chronological order."""
    out: list[str] = []
    for msg in messages or []:
        content = getattr(msg, "content", None)
        if not isinstance(content, str):
            continue
        if content.startswith(PLAN_FEEDBACK_MARKER):
            out.append(content[len(PLAN_FEEDBACK_MARKER):].strip())
    return out


def _format_feedback_block(feedback: list[str]) -> str:
    """Verbatim under the threshold; summarize older portion above it."""
    if not feedback:
        return ""
    if len(feedback) <= PLAN_FEEDBACK_VERBATIM_TURNS:
        return "\n".join(f"- {item}" for item in feedback)
    # Keep the most recent 2 turns verbatim; summarize the rest.
    recent = feedback[-2:]
    older = feedback[:-2]
    summary = _summarize_feedback(older)
    parts = []
    if summary:
        parts.append("Earlier feedback (summarized):\n" + summary)
    parts.append("Most recent feedback:\n" + "\n".join(f"- {item}" for item in recent))
    return "\n\n".join(parts)


def _summarize_feedback(older: list[str]) -> str:
    """Cheap LLM call to compress older feedback turns into bullets."""
    if not older:
        return ""
    try:
        llm = get_llm(0.0, max_tokens=512)
        bullet_input = "\n".join(f"- {item}" for item in older)
        response = llm.invoke([
            SystemMessage(content=PLAN_FEEDBACK_SUMMARIZER_PROMPT),
            HumanMessage(content=bullet_input),
        ])
        return (response.content or "").strip()
    except Exception as e:
        print(f"[Plan][WARN] Feedback summarization failed ({e}); keeping verbatim.", file=sys.stderr)
        return "\n".join(f"- {item}" for item in older)


def _classify_feedback(feedback_text: str) -> tuple[str, str]:
    """Return (label, reason). Falls back to 'render' on any error."""
    if not feedback_text.strip():
        return "render", "empty feedback"
    try:
        llm = get_llm(0.0, max_tokens=256)
        response = llm.invoke([
            SystemMessage(content=PLAN_FEEDBACK_CLASSIFIER_PROMPT),
            HumanMessage(content=f"User feedback:\n{feedback_text}"),
        ])
        raw = (response.content or "").strip()
        # Tolerate fenced JSON or stray text around the object.
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if fence:
            raw = fence.group(1).strip()
        decoder = json.JSONDecoder()
        idx = raw.find("{")
        if idx >= 0:
            obj, _ = decoder.raw_decode(raw, idx)
            label = str(obj.get("label", "")).strip().lower()
            reason = str(obj.get("reason", "")).strip()
            if label in PLAN_FEEDBACK_LABELS:
                return label, reason
        print(f"[Plan][WARN] Classifier returned unparseable response: {raw!r}", file=sys.stderr)
        return "ambiguous", "unparseable classifier response"
    except Exception as e:
        print(f"[Plan][WARN] Classifier call failed ({e}); falling back to render.", file=sys.stderr)
        return "render", f"classifier error: {e}"


def _make_feedback_message(text: str) -> HumanMessage:
    """Wrap a plan-feedback string with the marker prefix for later filtering."""
    return HumanMessage(content=f"{PLAN_FEEDBACK_MARKER}{text}")


def _dispatch_feedback(
    *,
    label: str,
    reason: str,
    feedback_text: str,
    html_path: Path,
    session_dir: str,
    loop_counts: dict,
    explore_intake: dict,
    prior_design: dict,
) -> dict:
    """Translate a classifier label into the state delta that drives routing."""
    print(f"[Plan] Feedback classified as '{label}': {reason}", flush=True)

    if label == "approve":
        append_step(session_dir, 4, str(html_path))
        return {
            "plan_html_path": str(html_path),
            "plan_feedback_route": "approve",
            "current_step": 4,
            "loop_counts": loop_counts,
        }

    html_path.unlink(missing_ok=True)

    if label == "render":
        return {
            "plan_html_path": "",
            "plan_feedback_route": "render",
            "messages": [_make_feedback_message(feedback_text)],
            "loop_counts": loop_counts,
        }

    if label == "refine":
        # Reset plan + refine loop counts so the backward jump and subsequent
        # re-render aren't aborted by counts accumulated during the initial pass.
        new_counts = dict(loop_counts)
        new_counts["plan"] = 0
        new_counts["refine"] = 0
        seed = (
            "The user reviewed the rendered preview and rejected it.\n\n"
            f"User feedback:\n{feedback_text}\n\n"
            "Please revise the design.json to address this feedback. "
            "Output the revised JSON following the standard format ending with "
            "<<DESIGN_READY>> on its own line and the JSON in a fenced ```json block."
        )
        return {
            "plan_html_path": "",
            "plan_feedback_route": "refine",
            "messages": [
                _make_feedback_message(feedback_text),
                HumanMessage(content=seed),
            ],
            "loop_counts": new_counts,
        }

    # label == "explore"
    # Reset all three so revise → finalize → refine → plan can run cleanly
    # regardless of how many turns the initial pass consumed.
    new_counts = dict(loop_counts)
    new_counts["plan"] = 0
    new_counts["refine"] = 0
    new_counts["explore"] = 0
    intake = dict(explore_intake)
    intake["stage"] = "revise"
    intake["prior_direction"] = prior_design if isinstance(prior_design, dict) else {}
    intake["rejection_feedback"] = feedback_text
    return {
        "plan_html_path": "",
        "plan_feedback_route": "explore",
        "explore_intake": intake,
        "messages": [_make_feedback_message(feedback_text)],
        "loop_counts": new_counts,
    }


def _get_html_path(session_dir: str) -> Path:
    if session_dir:
        return Path(session_dir) / "plan.html"
    # No session directory yet — write to the OS temp dir so we don't pollute
    # ~/.config/rice-sessions with a stray file.
    return Path(tempfile.gettempdir()) / "linux-ricing-plan.html"


def _extract_html(content: str) -> str:
    """Strip markdown fences if the model wrapped the HTML."""
    content = content.strip()
    # Remove ```html ... ``` or ``` ... ``` wrapping.
    # The previous regex tried to match partial closing tags inside the pattern
    # and would almost never succeed; use a simple fence-strip instead.
    fence_match = re.search(r"```(?:html)?\s*([\s\S]*?)```", content)
    if fence_match:
        inner = fence_match.group(1).strip()
        if inner.startswith("<!DOCTYPE") or inner.startswith("<html"):
            return inner
    if content.startswith("<!DOCTYPE") or content.startswith("<html"):
        return content
    # Try to find the HTML block anywhere in the response
    for marker in ("<!DOCTYPE", "<html"):
        start = content.find(marker)
        if start != -1:
            return content[start:]
    print("[Plan][WARN] No HTML marker found in LLM response — plan.html will be empty", file=sys.stderr)
    return ""


def _preview_contract_violations(html: str, design: dict | None = None) -> list[str]:
    """Return preview honesty violations that should block approval."""
    lower = html.lower()
    violations: list[str] = []

    if any(term in lower for term in _MACOS_CHROME_TERMS):
        violations.append("macOS traffic-light window chrome is not implemented")
    else:
        hits = {hex_code for hex_code in _MACOS_TRAFFIC_LIGHT_HEXES if hex_code in lower}
        if len(hits) >= 2:
            violations.append("macOS red/yellow/green traffic-light colors detected in window chrome")

    if _looks_like_rounded_window_or_terminal(lower) and not _rounded_chrome_is_implementable(design or {}):
        violations.append("rounded terminal/window chrome previewed without implementable chrome_strategy")

    return violations


def _looks_like_rounded_window_or_terminal(lower_html: str) -> bool:
    """Heuristic for rounded app/window chrome, not ordinary rounded buttons."""
    if "border-radius" not in lower_html and "rounded window" not in lower_html and "rounded terminal" not in lower_html:
        return False
    chrome_terms = ("terminal", "titlebar", "title-bar", "window-frame", "window frame", "app-window", "app window")
    return any(term in lower_html for term in chrome_terms)


def _rounded_chrome_is_implementable(design: dict) -> bool:
    chrome = design.get("chrome_strategy", {}) if isinstance(design, dict) else {}
    if not isinstance(chrome, dict):
        return False
    rounded = chrome.get("rounded_corners")
    wants_rounding = rounded is True or (isinstance(rounded, dict) and rounded.get("enabled"))
    if not wants_rounding:
        return False
    method = str(chrome.get("method", "")).lower()
    targets = " ".join(str(t).lower() for t in chrome.get("implementation_targets", []))
    implementable_terms = ("eww", "frame", "overlay", "custom", "kvantum", "terminal_config", "kitty")
    return any(term in method or term in targets for term in implementable_terms)


def _contract_violation_html(design: dict, violations: list[str]) -> str:
    """Generate a visible rejection page instead of a misleading preview."""
    palette = design.get("palette", {}) if isinstance(design, dict) else {}
    bg = palette.get("background", "#111111")
    fg = palette.get("foreground", "#f5f5f5")
    danger = palette.get("danger", "#ff5555")
    surface = palette.get("surface", "#222222")
    items = "".join(f"<li>{_html_escape(v)}</li>" for v in violations)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="linux-ricing-contract-violation" content="preview-honesty">
<title>Preview rejected</title><style>
body{{margin:0;background:{bg};color:{fg};font:16px system-ui,sans-serif;display:grid;place-items:center;min-height:100vh}}
main{{max-width:760px;background:{surface};border:2px solid {danger};border-radius:24px;padding:32px;box-shadow:0 24px 80px #0008}}
h1{{color:{danger};margin-top:0}} code{{background:#0005;padding:2px 6px;border-radius:6px}}
</style></head><body><main>
<h1>Preview rejected: misleading window chrome</h1>
<p>The generated mockup showed UI chrome that the workflow will not implement.</p>
<ul>{items}</ul>
<p>Type <code>regenerate</code>. The next preview must use frameless terminal content, custom Linux/KDE chrome, or controls that are actually implemented.</p>
</main></body></html>"""


def _existing_contract_violations(path: Path, design: dict | None = None) -> list[str]:
    try:
        html = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    if 'name="linux-ricing-contract-violation"' in html:
        return ["previous preview was rejected for misleading unimplemented window chrome"]
    return _preview_contract_violations(html, design)


def _html_escape(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))
