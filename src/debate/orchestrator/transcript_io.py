from __future__ import annotations

from pathlib import Path

from debate.config import AppConfig


def write_transcript(config: AppConfig, session_id: str, transcript: str) -> Path:
    """Persist the full, untruncated debate transcript to ``logs/``.

    The live console/JSONL logs abbreviate each turn for readability; this
    file keeps every turn in full so a run can be reviewed verbatim.
    """
    out = config.project_root / "logs" / f"transcript_{session_id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"# Debate transcript — session {session_id}\n\n"
        f"Topic: {config.debate.topic}\n\n"
        f"Sides: {config.debate.pro_side} | {config.debate.con_side}\n\n---\n\n"
    )
    out.write_text(header + transcript + "\n", encoding="utf-8")
    return out
