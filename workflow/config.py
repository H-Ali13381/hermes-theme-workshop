import os
import sys
from pathlib import Path

# ── Module-level constants ────────────────────────────────────────────────────
# Last-resort model fallback — only used when RICER_MODEL env var is unset
# AND no Hermes config is present (h["model"] takes priority when available).
# Must be a valid OpenRouter / OpenAI-compatible model identifier.
MODEL = os.environ.get("RICER_MODEL", "deepseek/deepseek-v4-pro")

SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
SESSIONS_DIR = Path.home() / ".config" / "rice-sessions"
DB_PATH = str(Path.home() / ".local" / "share" / "linux-ricing" / "sessions.sqlite")

# Ensure scripts/ is importable so we can share constants with the scripts layer.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from core.constants import REQUIRED_PALETTE_KEYS as PALETTE_SLOTS  # noqa: E402
BASE_REQUIRED_KEYS = ["name", "description", "palette", "mood_tags"]
RECIPE_REQUIRED_KEYS = {
    "kde": [
        "kvantum_theme", "plasma_theme", "cursor_theme", "icon_theme", "gtk_theme",
        "originality_strategy", "chrome_strategy",
    ],
    "gnome": ["gtk_theme", "cursor_theme", "icon_theme"],
    "hyprland": ["gtk_theme", "cursor_theme", "icon_theme"],
}
RECIPE_PROMPT_FIELDS = {
    "kde": [
        '- kvantum_theme: e.g. "KvDark"',
        '- plasma_theme: e.g. "default" (theme package only; NOT a substitute for layout work)',
        '- cursor_theme: e.g. "default"',
        '- icon_theme: e.g. "Papirus-Dark"',
        '- gtk_theme: e.g. "Adwaita-dark"',
        '- originality_strategy: object with REQUIRED keys "vision_alignment" (string explaining how the design serves the user brief) and "non_default_moves" (list of at least 3 strings, each a SPECIFIC visual decision tied to the brief)',
        '- chrome_strategy: object with REQUIRED keys "method" (string, e.g. "kvantum + eww_frame") and "implementation_targets" (list of strings like ["widgets:eww", "terminal:kitty"]); OPTIONAL keys "rounded_corners" (boolean true/false, or object {"enabled": true, "radius_px": <int>}), "custom_titlebars", "terminal_frames", "panel_chrome", "ornamental_borders" (descriptive strings)',
        '- panel_layout: optional object if the concept changes the panel/dock/toolbar; include mode, placement, shape, and visible controls',
        '- widget_layout: optional list of custom widgets/overlays only when they serve the user vision; each item should describe a name, a position, the live data it shows, and its visual concept',
    ],
    "gnome": [
        '- gtk_theme: e.g. "Adwaita-dark"',
        '- cursor_theme: e.g. "default"',
        '- icon_theme: e.g. "Papirus-Dark"',
    ],
    "hyprland": [
        '- gtk_theme: e.g. "Adwaita-dark"',
        '- cursor_theme: e.g. "default"',
        '- icon_theme: e.g. "Papirus-Dark"',
    ],
}
SUPPORTED_DESKTOP_RECIPES = frozenset(RECIPE_REQUIRED_KEYS)
# Catch configuration drift at import time: every recipe must have both a keys
# list and a prompt-fields list so refine.build_system_prompt never KeyErrors.
assert set(RECIPE_REQUIRED_KEYS) == set(RECIPE_PROMPT_FIELDS), (
    f"RECIPE_PROMPT_FIELDS is missing recipes: "
    f"{set(RECIPE_REQUIRED_KEYS) - set(RECIPE_PROMPT_FIELDS)}"
)
UNSUPPORTED_DESKTOP_MESSAGE = (
    "Unsupported desktop environment for linux-ricing workflow. "
    "Currently supported recipes: KDE Plasma, GNOME, and Hyprland. "
    "Please submit a GitHub ticket requesting support for your environment."
)
# Backward-compatible KDE recipe alias for older imports.
DESIGN_REQUIRED_KEYS = BASE_REQUIRED_KEYS + RECIPE_REQUIRED_KEYS["kde"]
SCORE_PASS_THRESHOLD = 8
# Maximum number of times implement_node will re-process a single element after
# the user selects "retry" at the score gate before forcing a hard skip.
MAX_IMPLEMENT_RETRIES = 3
# Maximum times a looping node (explore / refine / plan) may be re-entered before
# the routing function aborts the workflow to END.  This prevents infinite LLM
# loops when a sentinel appears in the response but JSON parsing consistently fails.
MAX_LOOP_ITERATIONS = 10

# ── Step 4 — Plan feedback classifier ────────────────────────────────────────
# Number of feedback turns the plan node includes verbatim in its prompt before
# falling back to summarization. Older turns above this threshold are summarized
# but the most recent 2 turns are always preserved verbatim.
PLAN_FEEDBACK_VERBATIM_TURNS = 6

