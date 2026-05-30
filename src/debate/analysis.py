"""Parse and aggregate debate logs for the research notebook (§9).

Pure, side-effect-free functions so `notebooks/analysis.ipynb` stays thin
(it only loads data and plots). Everything here is unit-tested, keeping the
project's 100% coverage gate intact.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_TURN_HEADER = re.compile(
    r"^\[(?P<role>PRO|CON) defending '(?P<side>[^']*)' ping=(?P<ping>\d+)\]\s*(?P<text>.*)$"
)


@dataclass(frozen=True)
class VerdictRecord:
    session_id: str
    winner: str
    pro_score: float
    con_score: float

    @property
    def margin(self) -> float:
        return abs(self.pro_score - self.con_score)


@dataclass(frozen=True)
class TurnRecord:
    role: str
    side: str
    ping: int
    word_count: int
    citation_count: int


@dataclass(frozen=True)
class WinSummary:
    pro_wins: int
    con_wins: int
    total: int
    mean_margin: float


def parse_verdict(data: dict) -> VerdictRecord:
    payload = data["payload"]
    return VerdictRecord(
        session_id=str(data.get("session_id", "")),
        winner=str(payload["winner"]),
        pro_score=float(payload["pro_score"]),
        con_score=float(payload["con_score"]),
    )


def load_verdicts(directory: Path) -> list[VerdictRecord]:
    """Load every ``verdict*.json`` under a directory tree (logs/ or examples/)."""
    return [
        parse_verdict(json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(directory.rglob("verdict*.json"))
    ]


def dedupe_verdicts(records: list[VerdictRecord]) -> list[VerdictRecord]:
    """Keep one record per ``session_id`` (first wins).

    A worked example is committed under both ``examples/`` and ``logs/``, so
    aggregating both trees would otherwise count that session twice.
    """
    seen: set[str] = set()
    unique: list[VerdictRecord] = []
    for record in records:
        if record.session_id in seen:
            continue
        seen.add(record.session_id)
        unique.append(record)
    return unique


def _count_sources(line: str) -> int:
    body = line.split(":", 1)[1].strip()
    if not body or body.lower().startswith("no citation"):
        return 0
    return len([url for url in body.split(",") if url.strip()])


def parse_transcript(text: str) -> list[TurnRecord]:
    """Extract per-turn records from a saved transcript markdown file."""
    turns: list[TurnRecord] = []
    current: dict | None = None

    for line in text.splitlines():
        header = _TURN_HEADER.match(line.strip())
        if header:
            if current is not None:
                turns.append(_finalize(current))
            current = {
                "role": header["role"],
                "side": header["side"],
                "ping": int(header["ping"]),
                "words": len(header["text"].split()),
                "citations": 0,
            }
        elif current is not None and line.startswith("Sources:"):
            current["citations"] = _count_sources(line)

    if current is not None:
        turns.append(_finalize(current))
    return turns


def _finalize(current: dict) -> TurnRecord:
    return TurnRecord(
        role=current["role"],
        side=current["side"],
        ping=current["ping"],
        word_count=current["words"],
        citation_count=current["citations"],
    )


def summarize_verdicts(records: list[VerdictRecord]) -> WinSummary:
    pro = sum(1 for r in records if r.winner == "pro")
    con = sum(1 for r in records if r.winner == "con")
    total = len(records)
    mean_margin = sum(r.margin for r in records) / total if total else 0.0
    return WinSummary(pro_wins=pro, con_wins=con, total=total, mean_margin=mean_margin)


def mean_citations_per_role(turns: list[TurnRecord]) -> dict[str, float]:
    grouped: dict[str, list[int]] = {}
    for turn in turns:
        grouped.setdefault(turn.role, []).append(turn.citation_count)
    return {role: sum(counts) / len(counts) for role, counts in grouped.items()}
