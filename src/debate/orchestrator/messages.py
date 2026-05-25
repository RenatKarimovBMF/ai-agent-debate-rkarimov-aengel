from __future__ import annotations

from typing import Any

from debate.models import AgentRole, DebateMessage, MessageType
from debate.orchestrator.commands import ERROR


def validate_child_message(
    raw: Any,
    *,
    expected_sender: AgentRole,
    session_id: str,
    ping: int,
) -> DebateMessage:
    if isinstance(raw, dict) and raw.get("type") == ERROR:
        raise RuntimeError(f"{raw.get('role')} worker failed: {raw.get('error')}")

    message = DebateMessage.model_validate(raw)

    if message.session_id != session_id:
        raise ValueError(f"Wrong session id: {message.session_id}")

    if message.type != MessageType.TURN:
        raise ValueError(f"Expected TURN message, got {message.type}")

    if message.from_role != expected_sender:
        raise ValueError(f"Expected sender {expected_sender}, got {message.from_role}")

    if message.to_role != AgentRole.PARENT:
        raise ValueError(f"Child messages must go to parent, got {message.to_role}")

    if message.payload.ping_number != ping:
        raise ValueError(
            f"Wrong ping number: expected {ping}, got {message.payload.ping_number}"
        )

    return message


def make_relay(message: DebateMessage, target: AgentRole) -> DebateMessage:
    return message.model_copy(
        update={
            "type": MessageType.RELAY,
            "from_role": AgentRole.PARENT,
            "to_role": target,
        }
    )
