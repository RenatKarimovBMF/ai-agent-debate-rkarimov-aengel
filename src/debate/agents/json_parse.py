from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from debate.models import Citation, DebatePayload


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    decoder = json.JSONDecoder()

    for start_index, char in enumerate(cleaned):
        if char != "{":
            continue

        try:
            obj, _end_index = decoder.raw_decode(cleaned[start_index:])
        except json.JSONDecodeError:
            continue

        if isinstance(obj, dict):
            return obj

    raise ValueError(f"No valid JSON object in model output. Raw output was:\n{cleaned[:1200]}")


def validate_citations(citations: list[Citation]) -> None:
    if not citations:
        raise ValueError("Each turn must include at least one citation")

    for citation in citations:
        parsed = urlparse(citation.url)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid citation URL: {citation.url!r}")

        if not citation.title.strip():
            raise ValueError("Citation title cannot be empty")


def parse_debate_payload(
    raw: str,
    ping: int,
    responding_to_ping: int | None,
) -> DebatePayload:
    data = extract_json(raw)

    citations = [Citation.model_validate(c) for c in data.get("citations", [])]
    validate_citations(citations)

    text = str(data["text"]).strip()
    if not text:
        raise ValueError("Debate text cannot be empty")

    return DebatePayload(
        text=text,
        ping_number=ping,
        responding_to_ping=responding_to_ping,
        citations=citations,
    )
