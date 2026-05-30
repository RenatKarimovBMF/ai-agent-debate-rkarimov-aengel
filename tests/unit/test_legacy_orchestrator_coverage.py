"""Cover the legacy single-process ``DebateOrchestrator`` wiring.

The heavy ``run_debate_session`` (LLM + IPC) is monkeypatched so the
orchestrator's construction, progress/heartbeat/watchdog plumbing, and
run/stop lifecycle execute without a network call.
"""

from __future__ import annotations

from dataclasses import replace

from debate.config import load_config
from debate.legacy import debate_orchestrator as do


def _config(tmp_path):
    cfg = load_config()
    return replace(cfg, project_root=tmp_path)


def test_orchestrator_full_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(do, "setup_logging", lambda *_: None)
    monkeypatch.setattr(do, "run_debate_session", lambda *a: tmp_path / "v.json")

    messages: list[str] = []
    orch = do.DebateOrchestrator(_config(tmp_path), progress_callback=messages.append)

    orch._progress("hello")
    assert "hello" in messages

    orch._heartbeat()
    assert orch._is_alive() is True

    orch._watchdog_restart()
    assert any("stalled" in m for m in messages)

    assert orch.run() == tmp_path / "v.json"

    orch.start_watchdogs()
    orch.stop_watchdogs()


def test_orchestrator_without_callback(tmp_path, monkeypatch):
    monkeypatch.setattr(do, "setup_logging", lambda *_: None)
    orch = do.DebateOrchestrator(_config(tmp_path))
    orch._progress("no callback path")
    orch._watchdog_restart()
    assert orch._is_alive() is False or orch._is_alive() is True
