from __future__ import annotations

import pytest

from debate.config import load_config
from debate.gatekeeper import Gatekeeper
from debate.legacy.helpers import short_text
from debate.legacy.message_validation import require_message
from debate.legacy.setup import build_legacy_agents, clear_ipc_queues
from debate.models import AgentRole, DebateMessage, DebatePayload, MessageType
from sdk.llm_client import LlmClient


def test_legacy_short_text():
    assert short_text("one two three", limit=10) == "one two th..."


def test_require_message_accepts_relay():
    message = DebateMessage(
        type=MessageType.RELAY,
        from_role=AgentRole.PARENT,
        to_role=AgentRole.CON,
        session_id="abc",
        turn_id=1,
        payload=DebatePayload(text="relay", ping_number=1),
    )
    result = require_message(
        message,
        session_id="abc",
        expected_original_sender=AgentRole.PRO,
        ping=1,
    )
    assert result.type == MessageType.RELAY


def test_require_message_rejects_none():
    with pytest.raises(TimeoutError):
        require_message(
            None,
            session_id="abc",
            expected_original_sender=AgentRole.PRO,
            ping=1,
        )


def test_build_legacy_agents_and_clear_queues(tmp_path):
    from dataclasses import replace

    config = replace(load_config(), project_root=tmp_path)

    clear_ipc_queues(config)
    fifo = tmp_path / config.ipc.fifo_dir
    assert fifo.is_dir()

    gk = Gatekeeper(config.gatekeeper)
    client = LlmClient()
    agents = build_legacy_agents(config, "sess", gk, client)
    assert agents.pro.role == AgentRole.PRO
    assert agents.con.role == AgentRole.CON
    agents.pro_channels.close()
    agents.con_channels.close()
