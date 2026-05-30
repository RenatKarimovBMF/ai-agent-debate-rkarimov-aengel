from __future__ import annotations

from debate.agent_base import BaseAgent
from debate.agents.judge_prompts import judge_system_prompt, verdict_prompt
from debate.agents.verdict_builder import _build_verdict_message
from debate.agents.verdict_llm import invoke_and_parse_verdict_with_retry
from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole, DebateMessage, MessageType, VerdictMessage
from debate.transport import ChannelPair
from sdk.llm_client import LlmClient

__all__ = ["ParentAgent", "_build_verdict_message"]


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
        pro_side, con_side = self._assigned_sides()
        base = judge_system_prompt(self.config.debate.topic, pro_side, con_side)
        return base + self.skill_suffix()

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

    def transcript_text(self) -> str:
        """Full debate transcript (every turn, untruncated) for persistence."""
        return "\n\n".join(self._history)

    def render_verdict(self) -> VerdictMessage:
        transcript = "\n\n".join(self._history[-80:])
        pro_side, con_side = self._assigned_sides()

        prompt = verdict_prompt(pro_side, con_side, transcript)
        data = invoke_and_parse_verdict_with_retry(self, prompt)
        return _build_verdict_message(self.session_id, data)
