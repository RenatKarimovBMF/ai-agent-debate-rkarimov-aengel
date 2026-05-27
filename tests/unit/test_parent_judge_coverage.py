"""Targeted branch coverage for the parent/judge prompt and message
helpers: `debate.agents.judge_prompts`, `debate.agents.prompts`
(host opening), `debate.agents.parent_agent`, and `_build_verdict_message`.
"""

from __future__ import annotations

from debate.agents.judge_prompts import judge_system_prompt, verdict_prompt
from debate.agents.parent_agent import ParentAgent, _build_verdict_message
from debate.agents.prompts import host_opening_address
from debate.config import load_config
from debate.transport import ChannelPair

from ._coverage_helpers import MagicMock, make_gatekeeper


def test_judge_prompts_render():
    sys = judge_system_prompt("Topic", "PRO side", "CON side")
    assert "PRO defends: PRO side" in sys
    verdict = verdict_prompt("PRO side", "CON side", "transcript content")
    assert "transcript content" in verdict
    assert "Required schema" in verdict


def test_host_opening_address_includes_assignment():
    text = host_opening_address(
        role="pro",
        topic="T",
        assigned_side="Side A",
        opponent_side="Side B",
        pings=10,
        max_words=200,
    )
    assert "Side A" in text and "Side B" in text and "T" in text


def test_parent_agent_apply_assignment_strips_to_none_on_blank():
    cfg = load_config()
    pair = ChannelPair(MagicMock(), MagicMock())
    parent = ParentAgent(cfg, make_gatekeeper(), MagicMock(), "sess", pair, pair)
    parent.apply_assignment(pro_side="   ", con_side="\t")
    pro, con = parent._assigned_sides()
    assert pro == cfg.debate.pro_side
    assert con == cfg.debate.con_side


def test_parent_agent_system_prompt_uses_assignment():
    cfg = load_config()
    pair = ChannelPair(MagicMock(), MagicMock())
    parent = ParentAgent(cfg, make_gatekeeper(), MagicMock(), "sess", pair, pair)
    parent.apply_assignment(pro_side="Side X", con_side="Side Y")
    prompt = parent.system_prompt()
    assert "Side X" in prompt and "Side Y" in prompt


def test_build_verdict_message_pro_tie_branch():
    verdict = _build_verdict_message(
        "sess",
        {
            "winner": "pro",
            "pro_score": 60,
            "con_score": 60,
            "rationale": "r",
            "persuasion_notes": "p",
        },
    )
    assert verdict.payload.pro_score > verdict.payload.con_score


def test_build_verdict_message_pro_winner_score_repair():
    verdict = _build_verdict_message(
        "sess",
        {
            "winner": "pro",
            "pro_score": 40,
            "con_score": 80,
            "rationale": "r",
            "persuasion_notes": "p",
        },
    )
    assert verdict.payload.pro_score > verdict.payload.con_score


def test_build_verdict_message_con_winner_score_repair():
    verdict = _build_verdict_message(
        "sess",
        {
            "winner": "con",
            "pro_score": 80,
            "con_score": 40,
            "rationale": "r",
            "persuasion_notes": "p",
        },
    )
    assert verdict.payload.con_score > verdict.payload.pro_score
