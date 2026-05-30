from __future__ import annotations

import pytest

from debate.config import load_config
from debate.models import AgentRole
from debate.orchestrator.commands import ASSIGN
from debate.orchestrator.host_protocol import decide_sides, send_assignments

from ._coverage_helpers import FakeQueue


def test_decide_sides_is_deterministic_for_same_session():
    cfg = load_config()
    first = decide_sides(cfg, session_id="abc123")
    second = decide_sides(cfg, session_id="abc123")
    assert first == second


def test_decide_sides_differs_across_sessions_overall():
    cfg = load_config()
    results = {
        decide_sides(cfg, session_id=f"session-{i}")[AgentRole.PRO]
        for i in range(20)
    }
    assert len(results) == 2, "Over 20 sessions both options should appear in Pro"


def test_decide_sides_env_override_option_a(monkeypatch):
    monkeypatch.setenv("DEBATE_PRO_ASSIGNMENT", "option_a")
    cfg = load_config()
    sides = decide_sides(cfg, session_id="whatever")
    assert sides[AgentRole.PRO] == cfg.debate.pro_side
    assert sides[AgentRole.CON] == cfg.debate.con_side


def test_decide_sides_env_override_option_b(monkeypatch):
    monkeypatch.setenv("DEBATE_PRO_ASSIGNMENT", "option_b")
    cfg = load_config()
    sides = decide_sides(cfg, session_id="whatever")
    assert sides[AgentRole.PRO] == cfg.debate.con_side
    assert sides[AgentRole.CON] == cfg.debate.pro_side


def test_send_assignments_puts_one_message_per_child():
    cfg = load_config()
    # FakeQueue (list-backed) avoids spawning real mp.Queue feeder threads,
    # which linger and crash under coverage's tracer during GC (CI SIGILL).
    parent_to_pro: FakeQueue = FakeQueue()
    parent_to_con: FakeQueue = FakeQueue()
    events: FakeQueue = FakeQueue()

    sides = send_assignments(
        config=cfg,
        session_id="sess",
        parent_to_pro=parent_to_pro,
        parent_to_con=parent_to_con,
        event_queue=events,
    )

    pro_cmd = parent_to_pro.get(timeout=2)
    con_cmd = parent_to_con.get(timeout=2)

    for cmd in (pro_cmd, con_cmd):
        assert cmd["type"] == ASSIGN
        assert cmd["topic"] == cfg.debate.topic
        assert cmd["pings"] == cfg.debate.pings_per_side
        assert cmd["max_words"] == cfg.debate.max_words_per_turn
        assert cmd["rules"], "rules list must not be empty"

    assert pro_cmd["assigned_side"] == sides[AgentRole.PRO]
    assert con_cmd["assigned_side"] == sides[AgentRole.CON]
    assert pro_cmd["opponent_side"] == sides[AgentRole.CON]
    assert con_cmd["opponent_side"] == sides[AgentRole.PRO]


def test_debater_agent_uses_runtime_assignment():
    from debate.agents.pro_agent import ProAgent
    from debate.config import GatekeeperConfig
    from debate.gatekeeper import Gatekeeper

    class _DummyClient:
        def active_provider(self) -> str:
            return ""

        def complete(self, system, user):  # pragma: no cover - not exercised
            raise NotImplementedError

    cfg = load_config()
    gk = Gatekeeper(GatekeeperConfig(enabled=False, max_total_requests=1, max_requests_per_agent=1))
    agent = ProAgent(AgentRole.PRO, cfg, None, gk, _DummyClient(), "s1")

    agent.apply_assignment("CustomSideX", "OpponentSideY")
    prompt = agent.system_prompt()

    assert "CustomSideX" in prompt
    assert "OpponentSideY" in prompt
    assert "refut" in prompt.lower(), "prompt must mention the refute-with-citation rule"
    assert "cite" in prompt.lower() or "citation" in prompt.lower()


def test_decide_sides_default_no_env(monkeypatch):
    monkeypatch.delenv("DEBATE_PRO_ASSIGNMENT", raising=False)
    cfg = load_config()
    sides = decide_sides(cfg, session_id="x")
    assert set(sides.values()) == {cfg.debate.pro_side, cfg.debate.con_side}


def test_assign_command_helper():
    from debate.orchestrator.commands import assignment

    cmd = assignment(
        role="pro",
        topic="t",
        assigned_side="A",
        opponent_side="B",
        pings=3,
        max_words=100,
        rules=["r1", "r2"],
    )
    assert cmd["type"] == ASSIGN
    assert cmd["assigned_side"] == "A"
    assert cmd["opponent_side"] == "B"
    assert cmd["rules"] == ["r1", "r2"]


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    monkeypatch.delenv("DEBATE_PRO_ASSIGNMENT", raising=False)
    yield
