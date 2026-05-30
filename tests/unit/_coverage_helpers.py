"""Shared fixtures for the per-module *_coverage.py test files.

Kept in a private module (leading underscore) so pytest does not try
to collect it as a test file. The targeted coverage tests import the
helpers below to avoid duplicating Gatekeeper / DebateMessage
construction in every module.
"""

from __future__ import annotations

import queue as _queue
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


class FakeQueue:
    """In-process stand-in for ``multiprocessing.Queue``.

    Backed by a list so worker loops can be driven deterministically
    without spawning OS processes. ``get`` raises ``queue.Empty`` when
    drained so ``queue_get_or_timeout`` exercises its timeout branch.
    """

    def __init__(self, items: list | None = None) -> None:
        self.items: list = list(items or [])
        self.puts: list = []

    def put(self, item: object) -> None:
        self.items.append(item)
        self.puts.append(item)

    def get(self, timeout: float | None = None) -> object:
        if not self.items:
            raise _queue.Empty
        return self.items.pop(0)


__all__ = [
    "FakeQueue",
    "MagicMock",
    "make_gatekeeper",
    "make_message",
    "make_payload",
]
