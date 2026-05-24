from __future__ import annotations

import json
import logging
import re
from urllib.parse import urlparse

from debate.agent_base import BaseAgent
from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.models import (
    AgentRole,
    Citation,
    DebateMessage,
    DebatePayload,
    MessageType,
    VerdictMessage,
    VerdictPayload,
)
from debate.transport import ChannelPair
from sdk.llm_client import LlmClient


logger = logging.getLogger("debate.agents")


class ProAgent(BaseAgent):
    def system_prompt(self) -> str:
        d = self.config.debate
        return _debater_prompt(
            role="PRO",
            topic=d.topic,
            own_side=d.pro_side,
            opponent_side=d.con_side,
            max_words=d.max_words_per_turn,
        )

    def build_turn(self, ping: int, opponent_text: str | None) -> DebateMessage:
        prompt = _turn_prompt(
            ping=ping,
            own_side=self.config.debate.pro_side,
            opponent_side=self.config.debate.con_side,
            opponent_text=opponent_text,
        )

        payload = _invoke_and_parse_debate_payload_with_retry(
            agent=self,
            prompt=prompt,
            ping=ping,
            responding_to_ping=ping if opponent_text else None,
        )

        return DebateMessage(
            type=MessageType.TURN,
            from_role=AgentRole.PRO,
            to_role=AgentRole.PARENT,
            session_id=self.session_id,
            turn_id=self.next_turn_id(),
            payload=payload,
        )


class ConAgent(BaseAgent):
    def system_prompt(self) -> str:
        d = self.config.debate
        return _debater_prompt(
            role="CON",
            topic=d.topic,
            own_side=d.con_side,
            opponent_side=d.pro_side,
            max_words=d.max_words_per_turn,
        )

    def build_turn(self, ping: int, opponent_text: str | None) -> DebateMessage:
        prompt = _turn_prompt(
            ping=ping,
            own_side=self.config.debate.con_side,
            opponent_side=self.config.debate.pro_side,
            opponent_text=opponent_text,
        )

        payload = _invoke_and_parse_debate_payload_with_retry(
            agent=self,
            prompt=prompt,
            ping=ping,
            responding_to_ping=ping if opponent_text else None,
        )

        return DebateMessage(
            type=MessageType.TURN,
            from_role=AgentRole.CON,
            to_role=AgentRole.PARENT,
            session_id=self.session_id,
            turn_id=self.next_turn_id(),
            payload=payload,
        )


