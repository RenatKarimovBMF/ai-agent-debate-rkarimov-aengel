"""Drive ``ProcessDebateOrchestrator.run`` with a fake pool + watchdog.

The real ``DebateProcessPool`` and watchdog are swapped for in-process
fakes so the supervisor event loop is exercised without spawning any OS
processes.
"""
from __future__ import annotations

import queue
from dataclasses import replace
from pathlib import Path

import pytest

from debate.config import load_config
from debate.orchestrator import supervisor as sup

from ._coverage_helpers import FakeQueue


class _Dead:
    def is_alive(self) -> bool:
        return False


class _Alive:
    def is_alive(self) -> bool:
        return True


class _ScriptedEvents:
    """Yield scripted events; the ``"empty"`` sentinel raises queue.Empty."""

    def __init__(self, steps) -> None:
        self.steps = list(steps)

    def get(self, timeout=None):
        step = self.steps.pop(0)
        if step == "empty":
            raise queue.Empty
        return step


class _FakePool:
    def __init__(self, events, processes=None) -> None:
        self.parent_commands: FakeQueue = FakeQueue()
        self.events = events
        self.processes = processes or {}
        self.started = False
        self.stopped = False

    def start_all(self, on_started) -> None:
        self.started = True
        on_started("pro", 11)

    def stop_all(self, on_terminate) -> None:
        self.stopped = True
        on_terminate("pro")


class _FakeWatchdog:
    def __init__(self, *a, **k) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def _orchestrator(monkeypatch, pool, *, timeout=120, callback=None, cancel_event=None):
    monkeypatch.setattr(sup, "setup_logging", lambda *_: None)
    monkeypatch.setattr(sup, "DebateProcessPool", lambda *a, **k: pool)
    monkeypatch.setattr(sup, "ProcessSupervisorWatchdog", _FakeWatchdog)
    cfg = load_config()
    cfg = replace(cfg, debate=replace(cfg.debate, request_timeout_seconds=timeout))
    return sup.ProcessDebateOrchestrator(
        cfg, progress_callback=callback, cancel_event=cancel_event
    )


def test_run_returns_verdict_path_on_done(monkeypatch):
    events = FakeQueue([
        {"kind": "progress", "message": "step", "data": {}},
        {"kind": "done", "message": "ok", "data": {"verdict_path": "logs/v.json"}},
    ])
    seen: list[str] = []
    orch = _orchestrator(monkeypatch, _FakePool(events), callback=seen.append)
    result = orch.run()
    assert result == Path("logs/v.json")
    assert "step" in seen


def test_run_continues_when_queue_empty_but_parent_alive(monkeypatch):
    events = _ScriptedEvents([
        "empty",
        {"kind": "done", "message": "ok", "data": {"verdict_path": "logs/v.json"}},
    ])
    pool = _FakePool(events, processes={"parent": _Alive()})
    orch = _orchestrator(monkeypatch, pool)
    assert orch.run() == Path("logs/v.json")


def test_run_raises_on_error_event(monkeypatch):
    events = FakeQueue([{"kind": "error", "message": "boom", "data": {}}])
    orch = _orchestrator(monkeypatch, _FakePool(events))
    with pytest.raises(RuntimeError, match="boom"):
        orch.run()


def test_run_detects_dead_parent_on_empty_queue(monkeypatch):
    pool = _FakePool(FakeQueue([]), processes={"parent": _Dead()})
    orch = _orchestrator(monkeypatch, pool)
    with pytest.raises(RuntimeError, match="Parent process stopped"):
        orch.run()


def test_run_global_timeout(monkeypatch):
    orch = _orchestrator(monkeypatch, _FakePool(FakeQueue([])), timeout=-1)
    with pytest.raises(TimeoutError, match="global timeout"):
        orch.run()


def test_start_and_stop_watchdogs_delegate(monkeypatch):
    orch = _orchestrator(monkeypatch, _FakePool(FakeQueue([])))
    orch.start_watchdogs()
    orch.stop_watchdogs()
    assert orch._watchdog.started and orch._watchdog.stopped


def test_run_raises_when_cancelled_via_event(monkeypatch):
    import threading

    from debate.orchestrator.types import DebateCancelled
    cancel = threading.Event()
    cancel.set()
    pool = _FakePool(FakeQueue([]))
    orch = _orchestrator(monkeypatch, pool, cancel_event=cancel)
    with pytest.raises(DebateCancelled, match="stopped by user"):
        orch.run()
    assert pool.stopped  # finally-block cleanup still ran


def test_request_stop_sets_default_event(monkeypatch):
    orch = _orchestrator(monkeypatch, _FakePool(FakeQueue([])))
    orch.request_stop()
    assert orch._cancel.is_set()
