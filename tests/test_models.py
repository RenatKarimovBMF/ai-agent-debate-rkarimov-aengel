import pytest

from debate.models import (
    AgentRole,
    DebateMessage,
    DebatePayload,
    MessageType,
    VerdictMessage,
    VerdictPayload,
)


def test_debate_message_roundtrip():
    msg = DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.PARENT,
        session_id="abc",
        turn_id=1,
        payload=DebatePayload(text="Godfather defined modern cinema.", ping_number=1),
    )
    restored = DebateMessage.from_json_line(msg.to_json_line())
    assert restored.payload.text == msg.payload.text


def test_verdict_requires_different_scores():
    v = VerdictMessage(
        session_id="x",
        payload=VerdictPayload(
            winner=AgentRole.PRO,
            pro_score=80,
            con_score=70,
            rationale="Stronger rebuttals",
            persuasion_notes="Pro cited legacy sources",
        ),
    )
    assert v.payload.winner == AgentRole.PRO