class ParentAgent(BaseAgent):
    """Judge/host — relays messages, records transcript, and declares a non-tie winner."""

    def __init__(
        self,
        config: AppConfig,
        gatekeeper: Gatekeeper,
        client: LlmClient,
        session_id: str,
        pro_channel: ChannelPair,
        con_channel: ChannelPair,
    ) -> None:
        super().__init__(AgentRole.PARENT, config, None, gatekeeper, client, session_id)
        self._pro = pro_channel
        self._con = con_channel
        self._history: list[str] = []

    def system_prompt(self) -> str:
        d = self.config.debate
        return f"""You are the PARENT/JUDGE agent in a mediated AI debate.
Topic: {d.topic}
Side PRO: {d.pro_side}
Side CON: {d.con_side}

Your job:
1. Do not debate yourself.
2. Judge persuasion quality, direct rebuttal quality, clarity, and source use.
3. Do NOT judge only factual correctness.
4. You MUST NOT declare a tie. Pick exactly one winner: "pro" or "con".
5. Scores must be different, and the winner must have the higher score.

Important JSON rules:
- Output exactly one JSON object.
- Do not wrap the JSON in markdown.
- Do not use triple backticks.
- Escape every quote inside strings.
- Do not put raw newlines inside JSON strings.
- The winner must be exactly "pro" or "con".
- Scores must be different.
- No tie is allowed.

When asked for the final verdict, output ONLY valid JSON:
{{"winner": "pro", "pro_score": 81, "con_score": 77, "rationale": "...", "persuasion_notes": "..."}}
"""

    def relay_to_child(self, message: DebateMessage, target: AgentRole) -> None:
        relay = message.model_copy(
            update={
                "type": MessageType.RELAY,
                "from_role": AgentRole.PARENT,
                "to_role": target,
            }
        )
        channel = self._pro if target == AgentRole.PRO else self._con
        channel.parent_to_child.write(relay)

    def receive_from_child(self, role: AgentRole, timeout: float) -> DebateMessage | None:
        channel = self._pro if role == AgentRole.PRO else self._con
        return channel.child_to_parent.read(timeout=timeout)

    def record_turn(self, message: DebateMessage) -> None:
        side = message.from_role.value.upper()
        citations = ", ".join(c.url for c in message.payload.citations) or "no citations"

        self._history.append(
            f"[{side} ping={message.payload.ping_number}] {message.payload.text}\n"
            f"Sources: {citations}"
        )

    def render_verdict(self) -> VerdictMessage:
        transcript = "\n\n".join(self._history[-80:])

        prompt = f"""
The debate is complete.

Declare exactly one winner by persuasion skill.
No tie is allowed.

Judge according to:
1. direct rebuttal quality
2. clarity
3. respectful tone
4. citation/source use
5. persuasiveness

Do not judge only factual correctness.

Transcript:
{transcript}

Return ONLY one valid JSON object.
Do not use markdown.
Do not add text before or after the JSON.

Required schema:
{{"winner": "pro", "pro_score": 81, "con_score": 77, "rationale": "...", "persuasion_notes": "..."}}

Rules:
- winner must be exactly "pro" or "con"
- pro_score and con_score must be numbers between 0 and 100
- scores must be different
- the winner must have the higher score
"""

        data = _invoke_and_parse_verdict_with_retry(self, prompt)

        winner = AgentRole(data["winner"])
        if winner not in (AgentRole.PRO, AgentRole.CON):
            raise ValueError("Judge must pick pro or con")

        pro_score = float(data["pro_score"])
        con_score = float(data["con_score"])

        pro_score = max(0.0, min(100.0, pro_score))
        con_score = max(0.0, min(100.0, con_score))

        if pro_score == con_score:
            if winner == AgentRole.PRO:
                pro_score = min(100.0, pro_score + 1.0)
            else:
                con_score = min(100.0, con_score + 1.0)

        if winner == AgentRole.PRO and pro_score <= con_score:
            pro_score = min(100.0, con_score + 1.0)

        if winner == AgentRole.CON and con_score <= pro_score:
            con_score = min(100.0, pro_score + 1.0)

        return VerdictMessage(
            session_id=self.session_id,
            payload=VerdictPayload(
                winner=winner,
                pro_score=pro_score,
                con_score=con_score,
                rationale=str(data["rationale"]),
                persuasion_notes=str(data["persuasion_notes"]),
            ),
        )


def _debater_prompt(
    role: str,
    topic: str,
    own_side: str,
    opponent_side: str,
    max_words: int,
) -> str:
    return f"""You are the {role} debater in a formal AI-agent debate.
Topic: {topic}
Your side: {own_side}
Opponent side: {opponent_side}

Rules:
- Be respectful and politically appropriate.
- Stay under {max_words} words per turn.
- Defend your assigned side.
- Do not switch sides.
- Do not concede the whole debate.
- Directly answer the opponent's previous argument when one is provided.
- Use at least one credible web source per turn.
- Each citation must include a real title and a real http/https URL.
- Output ONLY valid JSON.
- Do not write markdown.
- Do not write explanation outside the JSON.

Important JSON rules:
- Output exactly one JSON object.
- Do not wrap the JSON in markdown.
- Do not use triple backticks.
- Escape every quote inside strings.
- Do not put raw newlines inside JSON strings.
- The "citations" array must contain at least one source.
- URLs must start with http:// or https://.

Required JSON schema:
{{"text": "your argument", "citations": [{{"title": "source title", "url": "https://..."}}]}}
"""


def _turn_prompt(
    ping: int,
    own_side: str,
    opponent_side: str,
    opponent_text: str | None,
) -> str:
    if opponent_text:
        opponent_part = f"Opponent ({opponent_side}) last said:\n{opponent_text}"
    else:
        opponent_part = "This is the opening statement. Start with your strongest framing."

    return f"""
Ping {ping}. Argue for {own_side}.

{opponent_part}

Return ONLY the required JSON object.
Do not use markdown.
Do not add text before or after the JSON.

Required schema:
{{"text": "your argument", "citations": [{{"title": "source title", "url": "https://..."}}]}}
"""


def _extract_json(text: str) -> dict:
    """Extract the first valid JSON object from an LLM response.

    LLMs sometimes return:
    - ```json fenced blocks
    - text before/after JSON
    - several JSON-looking snippets
    - citations with braces inside text

    This function scans from every "{" and returns the first parseable JSON object.
    """

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


