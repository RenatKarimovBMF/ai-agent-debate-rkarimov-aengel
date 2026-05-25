from __future__ import annotations

import pytest

from debate.agent_base import BaseAgent
from debate.agents.debate_llm import invoke_and_parse_debate_payload_with_retry, safe_fallback_text
from debate.agents.verdict_llm import invoke_and_parse_verdict_with_retry, validate_verdict_dict
from debate.config import GatekeeperConfig, load_config
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole
from sdk.llm_client import LlmClient


def _disabled_gatekeeper() -> Gatekeeper:
    cfg = GatekeeperConfig(
        enabled=False,
        max_total_requests=10,
        max_requests_per_agent=10,
    )
    return Gatekeeper(cfg)


class _StubAgent(BaseAgent):
    def __init__(self, responses: list[str]) -> None:
        config = load_config()
        super().__init__(
            AgentRole.PRO,
            config,
            None,
            _disabled_gatekeeper(),
            LlmClient(),
            "sess",
        )
        self._responses = list(responses)

    def system_prompt(self) -> str:
        return "system"

    def invoke_llm(self, user_prompt: str) -> str:
        if not self._responses:
            raise RuntimeError("no more responses")
        return self._responses.pop(0)


def test_safe_fallback_text_truncates():
    long = "word " * 300
    result = safe_fallback_text(long, limit=50)
    assert len(result) <= 54
    assert result.endswith("...")


def test_invoke_and_parse_debate_payload_with_retry_repairs_json():
    good = (
        '{"text": "Fixed", "citations": [{"title": "IMDB", "url": "https://imdb.com"}]}'
    )
    agent = _StubAgent(["not-json", good])
    payload = invoke_and_parse_debate_payload_with_retry(
        agent, "prompt", ping=1, responding_to_ping=None
    )
    assert payload.text == "Fixed"


def test_invoke_and_parse_debate_payload_uses_fallback_after_two_failures():
    agent = _StubAgent(["bad", "still-bad"])
    payload = invoke_and_parse_debate_payload_with_retry(
        agent, "prompt", ping=1, responding_to_ping=None
    )
    assert "fallback turn" in payload.text.lower()
    assert payload.citations


def test_validate_verdict_dict_rejects_tie():
    with pytest.raises(ValueError, match="cannot be equal"):
        validate_verdict_dict(
            {
                "winner": "pro",
                "pro_score": 80,
                "con_score": 80,
                "rationale": "x",
                "persuasion_notes": "y",
            }
        )


def test_invoke_and_parse_verdict_with_retry_fallback():
    agent = _StubAgent(["{broken", "{still broken"])
    data = invoke_and_parse_verdict_with_retry(agent, "verdict prompt")
    assert data["winner"] == "pro"
    assert data["pro_score"] != data["con_score"]
