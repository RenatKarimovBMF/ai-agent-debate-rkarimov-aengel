"""Drive ``debate.main.main`` across every CLI branch in-process."""

from __future__ import annotations

from pathlib import Path

import pytest

from debate import main as main_mod


class _FakeClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def active_provider(self) -> str:
        return "gemini"


class _FakeOrchestrator:
    last: _FakeOrchestrator | None = None

    def __init__(self, config) -> None:
        self.config = config
        self.started = False
        self.stopped = False
        _FakeOrchestrator.last = self

    def start_watchdogs(self) -> None:
        self.started = True

    def run(self) -> Path:
        return Path("logs/verdict_test.json")

    def stop_watchdogs(self) -> None:
        self.stopped = True


def test_version_flag_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main_mod.main(["--version"])
    assert exc.value.code == 0


def test_dry_run_prints_summary(monkeypatch, capsys):
    monkeypatch.setattr("sdk.llm_client.LlmClient", _FakeClient)
    rc = main_mod.main(["--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "LLM provider: gemini" in out
    assert "Execution mode: real multiprocessing agents" in out


def test_dry_run_with_custom_debate(monkeypatch, capsys):
    monkeypatch.setattr("sdk.llm_client.LlmClient", _FakeClient)
    rc = main_mod.main(
        ["--dry-run", "--pro", "Cats", "--con", "Dogs", "--topic", "Best pet?"]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "Best pet?" in out
    assert "Cats" in out and "Dogs" in out


def test_gui_flag_delegates(monkeypatch):
    monkeypatch.setattr("debate.gui.main", lambda: 7, raising=False)
    assert main_mod.main(["--gui"]) == 7


def test_full_run_uses_orchestrator(monkeypatch, capsys):
    monkeypatch.setattr(main_mod, "ProcessDebateOrchestrator", _FakeOrchestrator)
    rc = main_mod.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Debate finished. Verdict written to:" in out
    assert _FakeOrchestrator.last is not None
    assert _FakeOrchestrator.last.started
    assert _FakeOrchestrator.last.stopped
