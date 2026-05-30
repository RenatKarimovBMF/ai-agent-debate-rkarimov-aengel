from __future__ import annotations

import logging
import multiprocessing as mp

from debate.config import AppConfig
from debate.logging_setup import setup_logging
from debate.models import AgentRole
from debate.orchestrator.commands import START, STOP
from debate.orchestrator.events import emit_event
from debate.orchestrator.factory import create_parent_agent
from debate.orchestrator.host_protocol import send_assignments
from debate.orchestrator.ping_round import run_ping_round
from debate.orchestrator.transcript_io import write_transcript
from debate.orchestrator.verdict_io import save_verdict


def parent_worker(
    config: AppConfig,
    session_id: str,
    command_queue: mp.Queue,
    event_queue: mp.Queue,
    parent_to_pro: mp.Queue,
    pro_to_parent: mp.Queue,
    parent_to_con: mp.Queue,
    con_to_parent: mp.Queue,
) -> None:
    setup_logging(config.logging)

    log = logging.getLogger("debate.worker.parent")
    log.info("PARENT process started")

    parent = create_parent_agent(config, session_id)
    emit_event(event_queue, "PARENT PROCESS: started", kind="process")

    try:
        command = command_queue.get()
        if command.get("type") != START:
            raise RuntimeError("Parent expected START command")

        pings = config.debate.pings_per_side
        timeout = float(config.debate.request_timeout_seconds)

        emit_event(event_queue, "=" * 72)
        emit_event(event_queue, f"SESSION: {session_id}")
        emit_event(event_queue, f"TOPIC: {config.debate.topic}")
        emit_event(
            event_queue,
            f"OPTIONS ON THE TABLE: {config.debate.pro_side} | {config.debate.con_side}",
        )
        emit_event(event_queue, f"PINGS PER SIDE: {pings}")
        emit_event(event_queue, f"TIMEOUT PER LLM CALL: {timeout:.0f} seconds")
        emit_event(event_queue, "=" * 72)

        sides = send_assignments(
            config=config,
            session_id=session_id,
            parent_to_pro=parent_to_pro,
            parent_to_con=parent_to_con,
            event_queue=event_queue,
        )
        parent.apply_assignment(
            pro_side=sides[AgentRole.PRO],
            con_side=sides[AgentRole.CON],
        )

        last_pro: str | None = None
        last_con: str | None = None

        for ping in range(1, pings + 1):
            last_pro, last_con = run_ping_round(
                ping=ping,
                pings=pings,
                config=config,
                session_id=session_id,
                parent=parent,
                parent_to_pro=parent_to_pro,
                pro_to_parent=pro_to_parent,
                parent_to_con=parent_to_con,
                con_to_parent=con_to_parent,
                event_queue=event_queue,
                timeout=timeout,
                last_pro=last_pro,
                last_con=last_con,
            )

        emit_event(event_queue, "")
        emit_event(event_queue, "PARENT/JUDGE: Debate finished. Judge is choosing a winner...")
        transcript_path = write_transcript(config, session_id, parent.transcript_text())
        emit_event(event_queue, f"Full transcript saved to: {transcript_path}")
        save_verdict(config, session_id, parent.render_verdict(), event_queue)

    except Exception as exc:
        log.exception("PARENT process failed")
        emit_event(
            event_queue,
            f"PARENT PROCESS ERROR: {exc}",
            kind="error",
            data={"error": str(exc)},
        )

    finally:
        parent_to_pro.put({"type": STOP})
        parent_to_con.put({"type": STOP})
        emit_event(event_queue, "PARENT PROCESS: stopped", kind="process")
