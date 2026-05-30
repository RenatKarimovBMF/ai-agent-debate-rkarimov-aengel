from __future__ import annotations

import logging
import multiprocessing as mp

from debate.agents import ParentAgent
from debate.config import AppConfig
from debate.models import AgentRole
from debate.orchestrator.commands import relay_message, turn_request
from debate.orchestrator.events import emit_event, queue_get_or_timeout
from debate.orchestrator.messages import make_relay, validate_child_message


def run_ping_round(
    *,
    ping: int,
    pings: int,
    config: AppConfig,
    session_id: str,
    parent: ParentAgent,
    parent_to_pro: mp.Queue,
    pro_to_parent: mp.Queue,
    parent_to_con: mp.Queue,
    con_to_parent: mp.Queue,
    event_queue: mp.Queue,
    timeout: float,
    last_pro: str | None,
    last_con: str | None,
) -> tuple[str | None, str | None]:
    log = logging.getLogger("debate.worker.parent")

    emit_event(event_queue, "")
    emit_event(event_queue, f"PING {ping}/{pings} — PARENT asks PRO to argue")
    parent_to_pro.put(turn_request(ping, last_con))

    raw_pro = queue_get_or_timeout(pro_to_parent, timeout, "PRO response")
    pro_msg = validate_child_message(
        raw_pro,
        expected_sender=AgentRole.PRO,
        session_id=session_id,
        ping=ping,
    )

    parent.record_turn(pro_msg)
    last_pro = pro_msg.payload.text

    emit_event(event_queue, f"PRO says: {last_pro}")
    if pro_msg.payload.citations:
        emit_event(
            event_queue,
            "PRO sources: " + ", ".join(c.url for c in pro_msg.payload.citations),
        )

    emit_event(event_queue, "PARENT: received PRO argument and relays it to CON.")
    parent_to_con.put(relay_message(make_relay(pro_msg, AgentRole.CON).model_dump(mode="json")))

    emit_event(event_queue, "")
    emit_event(event_queue, f"PING {ping}/{pings} — PARENT asks CON to respond")
    parent_to_con.put(turn_request(ping, last_pro))

    raw_con = queue_get_or_timeout(con_to_parent, timeout, "CON response")
    con_msg = validate_child_message(
        raw_con,
        expected_sender=AgentRole.CON,
        session_id=session_id,
        ping=ping,
    )

    parent.record_turn(con_msg)
    last_con = con_msg.payload.text

    emit_event(event_queue, f"CON says: {last_con}")
    if con_msg.payload.citations:
        emit_event(
            event_queue,
            "CON sources: " + ", ".join(c.url for c in con_msg.payload.citations),
        )

    emit_event(event_queue, "PARENT: received CON counterargument and relays it to PRO.")
    parent_to_pro.put(relay_message(make_relay(con_msg, AgentRole.PRO).model_dump(mode="json")))

    log.info(
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
