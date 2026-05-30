"""Test ``DebateProcessPool`` with a fake mp context (no real processes)."""

from __future__ import annotations

from debate.config import load_config
from debate.orchestrator.process_pool import DebateProcessPool

from ._coverage_helpers import FakeQueue


class _FakeProcess:
    def __init__(self, *, name=None, target=None, args=(), alive=True) -> None:
        self.name = name
        self.target = target
        self.args = args
        self.pid = 4321
        self.started = False
        self.terminated = False
        self._alive_after_start = alive
        self._alive = False

    def start(self) -> None:
        self.started = True
        self._alive = self._alive_after_start

    def is_alive(self) -> bool:
        return self._alive

    def join(self, timeout=None) -> None:
        return None

    def terminate(self) -> None:
        self.terminated = True


class _FakeCtx:
    def __init__(self, alive: bool = True) -> None:
        self.alive = alive
        self.processes: list[_FakeProcess] = []

    def Queue(self) -> FakeQueue:
        return FakeQueue()

    def Process(self, *, name, target, args) -> _FakeProcess:
        proc = _FakeProcess(name=name, target=target, args=args, alive=self.alive)
        self.processes.append(proc)
        return proc


def _pool(alive: bool = True) -> DebateProcessPool:
    return DebateProcessPool(_FakeCtx(alive), load_config(), "sess")


def test_start_all_and_stop_all_terminates_live_processes():
    pool = _pool(alive=True)
    started: list[tuple[str, int]] = []
    pool.start_all(lambda name, pid: started.append((name, pid)))

    assert set(pool.processes) == {"pro", "con", "parent"}
    assert {n for n, _ in started} == {"pro", "con", "parent"}

    terminated: list[str] = []
    pool.stop_all(terminated.append)
    assert sorted(terminated) == ["con", "parent", "pro"]
    assert all(p.terminated for p in pool.processes.values())


def test_stop_all_skips_dead_processes():
    pool = _pool(alive=False)
    pool.start_all(lambda name, pid: None)
    terminated: list[str] = []
    pool.stop_all(terminated.append)
    assert terminated == []


def test_restart_existing_child_replaces_process():
    pool = _pool(alive=True)
    pool.start_all(lambda name, pid: None)
    old = pool.processes["pro"]

    restarted: list[tuple[str, int]] = []
    pool.restart_child("pro", lambda name, pid: restarted.append((name, pid)))

    assert old.terminated
    assert pool.processes["pro"] is not old
    assert restarted == [("pro", 4321)]


def test_restart_unknown_name_is_noop():
    pool = _pool()
    pool.restart_child("parent", lambda name, pid: None)
    assert "parent" not in pool.processes


def test_restart_child_with_no_existing_process():
    pool = _pool(alive=True)
    started: list[str] = []
    pool.restart_child("con", lambda name, pid: started.append(name))
    assert started == ["con"]
    assert pool.processes["con"].started


def test_stop_all_swallows_queue_put_errors():
    pool = _pool(alive=False)
    pool.start_all(lambda name, pid: None)

    class _Raising:
        def put(self, item):
            raise RuntimeError("queue closed")

    pool.parent_to_pro = _Raising()
    pool.stop_all(lambda name: None)
