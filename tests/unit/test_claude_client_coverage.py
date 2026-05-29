"""Targeted branch coverage for `sdk.claude_client.ClaudeAgentClient`.

Covers the timeout and non-zero-exit branches of the CLI path, plus
the API path's missing-key and missing-package branches.
"""

from __future__ import annotations

import subprocess as _sp

import pytest

from sdk.claude_client import ClaudeAgentClient

from ._coverage_helpers import MagicMock


def test_claude_available_false_for_missing_cli(monkeypatch):
    monkeypatch.setattr("sdk.claude_client.shutil.which", lambda c: None)
    client = ClaudeAgentClient(cli_command="definitely-not-a-real-cli")
    assert client.available() is False


def test_claude_available_true_when_resolvable(monkeypatch):
    monkeypatch.setattr("sdk.claude_client.shutil.which", lambda c: "C:/claude.CMD")
    client = ClaudeAgentClient()
    assert client.available() is True


def test_claude_prompt_cli_timeout(monkeypatch):
    monkeypatch.setattr(
        "sdk.claude_client.subprocess.run",
        MagicMock(side_effect=_sp.TimeoutExpired(cmd="claude", timeout=1)),
    )
    client = ClaudeAgentClient(cli_command="claude", timeout_seconds=1)
    with pytest.raises(TimeoutError, match="Claude CLI timed out"):
        client.prompt("s", "u")


def test_claude_prompt_cli_non_zero_exit(monkeypatch):
    completed = MagicMock()
    completed.returncode = 2
    completed.stdout = ""
    completed.stderr = "broken"
    monkeypatch.setattr("sdk.claude_client.subprocess.run", MagicMock(return_value=completed))
    client = ClaudeAgentClient(cli_command="claude")
    with pytest.raises(RuntimeError, match="broken"):
        client.prompt("s", "u")


def test_claude_prompt_api_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = ClaudeAgentClient()
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY not set"):
        client.prompt_api("s", "u")


def test_claude_prompt_api_handles_missing_package(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "anthropic":
            raise ImportError("no module")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    client = ClaudeAgentClient()
    with pytest.raises(RuntimeError, match="'anthropic' is not installed"):
        client.prompt_api("s", "u")
