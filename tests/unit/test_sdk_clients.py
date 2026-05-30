from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sdk.claude_client import ClaudeAgentClient
from sdk.gemini_client import GeminiAgentClient


def test_claude_prompt_api_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

    client = ClaudeAgentClient()
    mock_anthropic = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="hello")]
    mock_anthropic.messages.create.return_value = mock_message

    with patch("anthropic.Anthropic", return_value=mock_anthropic):
        result = client.prompt_api("system", "user")

    assert result.text == "hello"


def test_claude_prompt_api_web_search_adds_tool_and_joins_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

    client = ClaudeAgentClient(web_search=True)
    mock_anthropic = MagicMock()
    tool_block = MagicMock()
    tool_block.text = 123  # non-string -> skipped by _extract_text
    text_block = MagicMock()
    text_block.text = "grounded answer"
    mock_message = MagicMock()
    mock_message.content = [tool_block, text_block]
    mock_anthropic.messages.create.return_value = mock_message

    with patch("anthropic.Anthropic", return_value=mock_anthropic):
        result = client.prompt_api("system", "user")

    assert result.text == "grounded answer"
    _, kwargs = mock_anthropic.messages.create.call_args
    assert kwargs["tools"] == [{"type": "web_search_20250305", "name": "web_search"}]


def test_claude_prompt_cli_success():
    client = ClaudeAgentClient(cli_command="claude")

    completed = MagicMock()
    completed.stdout = "cli answer"
    completed.returncode = 0
    completed.stderr = ""

    with patch("sdk.claude_client.subprocess.run", return_value=completed):
        result = client.prompt("system", "user")

    assert result.text == "cli answer"


def test_gemini_client_missing_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        GeminiAgentClient()


def test_gemini_prompt_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")

    client = GeminiAgentClient(use_google_search=False)

    with patch.object(client, "_generate", return_value="gemini answer"):
        result = client.prompt("system", "user")

    assert result.text == "gemini answer"
