from __future__ import annotations

from debate.agents import ConAgent, ParentAgent, ProAgent
from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole, DebateMessage
from debate.transport import ChannelPair, MessageTransport
from sdk.llm_client import LlmClient


class NoopTransport(MessageTransport):
    def write(self, message: DebateMessage) -> None:
        return None

    def read(self, timeout: float | None = None) -> DebateMessage | None:
        return None

    def close(self) -> None:
        return None


def make_llm_client(config: AppConfig) -> LlmClient:
    return LlmClient(
        cli_command=config.agents.cli_command,
        workdir=config.project_root / config.agents.workdir,
        timeout_seconds=config.debate.request_timeout_seconds,
        gemini_model=config.llm.gemini_model,
        gemini_fallback_models=config.llm.gemini_model_fallbacks,
        use_google_search=config.llm.use_google_search,
    )


def create_child_agent(
    role: AgentRole,
    config: AppConfig,
    session_id: str,
) -> ProAgent | ConAgent:
    gatekeeper = Gatekeeper(config.gatekeeper)
    client = make_llm_client(config)

    if role == AgentRole.PRO:
        return ProAgent(role, config, None, gatekeeper, client, session_id)

    if role == AgentRole.CON:
        return ConAgent(role, config, None, gatekeeper, client, session_id)

    raise ValueError(f"Child worker cannot use role: {role}")


def create_parent_agent(config: AppConfig, session_id: str) -> ParentAgent:
    gatekeeper = Gatekeeper(config.gatekeeper)
    client = make_llm_client(config)
    dummy_pair = ChannelPair(NoopTransport(), NoopTransport())

    return ParentAgent(
        config=config,
        gatekeeper=gatekeeper,
        client=client,
        session_id=session_id,
        pro_channel=dummy_pair,
        con_channel=dummy_pair,
    )
