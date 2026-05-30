"""Cover the research-notebook helpers in `debate.analysis`."""

from __future__ import annotations

import json

from debate.analysis import (
    dedupe_verdicts,
    load_verdicts,
    mean_citations_per_role,
    parse_transcript,
    parse_verdict,
    summarize_verdicts,
)

_VERDICT = {
    "session_id": "abc",
    "payload": {"winner": "con", "pro_score": 78.0, "con_score": 83.0},
}

_TRANSCRIPT = (
    "# header noise\n"
    "\n"
    "[PRO defending 'Alpha' ping=1] One two three four.\n"
    "Sources: https://a.com, https://b.com\n"
    "\n"
    "[CON defending 'Beta' ping=1] Five six.\n"
    "Sources: no citations\n"
)


def test_parse_verdict_and_margin():
    record = parse_verdict(_VERDICT)
    assert record.winner == "con"
    assert record.margin == 5.0


def test_load_verdicts_reads_tree(tmp_path):
    (tmp_path / "verdict_one.json").write_text(json.dumps(_VERDICT), encoding="utf-8")
    nested = tmp_path / "examples"
    nested.mkdir()
    (nested / "verdict.json").write_text(json.dumps(_VERDICT), encoding="utf-8")

    records = load_verdicts(tmp_path)
    assert len(records) == 2
    assert all(r.con_score == 83.0 for r in records)


def test_parse_transcript_counts_words_and_citations():
    turns = parse_transcript(_TRANSCRIPT)
    assert len(turns) == 2
    pro, con = turns
    assert pro.role == "PRO" and pro.side == "Alpha"
    assert pro.word_count == 4 and pro.citation_count == 2
    assert con.citation_count == 0


def test_summarize_verdicts_with_and_without_records():
    records = [parse_verdict(_VERDICT)]
    summary = summarize_verdicts(records)
    assert summary.con_wins == 1 and summary.pro_wins == 0
    assert summary.total == 1 and summary.mean_margin == 5.0

    empty = summarize_verdicts([])
    assert empty.total == 0 and empty.mean_margin == 0.0


def test_dedupe_verdicts_keeps_one_per_session():
    a = parse_verdict(_VERDICT)  # session "abc"
    b = parse_verdict({**_VERDICT, "session_id": "xyz"})
    dup = parse_verdict(_VERDICT)  # session "abc" again
    unique = dedupe_verdicts([a, b, dup])
    assert [r.session_id for r in unique] == ["abc", "xyz"]


def test_mean_citations_per_role():
    turns = parse_transcript(_TRANSCRIPT)
    means = mean_citations_per_role(turns)
    assert means["PRO"] == 2.0
    assert means["CON"] == 0.0
