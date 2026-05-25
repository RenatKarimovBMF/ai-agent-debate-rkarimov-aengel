from __future__ import annotations

from debate.agent_base import BaseAgent
from debate.agents.debate_llm import invoke_and_parse_debate_payload_with_retry
from debate.agents.prompts import debater_prompt, turn_prompt
from debate.models import AgentRole, DebateMessage, MessageType


class ProAgent(BaseAgent):
    def system_prompt(self) -> str:
        debate = self.config.debate
        return debater_prompt(
            role="PRO",
            topic=debate.topic,
            own_side=debate.pro_side,
            opponent_side=debate.con_side,
            max_words=debate.max_words_per_turn,
        )

    def build_turn(self, ping: int, opponent_text: str | None) -> DebateMessage:
        debate = self.config.debate
        prompt = turn_prompt(
            ping=ping,
            own_side=debate.pro_side,
            opponent_side=debate.con_side,
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
            from_role=AgentRole.PRO,
            to_role=AgentRole.PARENT,
            session_id=self.session_id,
            turn_id=self.next_turn_id(),
            payload=payload,
        )
