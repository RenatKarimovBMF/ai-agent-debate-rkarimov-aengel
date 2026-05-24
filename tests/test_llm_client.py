import os

from sdk.llm_client import LlmClient


def test_provider_prefers_gemini_when_key_set(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    client = LlmClient()
    assert client.active_provider() == "gemini"


def test_provider_forced_anthropic(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    client = LlmClient()
    assert client.active_provider() == "anthropic"


def test_placeholder_anthropic_key_ignored(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-your-key-here")
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyAbc123realkey")
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    client = LlmClient()
    assert client.active_provider() == "gemini"
