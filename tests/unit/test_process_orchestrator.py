from __future__ import annotations

from debate.models import AgentRole, DebateMessage, DebatePayload, MessageType
from debate.orchestrator.messages import make_relay, validate_child_message


def test_make_relay_goes_through_parent() -> None:
    original = DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.PARENT,
        session_id="abc123",
        turn_id=1,
        payload=DebatePayload(
            text="Argument",
            ping_number=1,
            citations=[],
        ),
    )

    relay = make_relay(original, AgentRole.CON)

    assert relay.type == MessageType.RELAY
    assert relay.from_role == AgentRole.PARENT
    assert relay.to_role == AgentRole.CON
    assert relay.payload.text == "Argument"


def test_validate_child_message_accepts_correct_turn() -> None:
    message = DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.PARENT,
        session_id="abc123",
        turn_id=1,
        payload=DebatePayload(
            text="Argument",
            ping_number=1,
            citations=[],
        ),
    )

    result = validate_child_message(
        message.model_dump(mode="json"),
        expected_sender=AgentRole.PRO,
        session_id="abc123",
        ping=1,
    )

    assert result.from_role == AgentRole.PRO
    assert result.to_role == AgentRole.PARENT


def test_validate_child_message_rejects_direct_child_to_child_message() -> None:
    message = DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.CON,
        session_id="abc123",
        turn_id=1,
        payload=DebatePayload(
            text="Bad direct message",
            ping_number=1,
            citations=[],
        ),
    )

    try:
        validate_child_message(
            message.model_dump(mode="json"),
            expected_sender=AgentRole.PRO,
            session_id="abc123",
            ping=1,
        )
    except ValueError as exc:
        assert "Child messages must go to parent" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
