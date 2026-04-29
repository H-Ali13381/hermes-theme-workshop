"""Template rendering: Jinja2 when available, simple {{key}} substitution as fallback."""
from pathlib import Path

# Optional Jinja2 import with fallback
jinja2 = None
try:
    import jinja2  # type: ignore[import]
except ImportError:
    pass


def simple_render(template_str: str, context: dict) -> str:
    """Minimal template renderer when Jinja2 is unavailable.

    Supports the same ``{{key}}`` double-brace syntax used by Jinja2 so that
    templates work identically regardless of whether Jinja2 is installed.
    Using single-brace ``{key}`` would match *inside* ``{{key}}``, leaving
    stray braces in the output (e.g. ``{#1e1e2e}`` instead of ``#1e1e2e``).
    """
    result = template_str
    for key, value in context.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def render_template(template_path: Path, context: dict) -> str:
    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()
    if jinja2:
        env = jinja2.Environment(undefined=jinja2.StrictUndefined)
        tmpl = env.from_string(template_str)
        return tmpl.render(**context)
    return simple_render(template_str, context)
