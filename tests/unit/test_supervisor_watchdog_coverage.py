"""Cover ``ProcessSupervisorWatchdog`` start/stop and the monitor loop.

``start``/``stop`` use a real (fast) thread; the loop-body branches are
driven by calling ``_loop`` directly with a controlled stop-event so no
timing races occur.
"""

from __future__ import annotations

from debate.orchestrator.supervisor_watchdog import ProcessSupervisorWatchdog


class _Proc:
    def __init__(self, alive: bool) -> None:
        self._alive = alive

    def is_alive(self) -> bool:
        return self._alive


class _FakePool:
    def __init__(self, processes) -> None:
        self.processes = processes
        self.restarted: list[str] = []

    def restart_child(self, name, on_started) -> None:
        self.restarted.append(name)
        on_started(name, 99)


class _OneShotStop:
    """Stop-event whose ``wait`` returns False once, then True."""

    def __init__(self) -> None:
        self.calls = 0

    def wait(self, _interval) -> bool:
        self.calls += 1
        return self.calls > 1


def _watchdog(pool, messages):
    wd = ProcessSupervisorWatchdog(pool, interval_seconds=2, on_message=messages.append)
    wd._stop = _OneShotStop()
    return wd


def test_start_and_stop_use_a_thread():
    pool = _FakePool({"parent": _Proc(True)})
    messages: list[str] = []
    wd = ProcessSupervisorWatchdog(pool, interval_seconds=2, on_message=messages.append)
    wd.start()
    wd.stop()
    assert "WATCHDOG: process watchdog started" in messages
    assert "WATCHDOG: process watchdog stopped" in messages


def test_loop_reports_dead_parent_and_returns():
    pool = _FakePool({"parent": _Proc(False)})
    messages: list[str] = []
    _watchdog(pool, messages)._loop()
    assert any("parent process died" in m for m in messages)
    assert pool.restarted == []


def test_loop_restarts_dead_child():
    pool = _FakePool({
        "parent": _Proc(True),
        "pro": _Proc(False),
        "con": _Proc(True),
    })
    messages: list[str] = []
    _watchdog(pool, messages)._loop()
    assert pool.restarted == ["pro"]
    assert any("restarted pro" in m for m in messages)


def test_loop_no_action_when_all_alive():
    pool = _FakePool({
        "parent": _Proc(True),
        "pro": _Proc(True),
        "con": _Proc(True),
    })
    messages: list[str] = []
    _watchdog(pool, messages)._loop()
    assert pool.restarted == []