# Routing labels the plan-feedback classifier may emit.
PLAN_FEEDBACK_LABELS = ("approve", "render", "refine", "explore", "ambiguous")

PLAN_FEEDBACK_CLASSIFIER_PROMPT = """\
You are classifying user feedback on a Linux desktop theme preview to decide what to revise.

The pipeline has three artifacts:
- direction: stance, mood, reference anchor (the creative vibe).
- design.json: 10-key palette + chrome strategy + originality + optional widgets/panel.
- plan.html: a rendered preview of the design.

Pick the SINGLE label that best matches the user's feedback:

- "approve": user accepts the preview as-is (e.g. "looks good", "ship it").
- "render": user wants the preview re-rendered without changing the underlying design
  (e.g. "the screenshot is glitchy", "regenerate", "try the same thing again").
- "refine": feedback targets the design.json — palette, colors, chrome, widgets, panel,
  specific layout pieces (e.g. "too cold", "drop the widgets", "make accent purple",
  "rounded corners look wrong", "add a panel on the left").
- "explore": feedback rejects the overall direction/vibe — stance, mood, reference anchor
  (e.g. "this whole thing feels wrong", "I wanted something cyberpunk not cottagecore",
  "different vibe entirely", "let's start over").
- "ambiguous": you cannot confidently choose between two or more of the above.

Output ONLY a JSON object on a single line: {"label": "<one-of-the-labels>", "reason": "<one-short-sentence>"}
No prose, no fences, no extra keys.
"""

PLAN_FEEDBACK_SUMMARIZER_PROMPT = """\
You are summarizing prior user feedback on a Linux desktop theme preview so the
designer LLM can produce a better next iteration.

You will receive a sequence of older user feedback turns. Produce a compact
bulleted summary that preserves:
- What the user explicitly REJECTED (colors, chrome, widgets, vibe).
- What the user explicitly LIKED or asked to keep.
- Any HARD constraints ("never use neon", "must keep widgets off").

Drop pleasantries, hedging, and meta-talk. Keep it under 8 bullets.
Output ONLY the bullets, no preamble.
"""


# ── Step 3 — Design creativity judge ─────────────────────────────────────────
# Semantic counterpart to validators._kde_creativity_complete (which only
# checks structural shape).  Run AFTER structural validation passes.
DESIGN_CREATIVITY_JUDGE_PROMPT = """\
You are auditing a Linux desktop design_system JSON against the user's brief.
Structural validity (required keys, palette hex, types) has already been
verified. Judge ONLY these semantic criteria:

1. originality: at least 3 of the non_default_moves are SPECIFIC visual
   decisions tied to the brief (not generic phrases like "modern look",
   "clean panel", "polished defaults"). A move that names what it replaces
   ("replace the default Plasma toolbar with a vertical stave") is fine AS
   LONG AS the replacement is specified concretely.
2. chrome_strategy.method explains HOW the chrome is built; implementation
   _targets names which subsystems carry it. Reject empty/placeholder values.
3. widget_layout (if present): each widget must convey a real DATA SOURCE
   (what live information feeds it) and a real VISUAL CONCEPT (what it looks
   like). Field names may vary across responses (e.g. "data" / "data_source"
   / "feed"; "visual" / "visual_metaphor" / "appearance") — judge by content
   meaning, NOT by key spelling.
4. panel_layout (if present): not a verbatim Plasma/Breeze stock toolbar.
   "Stock" means the design proposes no specific change; merely *naming*
   the default it replaces is fine.
5. The design coheres with the brief — not a palette swap with default
   chrome.

Brief (creative direction):
{direction}

Design:
{design}

Output ONLY a JSON object on a single line, no prose, no fences:
{{"pass": <true|false>, "fail_reasons": [<short sentence per failure>]}}
If you cannot decide confidently, output {{"pass": true, "fail_reasons": []}}
to fail open — a human will judge the rendered preview next.
"""


