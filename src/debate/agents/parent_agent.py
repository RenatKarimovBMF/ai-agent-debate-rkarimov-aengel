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
        self._pro_side: str | None = None
        self._con_side: str | None = None

    def apply_assignment(self, *, pro_side: str, con_side: str) -> None:
        """Record the runtime side mapping decided by `host_protocol`."""
        self._pro_side = pro_side.strip() or None
        self._con_side = con_side.strip() or None

    def _assigned_sides(self) -> tuple[str, str]:
        debate = self.config.debate
        return (
            self._pro_side or debate.pro_side,
            self._con_side or debate.con_side,
        )

    def system_prompt(self) -> str:
        debate = self.config.debate
        pro_side, con_side = self._assigned_sides()
        return f"""You are the PARENT/JUDGE agent in a mediated AI debate.
Topic: {debate.topic}
PRO defends: {pro_side}
CON defends: {con_side}

The sides were assigned by you at runtime — they are not facts about the
world. Judge persuasion, not which side is "really" true.

Judging principles (research-backed; see .claude/skills/debate-parent-judge):
1. Persuasion, not truth. A well-defended falsehood beats a poorly
   defended truth. The exception is the "refute-with-citation" rule: a
   debater alleging a falsehood must cite a real source in the same turn,
   or the allegation does not count and is penalised.
2. Clash matters. Reward direct engagement with the opponent's last
   point; penalise debaters who run their own talking points and ignore
   the opponent.
3. Dropped arguments stand. If a claim went unanswered for two
   consecutive turns, treat it as conceded for scoring.
4. No tie. Scores must differ; the winner has the strictly higher score.

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
        role_label = message.from_role.value.upper()
        pro_side, con_side = self._assigned_sides()
        defending = pro_side if message.from_role == AgentRole.PRO else con_side
        citations = ", ".join(c.url for c in message.payload.citations) or "no citations"

        self._history.append(
            f"[{role_label} defending '{defending}' ping={message.payload.ping_number}] "
            f"{message.payload.text}\nSources: {citations}"
        )

    def render_verdict(self) -> VerdictMessage:
        transcript = "\n\n".join(self._history[-80:])
        pro_side, con_side = self._assigned_sides()

        prompt = f"""
The debate is complete.

PRO defended: {pro_side}
CON defended: {con_side}

Apply the rubric from .claude/skills/debate-judge-rubric to score each
side across Matter (30), Manner (15), Method (15), Clash (25), and
Burden (15). Sum to a 0-100 total per side.

Then apply the five judging principles from
.claude/skills/debate-parent-judge:
1. Persuasion, not truth.
2. Clash matters; reward direct engagement.
3. Refuting a lie requires a cited source; bare contradictions do not
   count and are penalised.
4. Dropped arguments stand.
5. No tie permitted — break ties by higher Clash, then fewer dropped
   claims.

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
- persuasion_notes must reference at least one of the five principles above
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
