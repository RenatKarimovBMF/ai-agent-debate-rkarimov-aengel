"""Targeted branch coverage for `sdk.llm_client.LlmClient` and the
`_env_key` helper that gates placeholder API keys.
"""

from __future__ import annotations

import pytest

from sdk.llm_client import LlmClient, _env_key

from ._coverage_helpers import MagicMock


def test_env_key_rejects_placeholder(monkeypatch):
    monkeypatch.setenv("FAKE_KEY", "your-key-here")
    assert _env_key("FAKE_KEY") is None


def test_env_key_accepts_real_key(monkeypatch):
    monkeypatch.setenv("REAL_KEY", "abc123def456")
    assert _env_key("REAL_KEY") == "abc123def456"


def test_env_key_returns_none_for_missing(monkeypatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)
    assert _env_key("MISSING_KEY") is None


def test_llm_client_forces_gemini_without_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    client = LlmClient()
    with pytest.raises(RuntimeError, match="LLM_PROVIDER=gemini"):
        client._resolve_provider()


def test_llm_client_forces_anthropic(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = LlmClient()
    assert client._resolve_provider() == "anthropic"


def test_llm_client_forces_claude_cli(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "claude_cli")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = LlmClient()
    assert client._resolve_provider() == "claude_cli"


def test_llm_client_auto_prefers_claude_cli_when_available(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real")
    client = LlmClient()
    monkeypatch.setattr(client._claude, "available", lambda: True)
    assert client._resolve_provider() == "claude_cli"


def test_llm_client_auto_uses_anthropic_when_cli_absent(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real")
    client = LlmClient()
    monkeypatch.setattr(client._claude, "available", lambda: False)
    assert client._resolve_provider() == "anthropic"


def test_llm_client_auto_uses_gemini_when_only_gemini_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = LlmClient()
    monkeypatch.setattr(client._claude, "available", lambda: False)
    assert client._resolve_provider() == "gemini"


def test_llm_client_auto_last_resort_claude_cli(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = LlmClient()
    monkeypatch.setattr(client._claude, "available", lambda: False)
    assert client._resolve_provider() == "claude_cli"


def test_llm_client_complete_gemini_path(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    client = LlmClient()
    fake_gem = MagicMock()
    fake_gem.prompt.return_value = MagicMock(text="g", raw="g")
    monkeypatch.setattr(client, "_gemini_client", lambda: fake_gem)

    response = client.complete("system", "user")
    assert response.provider == "gemini"
    assert response.text == "g"


def test_llm_client_complete_anthropic_path(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    client = LlmClient()
    client._claude.prompt_api = MagicMock(return_value=MagicMock(text="a", raw="a"))

    response = client.complete("system", "user")
    assert response.provider == "anthropic"
    assert response.text == "a"


def test_llm_client_complete_claude_cli_path(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "claude_cli")
    client = LlmClient()
    client._claude.prompt = MagicMock(return_value=MagicMock(text="c", raw="c"))

    response = client.complete("system", "user")
    assert response.provider == "claude_cli"
    assert response.text == "c"


def test_llm_client_complete_no_provider_available(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "claude_cli")
    client = LlmClient()
    client._claude.prompt = MagicMock(side_effect=FileNotFoundError("claude"))

    with pytest.raises(RuntimeError, match="No LLM available"):
        client.complete("system", "user")


def test_llm_client_caches_gemini_instance(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    client = LlmClient()
    fake_constructor = MagicMock(return_value=MagicMock())
    monkeypatch.setattr("sdk.llm_client.GeminiAgentClient", fake_constructor)
    client._gemini_client()
    client._gemini_client()
    assert fake_constructor.call_count == 1
