from __future__ import annotations

import json
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
        raw = self.invoke_llm(prompt)
        payload = _parse_debate_payload(
            raw,
            ping,
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
        raw = self.invoke_llm(prompt)
        payload = _parse_debate_payload(
            raw,
            ping,
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

When asked for the final verdict, output ONLY valid JSON:
{{"winner": "pro"|"con", "pro_score": 0-100, "con_score": 0-100, "rationale": "...", "persuasion_notes": "..."}}
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
        prompt = (
            "The debate is complete. Declare exactly one winner by persuasion skill. "
            "No tie is allowed. Consider direct rebuttals, clarity, respectful tone, and citation use.\n\n"
            f"Transcript:\n{transcript}"
        )

        raw = self.invoke_llm(prompt)
        data = _extract_json(raw)

        winner = AgentRole(data["winner"])
        if winner not in (AgentRole.PRO, AgentRole.CON):
            raise ValueError("Judge must pick pro or con")

        pro_score = float(data["pro_score"])
        con_score = float(data["con_score"])

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
- Defend your assigned side. Do not switch sides and do not concede the whole debate.
- Directly answer the opponent's previous argument when one is provided.
- Use at least one credible web source per turn.
- Each citation must include a real title and a real https/http URL.
- Output ONLY valid JSON, no markdown and no explanation outside JSON.

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

    return (
        f"Ping {ping}. Argue for {own_side}.\n"
        f"{opponent_part}\n\n"
        "Return only the required JSON object."
    )


def _extract_json(text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object in model output")

    return json.loads(match.group())


def _parse_debate_payload(
    raw: str,
    ping: int,
    responding_to_ping: int | None,
) -> DebatePayload:
    data = _extract_json(raw)
    citations = [Citation.model_validate(c) for c in data.get("citations", [])]
    _validate_citations(citations)

    return DebatePayload(
        text=str(data["text"]).strip(),
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