from __future__ import annotations

import logging
from collections.abc import Callable

from debate.legacy.helpers import short_text
from debate.legacy.message_validation import require_message
from debate.legacy.setup import LegacyAgents
from debate.models import AgentRole

logger = logging.getLogger("debate.legacy.ping")


def run_single_ping(
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
    log_side(progress, "PRO", received_pro.payload.text, received_pro.payload.citations)

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
    log_side(progress, "CON", received_con.payload.text, received_con.payload.citations)

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


def log_side(
    progress: Callable[[str], None],
    label: str,
    text: str,
    citations,
) -> None:
    progress(f"{label} says: {short_text(text)}")
    urls = [citation.url for citation in citations]
    if urls:
        progress(f"{label} sources: {', '.join(urls)}")