def judge_design_creativity(design: dict, direction: dict) -> tuple[bool, list[str]]:
    """LLM gate that semantically audits a structurally-valid design.

    Returns ``(True, [])`` on pass or fail-open (parse errors, network blips).
    Returns ``(False, reasons)`` only when the judge confidently rejects.
    """
    import json as _json  # noqa: PLC0415

    from .log_setup import get_logger  # noqa: PLC0415

    log = get_logger("config.judge")
    try:
        llm = get_llm(temperature=0)
    except Exception as e:
        log.warning("creativity judge unavailable (%s); failing open", e)
        return True, []

    prompt = DESIGN_CREATIVITY_JUDGE_PROMPT.format(
        direction=_json.dumps(direction, indent=2),
        design=_json.dumps(design, indent=2),
    )
    try:
        response = llm.invoke(prompt)
    except Exception as e:
        log.warning("creativity judge call failed (%s); failing open", e)
        return True, []

    raw = (getattr(response, "content", None) or "").strip()
    # Strip markdown fences in case the model wrapped despite instructions.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].lstrip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < 0 or end <= start:
        log.warning("creativity judge returned non-JSON (%r); failing open", raw[:120])
        return True, []
    try:
        verdict = _json.loads(raw[start:end + 1])
    except Exception as e:
        log.warning("creativity judge JSON parse error (%s); failing open", e)
        return True, []

    if not isinstance(verdict, dict):
        return True, []
    if verdict.get("pass") is True:
        return True, []
    reasons = verdict.get("fail_reasons") or []
    if not isinstance(reasons, list) or not reasons:
        # Fail with no actionable reasons → treat as ambiguous, fail open.
        return True, []
    return False, [str(r) for r in reasons]


def _parse_dotenv(path: Path) -> dict:
    result = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    except Exception as e:
        from .log_setup import get_logger
        get_logger("config").warning("could not parse %s: %s", path, e)
    return result


_PROVIDER_KEY_ENV: dict[str, str] = {
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic":  "ANTHROPIC_API_KEY",
    "openai":     "OPENAI_API_KEY",
    "deepseek":   "DEEPSEEK_API_KEY",
    "google":     "GOOGLE_API_KEY",
    "xai":        "XAI_API_KEY",
    "copilot":    "GITHUB_TOKEN",
}


def _load_hermes_config() -> dict:
    """Read active provider config from ~/.hermes/config.yaml + .env."""
    config_path = Path.home() / ".hermes" / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        from .log_setup import get_logger
        get_logger("config").warning("could not load %s: %s", config_path, e)
        return {}

    model_cfg  = cfg.get("model", {})
    provider   = model_cfg.get("provider", "")
    base_url   = model_cfg.get("base_url", "")
    api_mode   = model_cfg.get("api_mode", "chat_completions")
    model_name = model_cfg.get("default", "")

    # Priority 1: inline api_key in config.yaml providers section
    api_key = cfg.get("providers", {}).get(provider, {}).get("api_key", "")

    # Priority 2: always check ~/.hermes/.env — .env keys are more likely to be
    # current than inline config.yaml keys, which can go stale.
    env_vars = _parse_dotenv(Path.home() / ".hermes" / ".env")
    env_var_name = _PROVIDER_KEY_ENV.get(provider, "")
    if env_var_name:
        env_key = env_vars.get(env_var_name, "")
        if env_key:
            api_key = env_key

    return {
        "base_url": base_url,
        "api_key":  api_key,
        "model":    model_name,
        "provider": provider,
        "api_mode": api_mode,
    }


def resolve_llm_config() -> dict:
    """Resolve LLM connection settings from env and Hermes config.

    Priority:
      1. RICER_* env vars (bypass Hermes subprocess env blocklist)
      2. ~/.hermes/config.yaml + .env (active Hermes provider)
    """
    base_url = os.environ.get("RICER_BASE_URL", "")
    api_key  = os.environ.get("RICER_API_KEY", "")
    model    = os.environ.get("RICER_MODEL", "")
    api_mode = ""

    # Always load Hermes config so we can fill in missing fields (especially model).
    h = _load_hermes_config()
    base_url = base_url or h.get("base_url", "")
    api_key  = api_key  or h.get("api_key",  "")
    api_mode = h.get("api_mode", "")
    if not model and h.get("model"):
        model = h["model"]
    if not model:
        model = MODEL

    return {"base_url": base_url, "api_key": api_key, "model": model, "api_mode": api_mode}


def get_llm(temperature: float = 0.7, max_tokens: int | None = None):
    """Return a LangChain chat model inheriting Hermes' active provider."""
    resolved = resolve_llm_config()
    base_url = resolved["base_url"]
    api_key = resolved["api_key"]
    model = resolved["model"]
    api_mode = resolved["api_mode"]

    is_anthropic_native = (
        api_mode == "anthropic_messages"
        or (not api_mode and not base_url and model.startswith("claude-"))
    )

    if is_anthropic_native:
        from langchain_anthropic import ChatAnthropic
        kwargs: dict = {"model": model, "temperature": temperature}
        if max_tokens is not None: kwargs["max_tokens"] = max_tokens
        if api_key:                kwargs["api_key"]    = api_key
        return ChatAnthropic(**kwargs)

    from langchain_openai import ChatOpenAI
    kwargs: dict = {"model": model, "temperature": temperature}
    if base_url:               kwargs["base_url"]   = base_url
    if api_key:                kwargs["api_key"]    = api_key
    if max_tokens is not None: kwargs["max_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)
