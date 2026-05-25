from __future__ import annotations

import pytest

from debate.legacy.message_validation import require_message
from debate.models import AgentRole, DebateMessage, DebatePayload, MessageType


def _message(**updates) -> DebateMessage:
    base = DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.PARENT,
        session_id="abc",
        turn_id=1,
        payload=DebatePayload(text="x", ping_number=1),
    )
    return base.model_copy(update=updates)


def test_require_message_wrong_session():
    with pytest.raises(ValueError, match="Wrong session"):
        require_message(
            _message(session_id="other"),
            session_id="abc",
            expected_original_sender=AgentRole.PRO,
            ping=1,
        )


def test_require_message_wrong_ping():
    with pytest.raises(ValueError, match="Wrong ping number"):
        require_message(
            _message(payload=DebatePayload(text="x", ping_number=2)),
            session_id="abc",
            expected_original_sender=AgentRole.PRO,
            ping=1,
        )


def test_require_message_bad_type():
    with pytest.raises(ValueError, match="Unexpected message type"):
        require_message(
            _message(type=MessageType.VERDICT),
            session_id="abc",
            expected_original_sender=AgentRole.PRO,
            ping=1,
        )


def test_require_message_bad_sender_on_turn():
    with pytest.raises(ValueError, match="Unexpected sender"):
        require_message(
            _message(from_role=AgentRole.CON),
            session_id="abc",
            expected_original_sender=AgentRole.PRO,
            ping=1,
        )


def test_require_message_bad_relay_target():
    with pytest.raises(ValueError, match="Bad relay target"):
        require_message(
            _message(type=MessageType.RELAY, to_role=AgentRole.PARENT),
            session_id="abc",
            expected_original_sender=AgentRole.PRO,
            ping=1,
        )
