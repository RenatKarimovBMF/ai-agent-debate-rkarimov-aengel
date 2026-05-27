"""Targeted branch coverage for `debate.orchestrator.factory` and
`debate.orchestrator.messages` (child message validation + relay).
"""

from __future__ import annotations

import pytest

from debate.config import load_config
from debate.models import AgentRole, MessageType
from debate.orchestrator.commands import ERROR
from debate.orchestrator.factory import (
    NoopTransport,
    create_child_agent,
    create_parent_agent,
)
from debate.orchestrator.messages import make_relay, validate_child_message

from ._coverage_helpers import make_message


def test_factory_noop_transport_is_inert():
    t = NoopTransport()
    assert t.write(make_message()) is None
    assert t.read(timeout=0.0) is None
    assert t.close() is None


def test_factory_create_child_agent_pro_and_con(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    cfg = load_config()
    pro = create_child_agent(AgentRole.PRO, cfg, "sess")
    con = create_child_agent(AgentRole.CON, cfg, "sess")
    assert pro.role == AgentRole.PRO
    assert con.role == AgentRole.CON


def test_factory_create_child_agent_rejects_parent(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    cfg = load_config()
    with pytest.raises(ValueError, match="Child worker cannot use role"):
        create_child_agent(AgentRole.PARENT, cfg, "sess")


def test_factory_create_parent_agent_returns_parent(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy1234567890abcdef")
    cfg = load_config()
    parent = create_parent_agent(cfg, "sess")
    assert parent.role == AgentRole.PARENT


def test_validate_child_message_rejects_error_dict():
    bad = {"type": ERROR, "role": "pro", "error": "boom"}
    with pytest.raises(RuntimeError, match="pro worker failed"):
        validate_child_message(bad, expected_sender=AgentRole.PRO, session_id="s", ping=1)


def test_validate_child_message_rejects_wrong_session():
    msg = make_message(session_id="other").model_dump(mode="json")
    with pytest.raises(ValueError, match="Wrong session id"):
        validate_child_message(msg, expected_sender=AgentRole.PRO, session_id="s", ping=1)


def test_validate_child_message_rejects_non_turn_type():
    msg = make_message(msg_type=MessageType.RELAY).model_dump(mode="json")
    with pytest.raises(ValueError, match="Expected TURN message"):
        validate_child_message(msg, expected_sender=AgentRole.PRO, session_id="sess", ping=1)


def test_validate_child_message_rejects_wrong_sender():
    msg = make_message(from_role=AgentRole.CON).model_dump(mode="json")
    with pytest.raises(ValueError, match="Expected sender"):
        validate_child_message(msg, expected_sender=AgentRole.PRO, session_id="sess", ping=1)


def test_validate_child_message_rejects_wrong_recipient():
    msg = make_message(to_role=AgentRole.CON).model_dump(mode="json")
    with pytest.raises(ValueError, match="must go to parent"):
        validate_child_message(msg, expected_sender=AgentRole.PRO, session_id="sess", ping=1)


def test_validate_child_message_rejects_wrong_ping():
    msg = make_message(ping=2).model_dump(mode="json")
    with pytest.raises(ValueError, match="Wrong ping number"):
        validate_child_message(msg, expected_sender=AgentRole.PRO, session_id="sess", ping=1)


def test_validate_child_message_accepts_valid():
    msg = make_message().model_dump(mode="json")
    result = validate_child_message(
        msg, expected_sender=AgentRole.PRO, session_id="sess", ping=1
    )
    assert result.type == MessageType.TURN


def test_make_relay_swaps_metadata():
    relayed = make_relay(make_message(), AgentRole.CON)
    assert relayed.type == MessageType.RELAY
    assert relayed.from_role == AgentRole.PARENT
    assert relayed.to_role == AgentRole.CON
