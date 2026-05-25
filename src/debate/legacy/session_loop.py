from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from debate.config import AppConfig
from debate.legacy.helpers import short_text
from debate.legacy.message_validation import require_message
from debate.legacy.setup import LegacyAgents
from debate.models import AgentRole

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
        last_pro, last_con = _run_single_ping(
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


def _run_single_ping(
    *,
    ping: int,
    pings: int,
    session_id: str,
    agents: LegacyAgents,
    progress: Callable[[str], None],
    heartbeat: Callable[[], None],
    timeout: float,
    last_pro: str | None,
    last_con: str | None,
) -> tuple[str | None, str | None]:
    heartbeat()

    progress("")
    progress(f"PING {ping}/{pings} — PRO is thinking...")
    pro_msg = agents.pro.build_turn(ping, last_con)
    agents.pro.send(pro_msg)

    received_pro = agents.parent.receive_from_child(AgentRole.PRO, timeout=timeout)
    received_pro = require_message(
        received_pro,
        session_id=session_id,
        expected_original_sender=AgentRole.PRO,
        ping=ping,
    )

    agents.parent.record_turn(received_pro)
    last_pro = received_pro.payload.text
    _log_side(progress, "PRO", received_pro.payload.text, received_pro.payload.citations)

    progress("PARENT: received PRO argument and relays it to CON.")
    agents.parent.relay_to_child(received_pro, AgentRole.CON)

    relayed_to_con = agents.con.receive(timeout=timeout)
    last_pro = require_message(
        relayed_to_con,
        session_id=session_id,
        expected_original_sender=AgentRole.PRO,
        ping=ping,
    ).payload.text

    heartbeat()
    progress("")
    progress(f"PING {ping}/{pings} — CON is thinking...")
    con_msg = agents.con.build_turn(ping, last_pro)
    agents.con.send(con_msg)

    received_con = agents.parent.receive_from_child(AgentRole.CON, timeout=timeout)
    received_con = require_message(
        received_con,
        session_id=session_id,
        expected_original_sender=AgentRole.CON,
        ping=ping,
    )

    agents.parent.record_turn(received_con)
    last_con = received_con.payload.text
    _log_side(progress, "CON", received_con.payload.text, received_con.payload.citations)

    progress("PARENT: received CON counterargument and relays it to PRO.")
    agents.parent.relay_to_child(received_con, AgentRole.PRO)

    relayed_to_pro = agents.pro.receive(timeout=timeout)
    last_con = require_message(
        relayed_to_pro,
        session_id=session_id,
        expected_original_sender=AgentRole.CON,
        ping=ping,
    ).payload.text

    logger.info(
        "Ping complete",
        extra={
            "extra_data": {
                "ping": ping,
                "pro_words": len((last_pro or "").split()),
                "con_words": len((last_con or "").split()),
            }
        },
    )

    return last_pro, last_con


def _log_side(progress: Callable[[str], None], label: str, text: str, citations) -> None:
    progress(f"{label} says: {short_text(text)}")
    urls = [citation.url for citation in citations]
    if urls:
        progress(f"{label} sources: {', '.join(urls)}")
