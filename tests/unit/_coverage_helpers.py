"""Shared fixtures for the per-module *_coverage.py test files.

Kept in a private module (leading underscore) so pytest does not try
to collect it as a test file. The targeted coverage tests import the
helpers below to avoid duplicating Gatekeeper / DebateMessage
construction in every module.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from debate.config import GatekeeperConfig
from debate.gatekeeper import Gatekeeper
from debate.models import (
    AgentRole,
    Citation,
    DebateMessage,
    DebatePayload,
    MessageType,
)


def make_gatekeeper() -> Gatekeeper:
    """Return a Gatekeeper that never denies (budgets disabled)."""
    return Gatekeeper(
        GatekeeperConfig(enabled=False, max_total_requests=10, max_requests_per_agent=10)
    )


def make_payload(text: str = "hi", ping: int = 1) -> DebatePayload:
    return DebatePayload(
        text=text,
        ping_number=ping,
        citations=[Citation(title="t", url="https://example.com")],
    )


def make_message(
    *,
    msg_type: MessageType = MessageType.TURN,
    from_role: AgentRole = AgentRole.PRO,
    to_role: AgentRole = AgentRole.PARENT,
    session_id: str = "sess",
    ping: int = 1,
) -> DebateMessage:
    return DebateMessage(
        type=msg_type,
        from_role=from_role,
        to_role=to_role,
        session_id=session_id,
        turn_id=1,
        payload=make_payload(ping=ping),
    )


__all__ = ["MagicMock", "make_gatekeeper", "make_message", "make_payload"]
