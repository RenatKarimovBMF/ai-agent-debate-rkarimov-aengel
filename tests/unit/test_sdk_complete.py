from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sdk.claude_client import ClaudeResponse
from sdk.llm_client import LlmClient


def test_llm_complete_gemini_path(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456")

    client = LlmClient()
    mock_gemini = MagicMock()
    mock_gemini.prompt.return_value = ClaudeResponse(text="answer", raw="raw")

    with patch.object(client, "_gemini_client", return_value=mock_gemini):
        result = client.complete("system", "user")

    assert result.text == "answer"
    assert result.provider == "gemini"


def test_llm_complete_anthropic_path(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

    client = LlmClient()
    mock_claude = MagicMock()
    mock_claude.prompt_api.return_value = ClaudeResponse(text="api", raw="raw")

    with patch.object(client, "_claude", mock_claude):
        result = client.complete("system", "user")

    assert result.provider == "anthropic"


def test_llm_gemini_forced_without_key_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    client = LlmClient()
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        client.complete("s", "u")


def test_llm_cli_fallback_error_message(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "claude_cli")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    client = LlmClient()
    with patch.object(client._claude, "prompt", side_effect=FileNotFoundError("no cli")):
        with pytest.raises(RuntimeError, match="No LLM available"):
            client.complete("s", "u")
