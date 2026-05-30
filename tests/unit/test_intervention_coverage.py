"""Cover the judge's mid-debate intervention (`orchestrator.intervention`)."""

from __future__ import annotations

from debate.models import (
    AgentRole,
    Citation,
    DebateMessage,
    DebatePayload,
    MessageType,
)
from debate.orchestrator.intervention import capitulation_warning, solicit_turn

from ._coverage_helpers import FakeQueue


def _turn(text: str, role: AgentRole = AgentRole.CON) -> dict:
    msg = DebateMessage(
        type=MessageType.TURN,
        from_role=role,
        to_role=AgentRole.PARENT,
        session_id="sess",
        turn_id=1,
        payload=DebatePayload(
            text=text,
            ping_number=1,
            citations=[Citation(title="t", url="https://e.com")],
        ),
    )
    return msg.model_dump(mode="json")


def test_capitulation_warning_detects_full_surrender():
    assert capitulation_warning("Honestly, you are right about all of it.") is not None


def test_capitulation_warning_allows_minor_concession():
    assert capitulation_warning("I concede that point, but my case still stands.") is None


def test_solicit_turn_returns_first_when_compliant():
    resp = FakeQueue([_turn("My side clearly wins on the evidence.")])
    req: FakeQueue = FakeQueue()
    events: FakeQueue = FakeQueue()

    msg = solicit_turn(
        role=AgentRole.CON,
        ping=1,
        opponent_text=None,
        request_queue=req,
        response_queue=resp,
        session_id="sess",
        event_queue=events,
        timeout=1.0,
    )

    assert "wins" in msg.payload.text
    assert len(req.puts) == 1
    assert not any(e["kind"] == "host" for e in events.puts)


def test_solicit_turn_warns_and_re_requests():
    resp = FakeQueue([
        _turn("You are right, I agree with you completely."),
        _turn("No — my side wins; per AFI my position holds."),
    ])
    req: FakeQueue = FakeQueue()
    events: FakeQueue = FakeQueue()

    msg = solicit_turn(
        role=AgentRole.CON,
        ping=1,
        opponent_text="x",
        request_queue=req,
        response_queue=resp,
        session_id="sess",
        event_queue=events,
        timeout=1.0,
    )

    assert "my side wins" in msg.payload.text
    assert len(req.puts) == 2
    assert req.puts[1]["correction"]
    assert any(e["kind"] == "host" for e in events.puts)
