"""Targeted branch coverage for `sdk.gemini_client.GeminiAgentClient`
and the `_is_quota_error` helper.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from sdk.gemini_client import GeminiAgentClient, _is_quota_error

from ._coverage_helpers import MagicMock


def test_gemini_prompt_handles_missing_genai_package(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")
    client = GeminiAgentClient(use_google_search=False)
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "google" or name.startswith("google."):
            raise ImportError("no module")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="'google-genai' is not installed"):
        client.prompt("system", "user")


def test_gemini_prompt_retries_then_succeeds(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")
    client = GeminiAgentClient(use_google_search=False, max_retries=2)

    call_count = {"n": 0}

    def fake_generate(client_arg, model_name, system, user, use_search):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("429 too many")
        return "answer"

    monkeypatch.setattr(client, "_generate", fake_generate)
    monkeypatch.setattr("sdk.gemini_client.time.sleep", lambda _s: None)

    with patch("google.genai.Client", return_value=MagicMock()):
        response = client.prompt("s", "u")

    assert response.text == "answer"
    assert call_count["n"] == 2


def test_gemini_prompt_expired_key_message(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")
    client = GeminiAgentClient(use_google_search=False, max_retries=1)
    monkeypatch.setattr(
        client,
        "_generate",
        MagicMock(side_effect=RuntimeError("API key expired")),
    )
    with patch("google.genai.Client", return_value=MagicMock()):
        with pytest.raises(RuntimeError, match="expired or invalid"):
            client.prompt("s", "u")


def test_gemini_prompt_all_models_fail(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")
    client = GeminiAgentClient(use_google_search=False, max_retries=1)
    monkeypatch.setattr(
        client,
        "_generate",
        MagicMock(side_effect=RuntimeError("network unreachable")),
    )
    with patch("google.genai.Client", return_value=MagicMock()):
        with pytest.raises(RuntimeError, match="All Gemini models failed"):
            client.prompt("s", "u")


def test_gemini_search_attempts_includes_both_when_enabled(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")
    client = GeminiAgentClient(use_google_search=True)
    assert client._search_attempts() == [True, False]


def test_gemini_generate_with_and_without_search(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")
    client = GeminiAgentClient(use_google_search=False)

    fake_response = MagicMock()
    fake_response.text = "hello"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    text = client._generate(fake_client, "gemini-x", "system", "user", use_search=False)
    assert text == "hello"

    text2 = client._generate(fake_client, "gemini-x", "system", "user", use_search=True)
    assert text2 == "hello"


def test_gemini_generate_empty_response_raises(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey123456789")
    client = GeminiAgentClient(use_google_search=False)

    fake_response = MagicMock()
    fake_response.text = ""
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = fake_response

    with pytest.raises(RuntimeError, match="empty response"):
        client._generate(fake_client, "gemini-x", "s", "u", use_search=False)


def test_is_quota_error_recognises_codes():
    assert _is_quota_error("HTTP 429 too many requests")
    assert _is_quota_error("RESOURCE_EXHAUSTED")
    assert _is_quota_error("QuOtA exceeded")
    assert not _is_quota_error("auth failure")
