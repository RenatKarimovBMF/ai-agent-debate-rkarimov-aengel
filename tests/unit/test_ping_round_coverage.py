"""Exercise ``run_ping_round`` end-to-end with fake queues (no processes)."""

from __future__ import annotations

from debate.config import load_config
from debate.models import (
    AgentRole,
    Citation,
    DebateMessage,
    DebatePayload,
    MessageType,
)
from debate.orchestrator.ping_round import run_ping_round

from ._coverage_helpers import FakeQueue


class _FakeParent:
    def __init__(self) -> None:
        self.recorded: list = []

    def record_turn(self, message) -> None:
        self.recorded.append(message)


def _turn(role: AgentRole, text: str, *, with_citation: bool) -> dict:
    citations = [Citation(title="t", url="https://e.com")] if with_citation else []
    msg = DebateMessage(
        type=MessageType.TURN,
        from_role=role,
        to_role=AgentRole.PARENT,
        session_id="sess",
        turn_id=1,
        payload=DebatePayload(text=text, ping_number=1, citations=citations),
    )
    return msg.model_dump(mode="json")


def _run(pro_msg: dict, con_msg: dict):
    parent = _FakeParent()
    parent_to_pro: FakeQueue = FakeQueue()
    parent_to_con: FakeQueue = FakeQueue()
    events: FakeQueue = FakeQueue()
    result = run_ping_round(
        ping=1,
        pings=1,
        config=load_config(),
        session_id="sess",
        parent=parent,
        parent_to_pro=parent_to_pro,
        pro_to_parent=FakeQueue([pro_msg]),
        parent_to_con=parent_to_con,
        con_to_parent=FakeQueue([con_msg]),
        event_queue=events,
        timeout=1.0,
        last_pro=None,
        last_con=None,
    )
    return result, parent, parent_to_pro, parent_to_con


def test_ping_round_with_citations():
    pro = _turn(AgentRole.PRO, "pro text", with_citation=True)
    con = _turn(AgentRole.CON, "con text", with_citation=True)
    (last_pro, last_con), parent, p2pro, p2con = _run(pro, con)

    assert last_pro == "pro text"
    assert last_con == "con text"
    assert len(parent.recorded) == 2
    assert any(c["type"] == "TURN_REQUEST" for c in p2pro.puts)
    assert any(c["type"] == "RELAY" for c in p2con.puts)


def test_ping_round_without_citations():
    pro = _turn(AgentRole.PRO, "pro text", with_citation=False)
    con = _turn(AgentRole.CON, "con text", with_citation=False)
    (last_pro, last_con), _, _, _ = _run(pro, con)
    assert last_pro == "pro text"
    assert last_con == "con text"
