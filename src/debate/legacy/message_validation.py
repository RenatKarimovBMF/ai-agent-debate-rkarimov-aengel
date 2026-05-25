from __future__ import annotations

from debate.models import AgentRole, DebateMessage, MessageType


def require_message(
    message: DebateMessage | None,
    *,
    session_id: str,
    expected_original_sender: AgentRole,
    ping: int,
) -> DebateMessage:
    if message is None:
        raise TimeoutError(
            f"No message received for {expected_original_sender.value} ping {ping}"
        )

    if message.session_id != session_id:
        raise ValueError(f"Wrong session id in message: {message.session_id}")

    if message.payload.ping_number != ping:
        raise ValueError(
            f"Wrong ping number: expected {ping}, got {message.payload.ping_number}"
        )

    if message.type not in {MessageType.TURN, MessageType.RELAY}:
        raise ValueError(f"Unexpected message type: {message.type}")

    if message.type == MessageType.TURN and message.from_role != expected_original_sender:
        raise ValueError(f"Unexpected sender: {message.from_role}")

    if message.type == MessageType.RELAY and message.to_role not in {
        AgentRole.PRO,
        AgentRole.CON,
    }:
        raise ValueError(f"Bad relay target: {message.to_role}")

    return message
