"""Coverage for the full-transcript writer and ParentAgent.transcript_text."""

from __future__ import annotations

from dataclasses import replace

from debate.agents.parent_agent import ParentAgent
from debate.config import load_config
from debate.orchestrator.transcript_io import write_transcript
from debate.transport import ChannelPair

from ._coverage_helpers import MagicMock, make_gatekeeper, make_message


def _config(tmp_path):
    cfg = load_config()
    return replace(cfg, project_root=tmp_path)


def test_write_transcript_persists_full_text(tmp_path):
    cfg = _config(tmp_path)
    out = write_transcript(cfg, "sess123", "PRO: full argument\n\nCON: full rebuttal")

    assert out == tmp_path / "logs" / "transcript_sess123.md"
    body = out.read_text(encoding="utf-8")
    assert "session sess123" in body
    assert cfg.debate.topic in body
    assert "PRO: full argument" in body
    assert "CON: full rebuttal" in body


def test_parent_transcript_text_joins_history(tmp_path):
    cfg = _config(tmp_path)
    pair = ChannelPair(MagicMock(), MagicMock())
    parent = ParentAgent(cfg, make_gatekeeper(), MagicMock(), "sess", pair, pair)

    assert parent.transcript_text() == ""

    parent.record_turn(make_message())
    text = parent.transcript_text()
    assert "PRO" in text and "ping=1" in text
