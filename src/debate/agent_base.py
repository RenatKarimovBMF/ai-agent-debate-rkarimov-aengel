from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole, DebateMessage
from debate.transport import ChannelPair
from sdk.llm_client import LlmClient

logger = logging.getLogger("debate.agent")


class BaseAgent(ABC):
    """Shared behavior for pro, con, and parent agents."""

    def __init__(
        self,
        role: AgentRole,
        config: AppConfig,
        channels: ChannelPair | None,
        gatekeeper: Gatekeeper,
        client: LlmClient,
        session_id: str,
    ) -> None:
        self.role = role
        self.config = config
        self.channels = channels
        self.gatekeeper = gatekeeper
        self.client = client
        self.session_id = session_id
        self._turn = 0

    @abstractmethod
    def system_prompt(self) -> str: ...

    def next_turn_id(self) -> int:
        self._turn += 1
        return self._turn

    def invoke_llm(self, user_prompt: str) -> str:
        self.gatekeeper.check(self.role)
        response = self.client.complete(self.system_prompt(), user_prompt)
        self.gatekeeper.record(self.role)
        return response.text

    def send(self, message: DebateMessage) -> None:
        if self.channels is None:
            raise RuntimeError("Parent agent does not use child channels directly")
        self.channels.child_to_parent.write(message)

    def receive(self, timeout: float | None = None) -> DebateMessage | None:
        if self.channels is None:
            return None
        return self.channels.parent_to_child.read(timeout=timeout)
