from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from debate.config import AppConfig
from debate.legacy.ping_runner import run_single_ping
from debate.legacy.setup import LegacyAgents

logger = logging.getLogger("debate.legacy.session")


def run_debate_session(
    config: AppConfig,
    session_id: str,
    agents: LegacyAgents,
    progress: Callable[[str], None],
    heartbeat: Callable[[], None],
) -> Path:
    pings = config.debate.pings_per_side
    timeout = float(config.debate.request_timeout_seconds)

    progress("=" * 72)
    progress(f"SESSION: {session_id}")
    progress(f"TOPIC: {config.debate.topic}")
    progress(f"PRO: {config.debate.pro_side}")
    progress(f"CON: {config.debate.con_side}")
    progress(f"PINGS PER SIDE: {pings}")
    progress(f"TIMEOUT PER LLM CALL: {timeout:.0f} seconds")
    progress("=" * 72)

    last_pro: str | None = None
    last_con: str | None = None

    for ping in range(1, pings + 1):
        last_pro, last_con = run_single_ping(
            ping=ping,
            pings=pings,
            session_id=session_id,
            agents=agents,
            progress=progress,
            heartbeat=heartbeat,
            timeout=timeout,
            last_pro=last_pro,
            last_con=last_con,
        )

    heartbeat()
    progress("")
    progress("PARENT/JUDGE: Debate finished. Judge is choosing a winner...")
    verdict = agents.parent.render_verdict()

    out = config.project_root / "logs" / f"verdict_{session_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(verdict.to_json_line(), encoding="utf-8")

    winner = verdict.payload.winner.value.upper()
    progress("")
    progress("=" * 72)
    progress(f"FINAL VERDICT: {winner} wins")
    progress(f"PRO score: {verdict.payload.pro_score}")
    progress(f"CON score: {verdict.payload.con_score}")
    progress(f"Judge rationale: {verdict.payload.rationale}")
    progress(f"Persuasion notes: {verdict.payload.persuasion_notes}")
    progress(f"Verdict saved to: {out}")
    progress("=" * 72)

    logger.info("Verdict", extra={"extra_data": verdict.model_dump()})
    return out
