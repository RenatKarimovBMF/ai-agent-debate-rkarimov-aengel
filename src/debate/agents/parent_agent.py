from __future__ import annotations

from debate.agent_base import BaseAgent
from debate.agents.verdict_llm import invoke_and_parse_verdict_with_retry
from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole, DebateMessage, MessageType, VerdictMessage, VerdictPayload
from debate.transport import ChannelPair
from sdk.llm_client import LlmClient


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
        debate = self.config.debate
        return f"""You are the PARENT/JUDGE agent in a mediated AI debate.
Topic: {debate.topic}
Side PRO: {debate.pro_side}
Side CON: {debate.con_side}

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

        data = invoke_and_parse_verdict_with_retry(self, prompt)
        return _build_verdict_message(self.session_id, data)


def _build_verdict_message(session_id: str, data: dict) -> VerdictMessage:
    winner = AgentRole(data["winner"])
    if winner not in (AgentRole.PRO, AgentRole.CON):
        raise ValueError("Judge must pick pro or con")

    pro_score = max(0.0, min(100.0, float(data["pro_score"])))
    con_score = max(0.0, min(100.0, float(data["con_score"])))

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
        session_id=session_id,
        payload=VerdictPayload(
            winner=winner,
            pro_score=pro_score,
            con_score=con_score,
            rationale=str(data["rationale"]),
            persuasion_notes=str(data["persuasion_notes"]),
        ),
    )
