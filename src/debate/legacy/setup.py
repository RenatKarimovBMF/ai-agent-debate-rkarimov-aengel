from __future__ import annotations

from dataclasses import dataclass

from debate.agents import ConAgent, ParentAgent, ProAgent
from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.models import AgentRole
from debate.transport import ChannelPair, build_channels
from sdk.llm_client import LlmClient


@dataclass(frozen=True)
class LegacyAgents:
    parent: ParentAgent
    pro: ProAgent
    con: ConAgent
    pro_channels: ChannelPair
    con_channels: ChannelPair


def clear_ipc_queues(config: AppConfig) -> None:
    fifo_dir = config.project_root / config.ipc.fifo_dir
    fifo_dir.mkdir(parents=True, exist_ok=True)

    for path in fifo_dir.glob("*"):
        if path.is_file() and path.name != ".gitkeep":
            path.unlink(missing_ok=True)


def build_legacy_agents(
    config: AppConfig,
    session_id: str,
    gatekeeper: Gatekeeper,
    client: LlmClient,
) -> LegacyAgents:
    root = config.project_root
    pro_channels = build_channels(config.ipc, "pro", root)
    con_channels = build_channels(config.ipc, "con", root)

    parent = ParentAgent(
        config,
        gatekeeper,
        client,
        session_id,
        pro_channels,
        con_channels,
    )

    pro = ProAgent(
        AgentRole.PRO,
        config,
        pro_channels,
        gatekeeper,
        client,
        session_id,
    )

    con = ConAgent(
        AgentRole.CON,
        config,
        con_channels,
        gatekeeper,
        client,
        session_id,
    )

    return LegacyAgents(
        parent=parent,
        pro=pro,
        con=con,
        pro_channels=pro_channels,
        con_channels=con_channels,
    )
