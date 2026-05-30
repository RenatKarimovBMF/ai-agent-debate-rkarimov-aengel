"""End-to-end parent orchestration with a FAKE LLM (no network, no procs).

Real ``ParentAgent``/``ProAgent``/``ConAgent`` are built through the
orchestrator factory; only ``LlmClient.complete`` is stubbed. The child
turn outputs are pre-computed and pushed onto in-process queues so
``parent_worker`` runs the genuine ASSIGN -> ping -> relay -> verdict
path for ``pings_per_side=1``.
"""

from __future__ import annotations

import json
import queue as _queue
from dataclasses import replace

import pytest

from debate.config import load_config
from debate.models import AgentRole
from debate.orchestrator import parent_worker as pw
from debate.orchestrator.factory import create_child_agent
from sdk.llm_client import LlmClient, LlmResponse


class _FakeQueue:
    def __init__(self, items=None) -> None:
        self.items = list(items or [])
        self.puts: list = []

    def put(self, item) -> None:
        self.items.append(item)
        self.puts.append(item)

    def get(self, timeout=None):
        if not self.items:
            raise _queue.Empty
        return self.items.pop(0)


def _fake_complete(self, system, user):
    if "JUDGE" in system:
        body = json.dumps({
            "winner": "pro",
            "pro_score": 82,
            "con_score": 74,
            "rationale": "Pro framed the winning standard and answered the clash.",
            "persuasion_notes": "Clash and method favoured pro (principle 2).",
        })
    else:
        body = json.dumps({
            "text": "My single strongest argument, grounded in a real source.",
            "citations": [{"title": "Source", "url": "https://example.com/a"}],
        })
    return LlmResponse(text=body, raw=body, provider="fake")


@pytest.fixture
def fake_llm(monkeypatch):
    monkeypatch.setattr(LlmClient, "complete", _fake_complete)
    monkeypatch.setattr(pw, "setup_logging", lambda *_: None)


def _config(tmp_path):
    cfg = load_config()
    return replace(
        cfg,
        project_root=tmp_path,
        debate=replace(cfg.debate, pings_per_side=1),
    )


def test_full_debate_produces_verdict(fake_llm, tmp_path):
    cfg = _config(tmp_path)

    pro = create_child_agent(AgentRole.PRO, cfg, "sess")
    pro.apply_assignment("Side A", "Side B")
    pro_msg = pro.build_turn(1, None).model_dump(mode="json")

    con = create_child_agent(AgentRole.CON, cfg, "sess")
    con.apply_assignment("Side B", "Side A")
    con_msg = con.build_turn(1, "opening argument").model_dump(mode="json")

    parent_to_pro = _FakeQueue()
    parent_to_con = _FakeQueue()
    events = _FakeQueue()

    pw.parent_worker(
        cfg,
        "sess",
        _FakeQueue([{"type": "START"}]),
        events,
        parent_to_pro,
        _FakeQueue([pro_msg]),
        parent_to_con,
        _FakeQueue([con_msg]),
    )

    verdict_file = tmp_path / "logs" / "verdict_sess.json"
    assert verdict_file.is_file()
    saved = json.loads(verdict_file.read_text(encoding="utf-8"))
    assert saved["payload"]["winner"] == "pro"

    pro_types = [c["type"] for c in parent_to_pro.puts]
    assert pro_types[0] == "ASSIGN"
    assert "TURN_REQUEST" in pro_types and "RELAY" in pro_types
    assert pro_types[-1] == "STOP"

    kinds = [e.get("kind") for e in events.puts]
    assert "done" in kinds
    assert any("FINAL VERDICT" in str(e.get("message", "")) for e in events.puts)