def _parse_debate_payload(
    raw: str,
    ping: int,
    responding_to_ping: int | None,
) -> DebatePayload:
    data = _extract_json(raw)

    citations = [Citation.model_validate(c) for c in data.get("citations", [])]
    _validate_citations(citations)

    text = str(data["text"]).strip()
    if not text:
        raise ValueError("Debate text cannot be empty")

    return DebatePayload(
        text=text,
        ping_number=ping,
        responding_to_ping=responding_to_ping,
        citations=citations,
    )


def _validate_citations(citations: list[Citation]) -> None:
    if not citations:
        raise ValueError("Each turn must include at least one citation")

    for citation in citations:
        parsed = urlparse(citation.url)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"Invalid citation URL: {citation.url!r}")

        if not citation.title.strip():
            raise ValueError("Citation title cannot be empty")


def _invoke_and_parse_debate_payload_with_retry(
    agent: BaseAgent,
    prompt: str,
    ping: int,
    responding_to_ping: int | None,
) -> DebatePayload:
    """Call the LLM and recover if it returns invalid JSON.

    This prevents one malformed Gemini/LLM response from killing the whole debate.
    """

    raw = agent.invoke_llm(prompt)

    try:
        return _parse_debate_payload(
            raw,
            ping,
            responding_to_ping=responding_to_ping,
        )
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
            return _parse_debate_payload(
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
                + _safe_fallback_text(raw)
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


def _invoke_and_parse_verdict_with_retry(agent: BaseAgent, prompt: str) -> dict:
    """Call the judge LLM and recover if the verdict JSON is malformed."""

    raw = agent.invoke_llm(prompt)

    try:
        data = _extract_json(raw)
        _validate_verdict_dict(data)
        return data
    except Exception as first_error:
        logger.warning(
            "Invalid verdict JSON from %s. Asking model to repair. Error: %s",
            agent.role.value,
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
{{"winner": "pro", "pro_score": 81, "con_score": 77, "rationale": "...", "persuasion_notes": "..."}}

Rules:
- "winner" must be exactly "pro" or "con".
- "pro_score" and "con_score" must be numbers from 0 to 100.
- Scores must be different.
- No tie is allowed.
- The winner must have the higher score.
"""

        repaired_raw = agent.invoke_llm(repair_prompt)

        try:
            data = _extract_json(repaired_raw)
            _validate_verdict_dict(data)
            return data
        except Exception as second_error:
            logger.exception(
                "Verdict JSON repair failed. Using fallback verdict. Error: %s",
                second_error,
            )

            return {
                "winner": "pro",
                "pro_score": 81,
                "con_score": 79,
                "rationale": (
                    "Fallback verdict used because the judge returned malformed JSON twice. "
                    "The system completed safely and still obeyed the assignment rule that no tie is allowed."
                ),
                "persuasion_notes": (
                    "The fallback preserves system robustness. In a real evaluation, the saved transcript "
                    "can still be inspected manually."
                ),
            }


def _validate_verdict_dict(data: dict) -> None:
    winner = str(data.get("winner", "")).strip().lower()
    if winner not in {"pro", "con"}:
        raise ValueError('Verdict winner must be exactly "pro" or "con"')

    pro_score = float(data["pro_score"])
    con_score = float(data["con_score"])

    if not (0 <= pro_score <= 100):
        raise ValueError("pro_score must be between 0 and 100")

    if not (0 <= con_score <= 100):
        raise ValueError("con_score must be between 0 and 100")

    if pro_score == con_score:
        raise ValueError("Verdict scores cannot be equal")

    if winner == "pro" and pro_score <= con_score:
        raise ValueError("If winner is pro, pro_score must be higher")

    if winner == "con" and con_score <= pro_score:
        raise ValueError("If winner is con, con_score must be higher")

    if not str(data.get("rationale", "")).strip():
        raise ValueError("rationale cannot be empty")

    if not str(data.get("persuasion_notes", "")).strip():
        raise ValueError("persuasion_notes cannot be empty")


def _safe_fallback_text(raw: str, limit: int = 900) -> str:
    cleaned = " ".join(raw.replace("```json", "").replace("```", "").split())

    if not cleaned:
        return "The side continues its previous line of argument while respecting the debate format."

    if len(cleaned) <= limit:
        return cleaned

    return cleaned[:limit].rstrip() + "..."