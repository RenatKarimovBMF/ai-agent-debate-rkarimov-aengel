from __future__ import annotations

import multiprocessing as mp
import time
from pathlib import Path

from debate.config import AppConfig
from debate.models import VerdictMessage
from debate.orchestrator.events import emit_event


def save_verdict(
    config: AppConfig,
    session_id: str,
    verdict: VerdictMessage,
    event_queue: mp.Queue,
) -> Path:
    out = config.project_root / "logs" / f"verdict_{session_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(verdict.to_json_line(), encoding="utf-8")

    winner = verdict.payload.winner.value.upper()

    emit_event(event_queue, "")
    emit_event(event_queue, "=" * 72)
    emit_event(event_queue, f"FINAL VERDICT: {winner} wins")
    emit_event(event_queue, f"PRO score: {verdict.payload.pro_score}")
    emit_event(event_queue, f"CON score: {verdict.payload.con_score}")
    emit_event(event_queue, f"Judge rationale: {verdict.payload.rationale}")
    emit_event(event_queue, f"Persuasion notes: {verdict.payload.persuasion_notes}")
    emit_event(event_queue, f"Verdict saved to: {out}")
    emit_event(event_queue, "=" * 72)

    event_queue.put(
        {
            "kind": "done",
            "message": str(out),
            "data": {"verdict_path": str(out)},
            "time": time.time(),
        }
    )

    return out
