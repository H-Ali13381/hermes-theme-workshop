"""Tests for deterministic LLM configuration resolution."""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from workflow.config import resolve_llm_config


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


if __name__ == "__main__":
    unittest.main()