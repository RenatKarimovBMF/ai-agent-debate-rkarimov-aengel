from __future__ import annotations

import logging
import multiprocessing as mp

from debate.agents import ParentAgent
from debate.config import AppConfig
from debate.models import AgentRole, DebateMessage
from debate.orchestrator.commands import relay_message
from debate.orchestrator.events import emit_event
from debate.orchestrator.intervention import solicit_turn
from debate.orchestrator.messages import make_relay


def _announce_turn(event_queue: mp.Queue, label: str, message: DebateMessage) -> None:
    emit_event(event_queue, f"{label} says: {message.payload.text}")
    if message.payload.citations:
        emit_event(
            event_queue,
            f"{label} sources: " + ", ".join(c.url for c in message.payload.citations),
        )


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
    pro_msg = solicit_turn(
        role=AgentRole.PRO,
        ping=ping,
        opponent_text=last_con,
        request_queue=parent_to_pro,
        response_queue=pro_to_parent,
        session_id=session_id,
        event_queue=event_queue,
        timeout=timeout,
    )
    parent.record_turn(pro_msg)
    last_pro = pro_msg.payload.text
    _announce_turn(event_queue, "PRO", pro_msg)

    emit_event(event_queue, "PARENT: received PRO argument and relays it to CON.")
    parent_to_con.put(relay_message(make_relay(pro_msg, AgentRole.CON).model_dump(mode="json")))

    emit_event(event_queue, "")
    emit_event(event_queue, f"PING {ping}/{pings} — PARENT asks CON to respond")
    con_msg = solicit_turn(
        role=AgentRole.CON,
        ping=ping,
        opponent_text=last_pro,
        request_queue=parent_to_con,
        response_queue=con_to_parent,
        session_id=session_id,
        event_queue=event_queue,
        timeout=timeout,
    )
    parent.record_turn(con_msg)
    last_con = con_msg.payload.text
    _announce_turn(event_queue, "CON", con_msg)

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
