from __future__ import annotations

from debate.agent_base import BaseAgent
from debate.agents.debate_llm import invoke_and_parse_debate_payload_with_retry
from debate.agents.prompts import debater_prompt, turn_prompt
from debate.models import AgentRole, DebateMessage, MessageType


class DebaterAgent(BaseAgent):
    """Shared debater logic. Pro/Con are thin wrappers that set the role.

    The assigned side is delivered by the parent at session start via an
    ASSIGN command — it is not read from config at construction time.
    Until an assignment arrives we fall back to the config default so the
    agent remains usable in unit tests.
    """

    _assigned_side: str | None = None
    _opponent_side: str | None = None

    def apply_assignment(self, assigned_side: str, opponent_side: str) -> None:
        self._assigned_side = assigned_side.strip() or None
        self._opponent_side = opponent_side.strip() or None

    def _resolved_sides(self) -> tuple[str, str]:
        debate = self.config.debate
        if self.role == AgentRole.PRO:
            default_self, default_other = debate.pro_side, debate.con_side
        else:
            default_self, default_other = debate.con_side, debate.pro_side

        return (
            self._assigned_side or default_self,
            self._opponent_side or default_other,
        )

    def system_prompt(self) -> str:
        own_side, opponent_side = self._resolved_sides()
        base = debater_prompt(
            role=self.role.value.upper(),
            topic=self.config.debate.topic,
            own_side=own_side,
            opponent_side=opponent_side,
            max_words=self.config.debate.max_words_per_turn,
        )
        return base + self.skill_suffix()

    def build_turn(self, ping: int, opponent_text: str | None) -> DebateMessage:
        own_side, opponent_side = self._resolved_sides()
        prompt = turn_prompt(
            ping=ping,
            own_side=own_side,
            opponent_side=opponent_side,
            opponent_text=opponent_text,
        )

        payload = invoke_and_parse_debate_payload_with_retry(
            agent=self,
            prompt=prompt,
            ping=ping,
            responding_to_ping=ping if opponent_text else None,
        )

        return DebateMessage(
            type=MessageType.TURN,
            from_role=self.role,
            to_role=AgentRole.PARENT,
            session_id=self.session_id,
            turn_id=self.next_turn_id(),
            payload=payload,
        )
