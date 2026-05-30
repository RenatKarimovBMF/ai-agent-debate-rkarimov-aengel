from __future__ import annotations

from unittest.mock import MagicMock

from debate.agent_base import BaseAgent
from debate.agents.con_agent import ConAgent
from debate.agents.parent_agent import ParentAgent
from debate.agents.pro_agent import ProAgent
from debate.agents.prompts import debater_prompt, turn_prompt
from debate.config import GatekeeperConfig, load_config
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole, Citation, DebateMessage, DebatePayload, MessageType
from debate.transport import ChannelPair
from sdk.llm_client import LlmResponse


def _disabled_gatekeeper() -> Gatekeeper:
    cfg = GatekeeperConfig(
        enabled=False,
        max_total_requests=10,
        max_requests_per_agent=10,
    )
    return Gatekeeper(cfg)


def test_debater_prompt_contains_sides():
    text = debater_prompt("PRO", "topic", "A", "B", 100)
    assert "PRO" in text
    assert "A" in text
    assert "B" in text


def test_turn_prompt_with_opponent():
    text = turn_prompt(2, "Godfather", "Shawshank", "Previous argument")
    assert "Ping 2" in text
    assert "Previous argument" in text


def test_turn_prompt_opening():
    text = turn_prompt(1, "Godfather", "Shawshank", None)
    assert "opening statement" in text
    assert "opening/expansion" in text


def test_turn_prompt_development_phase():
    text = turn_prompt(5, "A", "B", "prev", pings=10)
    assert "development" in text


def test_turn_prompt_closing_phase():
    text = turn_prompt(9, "A", "B", "prev", pings=10)
    assert "closing" in text and "crystallize" in text


def _llm_json(text: str = "Our side wins.") -> str:
    return (
        f'{{"text": "{text}", "citations": [{{"title": "Source", "url": "https://example.com"}}]}}'
    )


def test_pro_agent_build_turn(monkeypatch):
    config = load_config()
    gk = _disabled_gatekeeper()
    client = MagicMock()
    client.complete.return_value = LlmResponse(text=_llm_json(), raw="", provider="gemini")

    agent = ProAgent(AgentRole.PRO, config, None, gk, client, "sess1")
    monkeypatch.setattr(agent, "invoke_llm", lambda prompt: _llm_json())

    message = agent.build_turn(1, None)
    assert message.from_role == AgentRole.PRO
    assert message.to_role == AgentRole.PARENT
    assert message.payload.ping_number == 1


def test_con_agent_build_turn(monkeypatch):
    config = load_config()
    gk = _disabled_gatekeeper()
    client = MagicMock()

    agent = ConAgent(AgentRole.CON, config, None, gk, client, "sess1")
    monkeypatch.setattr(agent, "invoke_llm", lambda prompt: _llm_json("Counter"))

    message = agent.build_turn(1, "opponent said this")
    assert message.from_role == AgentRole.CON


def test_parent_agent_record_and_verdict(monkeypatch):
    config = load_config()
    gk = _disabled_gatekeeper()
    client = MagicMock()
    pair = ChannelPair(MagicMock(), MagicMock())

    parent = ParentAgent(config, gk, client, "sess1", pair, pair)

    turn = DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.PARENT,
        session_id="sess1",
        turn_id=1,
        payload=DebatePayload(
            text="Argument",
            ping_number=1,
            citations=[Citation(title="S", url="https://x.com")],
        ),
    )

    parent.record_turn(turn)
    parent.relay_to_child(turn, AgentRole.CON)

    verdict_json = (
        '{"winner": "pro", "pro_score": 82, "con_score": 78, '
        '"rationale": "Stronger", "persuasion_notes": "Clear rebuttals"}'
    )
    monkeypatch.setattr(parent, "invoke_llm", lambda prompt: verdict_json)

    verdict = parent.render_verdict()
    assert verdict.payload.winner == AgentRole.PRO
    assert verdict.payload.pro_score > verdict.payload.con_score


def test_agent_base_invoke_llm_records_gatekeeper():
    config = load_config()
    gk = Gatekeeper(GatekeeperConfig(enabled=True, max_total_requests=5, max_requests_per_agent=5))
    client = MagicMock()
    client.complete.return_value = LlmResponse(text="ok", raw="", provider="gemini")

    class Stub(BaseAgent):
        def system_prompt(self) -> str:
            return "sys"

    agent = Stub(AgentRole.PRO, config, None, gk, client, "s")
    text = agent.invoke_llm("user")
    assert text == "ok"
    assert gk.total_requests == 1
