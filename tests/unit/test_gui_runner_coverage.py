"""Cover the debate runner without spawning real OS threads.

The worker body (`run_debate`) is exercised synchronously; `start_debate_thread`
is checked with a fake `Thread`. Real background threads are avoided because
they crash coverage's tracer during GC on the CI runner (SIGILL / exit 132).
"""

from __future__ import annotations

from pathlib import Path

from debate.gui import runner


class _FakeOrchestrator:
    def __init__(self, config, progress_callback=None, cancel_event=None) -> None:
        self.progress_callback = progress_callback
        self.cancel_event = cancel_event

    def start_watchdogs(self) -> None:
        return None

    def stop_watchdogs(self) -> None:
        return None

    def run(self) -> Path:
        if self.progress_callback:
            self.progress_callback("running")
        return Path("logs/v.json")


def _run(monkeypatch, orchestrator_cls):
    monkeypatch.setattr(runner, "ProcessDebateOrchestrator", orchestrator_cls)
    result: dict = {}
    logs: list[str] = []
    runner.run_debate(
        "Cats", "Dogs", "Best pet?", logs.append,
        lambda path, error: result.update(path=path, error=error),
    )
    return result, logs


def test_run_debate_success_path(monkeypatch):
    result, logs = _run(monkeypatch, _FakeOrchestrator)
    assert result["path"] == Path("logs/v.json")
    assert result["error"] is None
    assert "running" in logs


def test_run_debate_reports_exception(monkeypatch):
    class _Boom(_FakeOrchestrator):
        def run(self):
            raise RuntimeError("kaboom")

    result, _ = _run(monkeypatch, _Boom)
    assert result["path"] is None
    assert isinstance(result["error"], RuntimeError)


def test_start_debate_thread_spawns_daemon(monkeypatch):
    class _FakeThread:
        def __init__(self, target=None, args=(), daemon=False) -> None:
            self.target, self.args, self.daemon = target, args, daemon
            self.started = False

        def start(self) -> None:
            self.started = True  # never actually runs the target

    monkeypatch.setattr(runner.threading, "Thread", _FakeThread)
    thread = runner.start_debate_thread(
        pro="a", con="b", topic="q",
        queue_log=lambda _m: None, on_done=lambda _p, _e: None,
    )
    assert thread.started is True
    assert thread.daemon is True
    assert thread.target is runner.run_debate
