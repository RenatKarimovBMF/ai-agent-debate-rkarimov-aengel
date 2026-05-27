"""Targeted branch coverage for `debate.agents.verdict_llm`.

Covers every validation branch in `validate_verdict_dict` plus the
retry/fallback paths in `invoke_and_parse_verdict_with_retry`.
"""

from __future__ import annotations

import pytest

from debate.agents.verdict_llm import (
    invoke_and_parse_verdict_with_retry,
    validate_verdict_dict,
)
from debate.models import AgentRole

from ._coverage_helpers import MagicMock


def _base_verdict() -> dict:
    return {
        "winner": "pro",
        "pro_score": 80,
        "con_score": 70,
        "rationale": "r",
        "persuasion_notes": "p",
    }


def test_validate_verdict_dict_rejects_invalid_winner():
    with pytest.raises(ValueError, match='exactly "pro" or "con"'):
        validate_verdict_dict({**_base_verdict(), "winner": "neither"})


def test_validate_verdict_dict_rejects_pro_score_out_of_range():
    with pytest.raises(ValueError, match="pro_score must be between"):
        validate_verdict_dict({**_base_verdict(), "pro_score": 200})


def test_validate_verdict_dict_rejects_con_score_out_of_range():
    with pytest.raises(ValueError, match="con_score must be between"):
        validate_verdict_dict({**_base_verdict(), "con_score": -1})


def test_validate_verdict_dict_rejects_equal_scores():
    with pytest.raises(ValueError, match="cannot be equal"):
        validate_verdict_dict({**_base_verdict(), "pro_score": 70})


def test_validate_verdict_dict_rejects_pro_lower_than_con_when_pro_wins():
    with pytest.raises(ValueError, match="pro_score must be higher"):
        validate_verdict_dict({**_base_verdict(), "pro_score": 50})


def test_validate_verdict_dict_rejects_con_lower_than_pro_when_con_wins():
    with pytest.raises(ValueError, match="con_score must be higher"):
        validate_verdict_dict({**_base_verdict(), "winner": "con", "con_score": 50})


def test_validate_verdict_dict_rejects_empty_rationale():
    with pytest.raises(ValueError, match="rationale cannot be empty"):
        validate_verdict_dict({**_base_verdict(), "rationale": "   "})


def test_validate_verdict_dict_rejects_empty_persuasion_notes():
    with pytest.raises(ValueError, match="persuasion_notes cannot be empty"):
        validate_verdict_dict({**_base_verdict(), "persuasion_notes": ""})


def test_invoke_and_parse_verdict_repairs_on_first_failure():
    agent = MagicMock()
    agent.invoke_llm = MagicMock(
        side_effect=[
            "not json",
            (
                '{"winner": "pro", "pro_score": 81, "con_score": 77, '
                '"rationale": "r", "persuasion_notes": "p"}'
            ),
        ]
    )
    agent.role = AgentRole.PARENT

    data = invoke_and_parse_verdict_with_retry(agent, prompt="x")
    assert data["winner"] == "pro"
    assert agent.invoke_llm.call_count == 2


def test_invoke_and_parse_verdict_falls_back_after_double_failure():
    agent = MagicMock()
    agent.invoke_llm = MagicMock(side_effect=["junk", "junk again"])
    agent.role = AgentRole.PARENT

    data = invoke_and_parse_verdict_with_retry(agent, prompt="x")
    assert data["winner"] == "pro"
    assert "Fallback verdict" in data["rationale"]
