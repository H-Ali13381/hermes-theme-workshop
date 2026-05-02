"""Workflow logging — stderr console + per-session file.

Provides a thin wrapper over the stdlib ``logging`` module so every workflow
node can emit structured diagnostics without each node reinventing the wheel.

Usage::

    from workflow.logging import get_logger, truncate_for_log
    log = get_logger("refine", state)  # state is optional
    log.info("starting attempt %d", n)
    log.debug("raw response:\\n%s", truncate_for_log(content))

The session file lives at ``<session_dir>/workflow.log`` so all artefacts for
one rice (design.json, plan.html, session.md, workflow.log) sit together.

Environment variables:
    RICER_LOG_LEVEL  console level — DEBUG/INFO/WARNING/ERROR (default INFO)
    RICER_LOG_FILE   file level — same values, or OFF to disable (default DEBUG)
    RICER_LOG_RAW    "1" disables truncation in ``truncate_for_log``
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATEFMT = "%H:%M:%S"

# Cache of file handlers keyed by absolute log path so multiple loggers share
# one file handle per session and we don't duplicate lines.
_SESSION_HANDLERS: dict[str, logging.FileHandler] = {}


def _level_from_env(var: str, default: str) -> int | None:
    """Parse a log-level env var. Returns None when set to OFF."""
    raw = os.environ.get(var, default).upper()
    if raw == "OFF":
        return None
    return getattr(logging, raw, getattr(logging, default))


def _ensure_console_handler(logger: logging.Logger) -> None:
    if any(getattr(h, "_ricer_console", False) for h in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT, _DATEFMT))
    level = _level_from_env("RICER_LOG_LEVEL", "INFO")
    handler.setLevel(level if level is not None else logging.CRITICAL + 1)
    handler._ricer_console = True  # type: ignore[attr-defined]
    logger.addHandler(handler)


def _ensure_session_handler(logger: logging.Logger, session_dir: str) -> None:
    file_level = _level_from_env("RICER_LOG_FILE", "DEBUG")
    if file_level is None or not session_dir:
        return
    log_path = str(Path(session_dir) / "workflow.log")
    cached = _SESSION_HANDLERS.get(log_path)
    if cached is not None:
        if cached not in logger.handlers:
            logger.addHandler(cached)
        return
    try:
        Path(session_dir).mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
    except OSError as e:
        # Don't let a broken session dir crash the workflow — fall back to
        # stderr-only logging and surface the issue once.
        logger.warning("could not open workflow.log at %s: %s", log_path, e)
        return
    handler.setFormatter(logging.Formatter(_FORMAT, _DATEFMT))
    handler.setLevel(file_level)
    _SESSION_HANDLERS[log_path] = handler
    logger.addHandler(handler)


def get_logger(name: str, state: dict | None = None) -> logging.Logger:
    """Return a workflow logger configured for stderr + optional session file.

    Pass ``state`` (the LangGraph node's state dict) to enable the per-session
    file handler. When ``state`` is missing or has no ``session_dir`` (e.g.
    during unit tests), only the console handler is attached.
    """
    logger = logging.getLogger(f"ricer.{name}")
    # Logger admits everything — handlers do the gating. This lets DEBUG reach
    # the file even when the console is at INFO.
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    _ensure_console_handler(logger)
    if state is not None:
        session_dir = ""
        if hasattr(state, "get"):
            session_dir = state.get("session_dir") or ""
        if session_dir:
            _ensure_session_handler(logger, session_dir)
    return logger


def truncate_for_log(content: str, limit: int = 2000) -> str:
    """Truncate long content for log readability.

    Honours ``RICER_LOG_RAW=1`` to emit the full payload — useful when
    diagnosing LLM output that fails JSON extraction.
    """
    if os.environ.get("RICER_LOG_RAW") == "1":
        return content
    if not content or len(content) <= limit:
        return content
    head = content[: limit // 2]
    tail = content[-limit // 2 :]
    return f"{head}\n... [truncated {len(content) - limit} chars] ...\n{tail}"
