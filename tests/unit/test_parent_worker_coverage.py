"""Drive ``parent_worker`` in-process with fakes for every collaborator."""

from __future__ import annotations

from dataclasses import replace

import pytest

from debate.config import load_config
from debate.models import AgentRole
from debate.orchestrator import parent_worker as pw

from ._coverage_helpers import FakeQueue


class _FakeParent:
    def __init__(self) -> None:
        self.sides: tuple[str, str] | None = None

    def apply_assignment(self, *, pro_side: str, con_side: str) -> None:
        self.sides = (pro_side, con_side)

    def transcript_text(self) -> str:
        return "full transcript"

    def render_verdict(self) -> str:
        return "verdict"


def _config(pings: int):
    cfg = load_config()
    return replace(cfg, debate=replace(cfg.debate, pings_per_side=pings))


@pytest.fixture
def patched(monkeypatch):
    calls = {"ping_rounds": 0, "saved": None}
    monkeypatch.setattr(pw, "setup_logging", lambda *_: None)
    monkeypatch.setattr(pw, "create_parent_agent", lambda *a, **k: _FakeParent())
    monkeypatch.setattr(
        pw,
        "send_assignments",
        lambda **k: {AgentRole.PRO: "A", AgentRole.CON: "B"},
    )

    def fake_round(**kwargs):
        calls["ping_rounds"] += 1
        return ("pro", "con")

    monkeypatch.setattr(pw, "run_ping_round", fake_round)
    monkeypatch.setattr(pw, "write_transcript", lambda cfg, sid, text: None)
    monkeypatch.setattr(
        pw,
        "save_verdict",
        lambda cfg, sid, verdict, eq: calls.__setitem__("saved", verdict),
    )
    return calls


def _queues():
    return {name: FakeQueue() for name in (
        "parent_to_pro", "pro_to_parent", "parent_to_con", "con_to_parent",
    )}


def test_parent_worker_runs_full_session(patched):
    q = _queues()
    events: FakeQueue = FakeQueue()
    pw.parent_worker(
        _config(2),
        "sess",
        FakeQueue([{"type": "START"}]),
        events,
        q["parent_to_pro"],
        q["pro_to_parent"],
        q["parent_to_con"],
        q["con_to_parent"],
    )

    assert patched["ping_rounds"] == 2
    assert patched["saved"] == "verdict"
    assert q["parent_to_pro"].puts[-1] == {"type": "STOP"}
    assert q["parent_to_con"].puts[-1] == {"type": "STOP"}


def test_parent_worker_rejects_non_start(patched):
    q = _queues()
    events: FakeQueue = FakeQueue()
    pw.parent_worker(
        _config(1),
        "sess",
        FakeQueue([{"type": "NOPE"}]),
        events,
        q["parent_to_pro"],
        q["pro_to_parent"],
        q["parent_to_con"],
        q["con_to_parent"],
    )

    assert patched["ping_rounds"] == 0
    assert any(e["kind"] == "error" for e in events.puts)
    assert q["parent_to_pro"].puts[-1] == {"type": "STOP"}
