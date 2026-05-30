"""Cover ``start_debate_thread`` worker (success + failure) without an LLM.

The orchestrator is faked; the helper still spawns a real daemon thread,
so we synchronise on the ``on_done`` callback.
"""

from __future__ import annotations

import threading
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


def _wait_for_done(monkeypatch, orchestrator_cls):
    monkeypatch.setattr(runner, "ProcessDebateOrchestrator", orchestrator_cls)
    done = threading.Event()
    result: dict = {}

    def on_done(path, error):
        result["path"] = path
        result["error"] = error
        done.set()

    logs: list[str] = []
    thread = runner.start_debate_thread(
        pro="Cats", con="Dogs", topic="Best pet?",
        queue_log=logs.append, on_done=on_done,
    )
    assert done.wait(timeout=5), "worker thread did not finish"
    # Join so no daemon thread lingers into later tests (lingering threads
    # crash under coverage's tracer during GC — see CI SIGILL).
    thread.join(timeout=5)
    return result, logs


def test_worker_success_path(monkeypatch):
    result, logs = _wait_for_done(monkeypatch, _FakeOrchestrator)
    assert result["path"] == Path("logs/v.json")
    assert result["error"] is None
    assert "running" in logs


def test_worker_reports_exception(monkeypatch):
    class _Boom(_FakeOrchestrator):
        def run(self):
            raise RuntimeError("kaboom")

    result, _ = _wait_for_done(monkeypatch, _Boom)
    assert result["path"] is None
    assert isinstance(result["error"], RuntimeError)