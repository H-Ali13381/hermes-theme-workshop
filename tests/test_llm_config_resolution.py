"""Tests for deterministic LLM configuration resolution."""
from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from workflow.config import CODEX_BASE_URL, get_llm, resolve_llm_config


class LlmConfigResolutionTests(unittest.TestCase):
    def test_ricer_env_overrides_hermes_config(self):
        hermes = {
            "base_url": "https://hermes.example/v1",
            "api_key": "hermes-key",
            "model": "hermes/model",
            "api_mode": "chat_completions",
        }
        env = {
            "RICER_BASE_URL": "https://override.example/v1",
            "RICER_API_KEY": "override-key",
            "RICER_MODEL": "override/model",
        }
        with patch.dict(os.environ, env, clear=False), \
             patch("workflow.config._load_hermes_config", return_value=hermes):
            resolved = resolve_llm_config()

        self.assertEqual(resolved["base_url"], env["RICER_BASE_URL"])
        self.assertEqual(resolved["api_key"], env["RICER_API_KEY"])
        self.assertEqual(resolved["model"], env["RICER_MODEL"])

    def test_hermes_config_fills_missing_ricer_env(self):
        hermes = {
            "base_url": "https://hermes.example/v1",
            "api_key": "hermes-key",
            "model": "hermes/model",
            "api_mode": "chat_completions",
        }
        with patch.dict(os.environ, {k: "" for k in ("RICER_BASE_URL", "RICER_API_KEY", "RICER_MODEL")}, clear=False), \
             patch("workflow.config._load_hermes_config", return_value=hermes):
            resolved = resolve_llm_config()

        self.assertEqual(resolved["base_url"], hermes["base_url"])
        self.assertEqual(resolved["api_key"], hermes["api_key"])
        self.assertEqual(resolved["model"], hermes["model"])


    def test_openai_codex_uses_hermes_oauth_path_when_active_provider(self):
        """The workflow should share Hermes Agent's Codex OAuth route."""
        hermes = {
            "base_url": "https://chatgpt.com/backend-api/codex",
            "api_key": "",
            "model": "gpt-5.5",
            "provider": "openai-codex",
            "api_mode": "chat_completions",
        }
        with patch.dict(os.environ, {k: "" for k in ("RICER_BASE_URL", "RICER_API_KEY", "RICER_MODEL")}, clear=False), \
             patch("workflow.config._load_hermes_config", return_value=hermes), \
             patch("workflow.config._parse_dotenv", return_value={"OPENROUTER_API_KEY": "openrouter-key"}):
            resolved = resolve_llm_config()
            llm = get_llm()

        self.assertEqual(resolved["provider"], "openai-codex")
        self.assertEqual(resolved["base_url"], CODEX_BASE_URL)
        self.assertEqual(resolved["api_key"], "")
        self.assertEqual(resolved["api_mode"], "codex_responses")
        self.assertEqual(resolved["model"], "gpt-5.5")
        self.assertEqual(type(llm).__name__, "_CodexOAuthLLM")
        self.assertEqual(llm.model_name, "gpt-5.5")


    def test_codex_oauth_llm_invokes_hermes_agent_client(self):
        """The shim refreshes Hermes OAuth then delegates to Hermes' Codex adapter."""
        hermes = {
            "base_url": "https://chatgpt.com/backend-api/codex",
            "api_key": "",
            "model": "gpt-5.5",
            "provider": "openai-codex",
            "api_mode": "chat_completions",
        }
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
        )
        completions = SimpleNamespace(create=lambda **kwargs: response)
        client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

        with patch.dict(os.environ, {k: "" for k in ("RICER_BASE_URL", "RICER_API_KEY", "RICER_MODEL")}, clear=False), \
             patch("workflow.config._load_hermes_config", return_value=hermes), \
             patch("workflow.config._parse_dotenv", return_value={}), \
             patch("workflow.config.HERMES_AGENT_DIR") as hermes_dir:
            hermes_dir.exists.return_value = True
            llm = get_llm()
            with patch.dict("sys.modules", {
                "hermes_cli": SimpleNamespace(),
                "hermes_cli.auth": SimpleNamespace(
                    AuthError=RuntimeError,
                    resolve_codex_runtime_credentials=lambda: {"api_key": "oauth-token"},
                ),
                "agent": SimpleNamespace(),
                "agent.auxiliary_client": SimpleNamespace(
                    resolve_provider_client=lambda provider, model: (client, model),
                ),
            }):
                result = llm.invoke("ping")

        self.assertEqual(result.content, "ok")


if __name__ == "__main__":
    unittest.main()
