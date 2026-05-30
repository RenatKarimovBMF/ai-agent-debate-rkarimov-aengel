"""Drive the legacy ``run_debate_session`` / ``run_single_ping`` with fakes.

Fake agents return canned messages so the full session loop, relay
hand-off, citation logging, and verdict write-out run in-process with no
LLM and no real IPC channels.
"""

from __future__ import annotations

from dataclasses import replace

from debate.config import load_config
from debate.legacy.session_loop import run_debate_session
from debate.legacy.setup import LegacyAgents
from debate.models import (
    AgentRole,
    Citation,
    DebateMessage,
    DebatePayload,
    MessageType,
    VerdictMessage,
    VerdictPayload,
)


def _turn(role: AgentRole, ping: int, *, cite: bool) -> DebateMessage:
    cits = [Citation(title="t", url="https://e.com")] if cite else []
    return DebateMessage(
        type=MessageType.TURN,
        from_role=role,
        to_role=AgentRole.PARENT,
        session_id="sess",
        turn_id=1,
        payload=DebatePayload(text=f"{role.value} text", ping_number=ping, citations=cits),
    )


def _relay(target: AgentRole, ping: int) -> DebateMessage:
    return DebateMessage(
        type=MessageType.RELAY,
        from_role=AgentRole.PARENT,
        to_role=target,
        session_id="sess",
        turn_id=1,
        payload=DebatePayload(text="relayed", ping_number=ping, citations=[]),
    )


class _FakeChild:
    def __init__(self, turn_msg, relay_msg) -> None:
        self._turn = turn_msg
        self._relay = relay_msg
        self.sent: list = []

    def build_turn(self, ping, opponent_text):
        return self._turn

    def send(self, message) -> None:
        self.sent.append(message)

    def receive(self, timeout):
        return self._relay


class _FakeParent:
    def __init__(self, pro_turn, con_turn, verdict) -> None:
        self._pro = pro_turn
        self._con = con_turn
        self._verdict = verdict
        self.recorded: list = []

    def receive_from_child(self, role, timeout):
        return self._pro if role == AgentRole.PRO else self._con

    def record_turn(self, message) -> None:
        self.recorded.append(message)

    def relay_to_child(self, message, target) -> None:
        return None

    def render_verdict(self):
        return self._verdict


def test_run_debate_session_writes_verdict(tmp_path):
    cfg = load_config()
    cfg = replace(
        cfg,
        project_root=tmp_path,
        debate=replace(cfg.debate, pings_per_side=1),
    )

    pro_turn = _turn(AgentRole.PRO, 1, cite=True)
    con_turn = _turn(AgentRole.CON, 1, cite=False)
    verdict = VerdictMessage(
        session_id="sess",
        payload=VerdictPayload(
            winner=AgentRole.PRO,
            pro_score=60,
            con_score=40,
            rationale="reason",
            persuasion_notes="notes",
        ),
    )
    agents = LegacyAgents(
        parent=_FakeParent(pro_turn, con_turn, verdict),
        pro=_FakeChild(pro_turn, _relay(AgentRole.PRO, 1)),
        con=_FakeChild(con_turn, _relay(AgentRole.CON, 1)),
        pro_channels=None,
        con_channels=None,
    )

    logs: list[str] = []
    beats: list[int] = []
    out = run_debate_session(cfg, "sess", agents, logs.append, lambda: beats.append(1))

    assert out.is_file()
    assert "PRO wins" in "\n".join(logs)
    assert beats, "heartbeat should fire at least once"
    assert len(agents.parent.recorded) == 2
