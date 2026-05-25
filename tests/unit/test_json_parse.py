from __future__ import annotations

import pytest

from debate.agents.json_parse import extract_json, parse_debate_payload, validate_citations
from debate.models import Citation


def test_extract_json_from_fenced_block():
    raw = '```json\n{"text": "hello", "citations": []}\n```'
    data = extract_json(raw)
    assert data["text"] == "hello"


def test_extract_json_from_prose_prefix():
    raw = 'Here is my answer: {"text": "ok", "citations": [{"title": "A", "url": "https://a.com"}]}'
    data = extract_json(raw)
    assert data["text"] == "ok"


def test_extract_json_raises_when_missing():
    with pytest.raises(ValueError, match="No valid JSON"):
        extract_json("not json at all")


def test_validate_citations_requires_http_url():
    with pytest.raises(ValueError, match="at least one citation"):
        validate_citations([])

    with pytest.raises(ValueError, match="Invalid citation URL"):
        validate_citations([Citation(title="Bad", url="ftp://nope.example")])


def test_parse_debate_payload_success():
    raw = (
        '{"text": "Argument", "citations": [{"title": "Source", "url": "https://example.com"}]}'
    )
    payload = parse_debate_payload(raw, ping=2, responding_to_ping=1)
    assert payload.text == "Argument"
    assert payload.ping_number == 2
    assert payload.citations[0].url == "https://example.com"
