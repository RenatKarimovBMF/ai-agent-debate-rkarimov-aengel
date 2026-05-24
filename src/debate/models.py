from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    PARENT = "parent"
    PRO = "pro"
    CON = "con"


class MessageType(str, Enum):
    TURN = "turn"
    RELAY = "relay"
    VERDICT = "verdict"
    KEEPALIVE = "keepalive"
    ERROR = "error"


class Citation(BaseModel):
    title: str
    url: str


class DebatePayload(BaseModel):
    """Content carried between agents."""

    text: str
    ping_number: int | None = None
    responding_to_ping: int | None = None
    citations: list[Citation] = Field(default_factory=list)


class DebateMessage(BaseModel):
    """JSON protocol for all IPC (Exercise 02 §8.3.8)."""

    version: str = "1.0"
    type: MessageType
    from_role: AgentRole
    to_role: AgentRole
    session_id: str
    turn_id: int
    payload: DebatePayload

    def to_json_line(self) -> str:
        return self.model_dump_json() + "\n"

    @classmethod
    def from_json_line(cls, line: str) -> DebateMessage:
        return cls.model_validate_json(line.strip())


class VerdictPayload(BaseModel):
    winner: AgentRole
    pro_score: float = Field(ge=0, le=100)
    con_score: float = Field(ge=0, le=100)
    rationale: str
    persuasion_notes: str


class VerdictMessage(BaseModel):
    version: str = "1.0"
    type: MessageType = MessageType.VERDICT
    from_role: AgentRole = AgentRole.PARENT
    session_id: str
    payload: VerdictPayload

    def to_json_line(self) -> str:
        return self.model_dump_json() + "\n"


def message_from_dict(data: dict[str, Any]) -> DebateMessage | VerdictMessage:
    msg_type = data.get("type")
    if msg_type == MessageType.VERDICT.value:
        return VerdictMessage.model_validate(data)
    return DebateMessage.model_validate(data)
