from __future__ import annotations

import logging

from debate.agent_base import BaseAgent
from debate.agents.json_parse import parse_debate_payload
from debate.models import Citation, DebatePayload

logger = logging.getLogger("debate.agents")


def safe_fallback_text(raw: str, limit: int = 900) -> str:
    cleaned = " ".join(raw.replace("```json", "").replace("```", "").split())

    if not cleaned:
        return (
            "The side continues its previous line of argument "
            "while respecting the debate format."
        )

    if len(cleaned) <= limit:
        return cleaned

    return cleaned[:limit].rstrip() + "..."


def invoke_and_parse_debate_payload_with_retry(
    agent: BaseAgent,
    prompt: str,
    ping: int,
    responding_to_ping: int | None,
) -> DebatePayload:
    raw = agent.invoke_llm(prompt)

    try:
        return parse_debate_payload(raw, ping, responding_to_ping=responding_to_ping)
    except Exception as first_error:
        logger.warning(
            "Invalid JSON from %s on ping %s. Asking model to repair. Error: %s",
            agent.role.value,
            ping,
            first_error,
        )

        repair_prompt = f"""
Your previous answer was not valid JSON or did not match the required schema.

Error:
{first_error}

Original invalid answer:
{raw}

Rewrite it as ONLY one valid JSON object.
Do not use markdown.
Do not add text before or after the JSON.
Do not use triple backticks.
Escape every quote inside strings.
Do not put raw newlines inside JSON strings.

Required schema:
{{"text": "your argument", "citations": [{{"title": "source title", "url": "https://..."}}]}}

Rules:
- "text" must be a non-empty string.
- "citations" must contain at least one item.
- each citation must have "title" and "url".
- each url must start with http:// or https://.
"""

        repaired_raw = agent.invoke_llm(repair_prompt)

        try:
            return parse_debate_payload(
                repaired_raw,
                ping,
                responding_to_ping=responding_to_ping,
            )
        except Exception as second_error:
            logger.exception(
                "JSON repair failed for %s on ping %s. Using fallback payload. Error: %s",
                agent.role.value,
                ping,
                second_error,
            )

            fallback_text = (
                "The agent produced malformed JSON twice. "
                "To keep the debate running, this fallback turn summarizes the intended argument: "
                + safe_fallback_text(raw)
            )

            return DebatePayload(
                text=fallback_text,
                ping_number=ping,
                responding_to_ping=responding_to_ping,
                citations=[
                    Citation(
                        title="Fallback source used after malformed LLM JSON",
                        url="https://www.imdb.com/chart/top/",
                    )
                ],
            )
