from __future__ import annotations

import queue

import pytest

from debate.config import load_config
from debate.models import AgentRole, MessageType, VerdictMessage, VerdictPayload, message_from_dict
from debate.orchestrator.factory import create_child_agent, create_parent_agent, make_llm_client
from debate.orchestrator.verdict_io import save_verdict
from sdk.llm_client import LlmClient


def test_message_from_dict_verdict():
    data = {
        "type": MessageType.VERDICT.value,
        "session_id": "x",
        "payload": {
            "winner": "pro",
            "pro_score": 80,
            "con_score": 70,
            "rationale": "Better",
            "persuasion_notes": "Notes",
        },
    }
    msg = message_from_dict(data)
    assert isinstance(msg, VerdictMessage)


def test_create_child_agent_invalid_role():
    with pytest.raises(ValueError, match="Child worker cannot use role"):
        create_child_agent(AgentRole.PARENT, load_config(), "sess")


def test_factory_creates_agents():
    config = load_config()
    client = make_llm_client(config)
    assert isinstance(client, LlmClient)

    pro = create_child_agent(AgentRole.PRO, config, "sess")
    con = create_child_agent(AgentRole.CON, config, "sess")
    parent = create_parent_agent(config, "sess")

    assert pro.role == AgentRole.PRO
    assert con.role == AgentRole.CON
    assert parent.role == AgentRole.PARENT


def test_save_verdict_writes_file(tmp_path):
    from dataclasses import replace

    config = replace(load_config(), project_root=tmp_path)

    verdict = VerdictMessage(
        session_id="abc",
        payload=VerdictPayload(
            winner=AgentRole.PRO,
            pro_score=80,
            con_score=70,
            rationale="Good",
            persuasion_notes="Notes",
        ),
    )

    q: queue.Queue = queue.Queue()
    path = save_verdict(config, "abc", verdict, q)
    assert path.is_file()
    assert path.read_text(encoding="utf-8").strip().startswith("{")

    done = None
    while True:
        item = q.get(timeout=1)
        if item["kind"] == "done":
            done = item
            break

    assert done is not None
    assert done["data"]["verdict_path"] == str(path)
