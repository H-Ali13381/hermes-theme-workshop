import os
import sys
from pathlib import Path

# ── Module-level constants ────────────────────────────────────────────────────
# Last-resort model fallback — only used when RICER_MODEL env var is unset
# AND no Hermes config is present (h["model"] takes priority when available).
# Must be a valid Anthropic API model identifier.
# Short aliases like "claude-sonnet-4-6" are Hermes-internal; for a standalone
# fallback use the full versioned string, e.g. "claude-3-5-sonnet-20241022".
# Update this constant whenever the target model changes.
MODEL = os.environ.get("RICER_MODEL", "claude-sonnet-4-5-20251029")

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
    "kde": ["kvantum_theme", "plasma_theme", "cursor_theme", "icon_theme", "gtk_theme"],
    "gnome": ["gtk_theme", "cursor_theme", "icon_theme"],
    "hyprland": ["gtk_theme", "cursor_theme", "icon_theme"],
}
RECIPE_PROMPT_FIELDS = {
    "kde": [
        '- kvantum_theme: e.g. "KvDark"',
        '- plasma_theme: e.g. "default"',
        '- cursor_theme: e.g. "default"',
        '- icon_theme: e.g. "Papirus-Dark"',
        '- gtk_theme: e.g. "Adwaita-dark"',
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


def _parse_dotenv(path: Path) -> dict:
    result = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
    except Exception as e:
        print(f"[config] Warning: could not parse {path}: {e}", file=sys.stderr)
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
        import sys
        print(f"[config] Warning: could not load {config_path}: {e}", file=sys.stderr)
        return {}

    model_cfg  = cfg.get("model", {})
    provider   = model_cfg.get("provider", "")
    base_url   = model_cfg.get("base_url", "")
    api_mode   = model_cfg.get("api_mode", "chat_completions")
    model_name = model_cfg.get("default", "")

    # Priority 1: inline api_key in config.yaml providers section
    api_key = cfg.get("providers", {}).get(provider, {}).get("api_key", "")

    if not api_key:
        # Priority 2: read from ~/.hermes/.env
        env_vars = _parse_dotenv(Path.home() / ".hermes" / ".env")
        env_var_name = _PROVIDER_KEY_ENV.get(provider, "")
        if env_var_name:
            api_key = env_vars.get(env_var_name, "")

    return {
        "base_url": base_url,
        "api_key":  api_key,
        "model":    model_name,
        "provider": provider,
        "api_mode": api_mode,
    }


def get_llm(temperature: float = 0.7, max_tokens: int | None = None):
    """Return a LangChain chat model inheriting Hermes' active provider.

    Priority:
      1. RICER_* env vars (bypass Hermes subprocess env blocklist)
      2. ~/.hermes/config.yaml + .env (active Hermes provider)
    """
    base_url = os.environ.get("RICER_BASE_URL", "")
    api_key  = os.environ.get("RICER_API_KEY", "")
    model    = MODEL
    api_mode = ""

    if not (base_url and api_key):
        h = _load_hermes_config()
        base_url = base_url or h.get("base_url", "")
        api_key  = api_key  or h.get("api_key",  "")
        api_mode = h.get("api_mode", "")
        if not os.environ.get("RICER_MODEL") and h.get("model"):
            model = h["model"]

    is_anthropic_native = (
        api_mode == "anthropic_messages"
        or (not api_mode and not base_url and model.startswith("claude-"))
    )

    if is_anthropic_native:
        from langchain_anthropic import ChatAnthropic
        kwargs: dict = {"model": model, "temperature": temperature}
        if max_tokens: kwargs["max_tokens"] = max_tokens
        if api_key:    kwargs["api_key"]    = api_key
        return ChatAnthropic(**kwargs)

    from langchain_openai import ChatOpenAI
    kwargs: dict = {"model": model, "temperature": temperature}
    if base_url:   kwargs["base_url"]   = base_url
    if api_key:    kwargs["api_key"]    = api_key
    if max_tokens: kwargs["max_tokens"] = max_tokens
    return ChatOpenAI(**kwargs)
