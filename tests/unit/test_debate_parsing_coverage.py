"""Targeted branch coverage for the debate-side LLM/JSON helpers.

Covers `debate.agents.debate_llm` and `debate.agents.json_parse`.
"""

from __future__ import annotations

import pytest

from debate.agents.debate_llm import (
    invoke_and_parse_debate_payload_with_retry,
    safe_fallback_text,
)
from debate.agents.json_parse import (
    extract_json,
    parse_debate_payload,
    validate_citations,
)
from debate.models import AgentRole, Citation

from ._coverage_helpers import MagicMock


def test_safe_fallback_text_empty_input():
    assert "respecting the debate format" in safe_fallback_text("")


def test_safe_fallback_text_long_input_truncated():
    long = "word " * 400
    out = safe_fallback_text(long, limit=50)
    assert out.endswith("...")
    assert len(out) <= 53


def test_extract_json_skips_garbage_prefix():
    raw = 'noise {"text": "ok", "citations": []}'
    assert extract_json(raw) == {"text": "ok", "citations": []}


def test_extract_json_raises_when_no_object_present():
    with pytest.raises(ValueError, match="No valid JSON object"):
        extract_json("plain prose without JSON")


def test_validate_citations_empty_title():
    with pytest.raises(ValueError, match="Citation title cannot be empty"):
        validate_citations([Citation(title="   ", url="https://example.com")])


def test_validate_citations_missing_list():
    with pytest.raises(ValueError, match="at least one citation"):
        validate_citations([])


def test_parse_debate_payload_empty_text_rejected():
    raw = '{"text": "   ", "citations": [{"title": "t", "url": "https://x.com"}]}'
    with pytest.raises(ValueError, match="Debate text cannot be empty"):
        parse_debate_payload(raw, ping=1, responding_to_ping=None)


def test_invoke_and_parse_debate_payload_repairs_on_first_failure():
    agent = MagicMock()
    bad = "{not json"
    good = '{"text": "answer", "citations": [{"title": "t", "url": "https://x.com"}]}'
    agent.invoke_llm = MagicMock(side_effect=[bad, good])
    agent.role = AgentRole.PRO

    payload = invoke_and_parse_debate_payload_with_retry(
        agent, prompt="x", ping=2, responding_to_ping=1
    )
    assert payload.text == "answer"


def test_invoke_and_parse_debate_payload_falls_back_after_double_failure():
    agent = MagicMock()
    agent.invoke_llm = MagicMock(side_effect=["junk", "more junk"])
    agent.role = AgentRole.PRO

    payload = invoke_and_parse_debate_payload_with_retry(
        agent, prompt="x", ping=3, responding_to_ping=None
    )
    assert "fallback turn" in payload.text.lower()
    assert payload.citations[0].url.startswith("https://")
