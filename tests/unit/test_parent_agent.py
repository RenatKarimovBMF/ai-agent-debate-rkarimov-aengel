from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from debate.agents.parent_agent import ParentAgent, _build_verdict_message
from debate.config import GatekeeperConfig, load_config
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole
from debate.transport import ChannelPair


def test_build_verdict_message_adjusts_tied_scores():
    verdict = _build_verdict_message(
        "sess",
        {
            "winner": "con",
            "pro_score": 70,
            "con_score": 70,
            "rationale": "Close",
            "persuasion_notes": "Notes",
        },
    )
    assert verdict.payload.winner == AgentRole.CON
    assert verdict.payload.con_score > verdict.payload.pro_score


def test_build_verdict_message_rejects_invalid_winner():
    with pytest.raises(ValueError, match="Judge must pick"):
        _build_verdict_message(
            "sess",
            {
                "winner": "parent",
                "pro_score": 80,
                "con_score": 70,
                "rationale": "x",
                "persuasion_notes": "y",
            },
        )


def test_parent_receive_from_child():
    config = load_config()
    gk = Gatekeeper(GatekeeperConfig(enabled=False, max_total_requests=5, max_requests_per_agent=5))
    client = MagicMock()
    child_to_parent = MagicMock()
    child_to_parent.read.return_value = None
    pair = ChannelPair(child_to_parent, MagicMock())

    parent = ParentAgent(config, gk, client, "sess", pair, pair)
    assert parent.receive_from_child(AgentRole.PRO, timeout=1.0) is None
