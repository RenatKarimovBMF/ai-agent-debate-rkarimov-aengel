"""Drive ``child_worker`` in-process with fake queues and a fake agent.

No OS process is spawned: commands are pre-loaded into a ``FakeQueue``
ending in STOP so the ``while True`` loop terminates deterministically.
"""

from __future__ import annotations

import pytest

from debate.config import load_config
from debate.models import AgentRole, MessageType
from debate.orchestrator import child_worker as cw
from debate.orchestrator.commands import assignment, relay_message, turn_request

from ._coverage_helpers import FakeQueue, make_message


class _FakeAgent:
    def __init__(self) -> None:
        self.assignment: tuple[str, str] | None = None
        self.turns: list[tuple[int, str | None]] = []

    def apply_assignment(self, assigned: str, opponent: str) -> None:
        self.assignment = (assigned, opponent)

    def build_turn(self, ping: int, opponent_text: str | None, correction=None):
        self.turns.append((ping, opponent_text))
        return make_message(ping=ping)


@pytest.fixture
def patched(monkeypatch):
    agent = _FakeAgent()
    monkeypatch.setattr(cw, "setup_logging", lambda *_: None)
    monkeypatch.setattr(cw, "create_child_agent", lambda *a, **k: agent)
    return agent


def _run(commands: list, agent_to_parent: FakeQueue, events: FakeQueue) -> None:
    cw.child_worker(
        AgentRole.PRO.value,
        load_config(),
        "sess",
        FakeQueue(commands),
        agent_to_parent,
        events,
    )


def test_child_worker_handles_all_command_types(patched):
    relay = make_message(msg_type=MessageType.RELAY, from_role=AgentRole.PRO)
    out: FakeQueue = FakeQueue()
    events: FakeQueue = FakeQueue()
    commands = [
        "not-a-dict",
        assignment(
            role="pro", topic="t", assigned_side="A", opponent_side="B",
            pings=1, max_words=10, rules=["r"],
        ),
        relay_message(relay.model_dump(mode="json")),
        turn_request(1, "prev"),
        turn_request(2, None),
        {"type": "UNKNOWN"},
        {"type": "STOP"},
    ]
    _run(commands, out, events)

    assert patched.assignment == ("A", "B")
    assert patched.turns == [(1, "prev"), (2, "hi")]
    assert len(out.puts) == 2
    kinds = [e["kind"] for e in events.puts]
    assert "host" in kinds and "llm_start" in kinds and "llm_done" in kinds


def test_child_worker_reports_build_failure(monkeypatch, patched):
    def boom(*_a, **_k):
        raise ValueError("kaboom")

    monkeypatch.setattr(patched, "build_turn", boom)
    out: FakeQueue = FakeQueue()
    events: FakeQueue = FakeQueue()
    _run([turn_request(1, "x"), {"type": "STOP"}], out, events)

    assert out.puts[0]["type"] == "ERROR"
    assert "kaboom" in out.puts[0]["error"]
    assert any(e["kind"] == "error" for e in events.puts)
