"""Regression tests for honest plan.html preview chrome."""
from __future__ import annotations

from pathlib import Path

from workflow.nodes import plan as plan_mod


def test_plan_prompt_forbids_unimplemented_macos_traffic_lights():
    prompt = plan_mod.SYSTEM_PROMPT.lower()

    assert "traffic-light" in prompt
    assert "workflow does not currently implement" in prompt
    assert "never preview app/window chrome" in prompt


def test_preview_contract_detects_macos_traffic_light_terms():
    html = """
    <html><body>
      <div class="terminal"><div class="traffic-lights">
        <span></span><span></span><span></span>
      </div></div>
    </body></html>
    """

    violations = plan_mod._preview_contract_violations(html)

    assert violations
    assert "macOS traffic-light" in violations[0]


def test_preview_contract_detects_common_macos_button_colors():
    html = """
    <html><body><div class="terminal-titlebar">
      <span style="background:#ff5f56"></span>
      <span style="background:#ffbd2e"></span>
      <span style="background:#27c93f"></span>
    </div></body></html>
    """

    violations = plan_mod._preview_contract_violations(html)

    assert violations
    assert "red/yellow/green" in violations[0]


def test_preview_contract_allows_linux_top_right_controls():
    html = """
    <html><body><div class="kde-titlebar">
      <button aria-label="minimize">_</button>
      <button aria-label="maximize">□</button>
      <button aria-label="close">×</button>
    </div></body></html>
    """

    assert plan_mod._preview_contract_violations(html) == []


def test_preview_contract_rejects_unimplemented_rounded_terminal_chrome():
    html = """
    <html><body><section class="terminal-window" style="border-radius: 28px">
      $ echo rounded
    </section></body></html>
    """

    violations = plan_mod._preview_contract_violations(html, {"chrome_strategy": {"rounded_corners": False}})

    assert violations
    assert "rounded terminal/window chrome" in violations[0]


def test_preview_contract_allows_rounded_terminal_when_chrome_is_implementable():
    html = """
    <html><body><section class="terminal-window" style="border-radius: 28px">
      $ echo rounded
    </section></body></html>
    """
    design = {
        "chrome_strategy": {
            "method": "eww_frame + terminal_config",
            "rounded_corners": {"enabled": True, "radius_px": 28},
            "implementation_targets": ["widgets:eww", "terminal:kitty"],
        }
    }

    assert plan_mod._preview_contract_violations(html, design) == []


def test_contract_violation_page_blocks_existing_approval(tmp_path: Path):
    html = plan_mod._contract_violation_html(
        {"palette": {"background": "#111111", "foreground": "#eeeeee", "surface": "#222222", "danger": "#ff5555"}},
        ["macOS traffic-light window chrome is not implemented"],
    )
    path = tmp_path / "plan.html"
    path.write_text(html, encoding="utf-8")

    violations = plan_mod._existing_contract_violations(path)

    assert violations == ["previous preview was rejected for misleading unimplemented window chrome"]
