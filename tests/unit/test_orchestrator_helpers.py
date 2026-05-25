from __future__ import annotations

import multiprocessing as mp

import pytest

from debate.models import AgentRole, DebateMessage, DebatePayload, MessageType
from debate.orchestrator.commands import relay_message, turn_request, worker_error
from debate.orchestrator.events import emit_event, queue_get_or_timeout, short_text
from debate.orchestrator.messages import validate_child_message


def test_short_text_truncates():
    assert short_text("a " * 500, limit=20).endswith("...")


def test_emit_event_puts_payload():
    q: mp.Queue = mp.Queue()
    emit_event(q, "hello", kind="progress", data={"x": 1})
    item = q.get(timeout=1)
    assert item["message"] == "hello"
    assert item["kind"] == "progress"


def test_queue_get_or_timeout_raises():
    q: mp.Queue = mp.Queue()
    with pytest.raises(TimeoutError, match="PRO response"):
        queue_get_or_timeout(q, 0.1, "PRO response")


def test_command_helpers():
    assert turn_request(2, "text")["ping"] == 2
    assert relay_message({})["type"] == "RELAY"
    assert worker_error("pro", "boom")["error"] == "boom"


def test_validate_child_message_error_dict():
    with pytest.raises(RuntimeError, match="worker failed"):
        validate_child_message(
            {"type": "ERROR", "role": "pro", "error": "boom"},
            expected_sender=AgentRole.PRO,
            session_id="abc",
            ping=1,
        )


def test_validate_child_message_wrong_session():
    message = DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.PARENT,
        session_id="other",
        turn_id=1,
        payload=DebatePayload(text="x", ping_number=1),
    )
    with pytest.raises(ValueError, match="Wrong session"):
        validate_child_message(
            message.model_dump(mode="json"),
            expected_sender=AgentRole.PRO,
            session_id="abc",
            ping=1,
        )
