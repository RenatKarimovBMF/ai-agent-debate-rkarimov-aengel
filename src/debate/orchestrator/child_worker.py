from __future__ import annotations

import logging
import multiprocessing as mp

from debate.config import AppConfig
from debate.logging_setup import setup_logging
from debate.models import AgentRole, DebateMessage
from debate.orchestrator.commands import RELAY, STOP, TURN_REQUEST, worker_error
from debate.orchestrator.events import emit_event
from debate.orchestrator.factory import create_child_agent


def child_worker(
    role_value: str,
    config: AppConfig,
    session_id: str,
    parent_to_child: mp.Queue,
    child_to_parent: mp.Queue,
    event_queue: mp.Queue,
) -> None:
    role = AgentRole(role_value)
    setup_logging(config.logging)

    log = logging.getLogger(f"debate.worker.{role.value}")
    log.info("%s process started", role.value.upper())

    agent = create_child_agent(role, config, session_id)
    last_opponent_text: str | None = None

    emit_event(event_queue, f"{role.value.upper()} PROCESS: started", kind="process")

    while True:
        try:
            command = parent_to_child.get()
            if not isinstance(command, dict):
                continue

            command_type = command.get("type")

            if command_type == STOP:
                emit_event(event_queue, f"{role.value.upper()} PROCESS: stopping", kind="process")
                break

            if command_type == RELAY:
                relayed = DebateMessage.model_validate(command["message"])
                last_opponent_text = relayed.payload.text
                emit_event(
                    event_queue,
                    f"{role.value.upper()} PROCESS: received relay from PARENT",
                    kind="ipc",
                    data={
                        "from": relayed.from_role.value,
                        "to": relayed.to_role.value,
                        "ping": relayed.payload.ping_number,
                    },
                )
                continue

            if command_type == TURN_REQUEST:
                ping = int(command["ping"])
                opponent_text = command.get("opponent_text") or last_opponent_text

                emit_event(
                    event_queue,
                    f"{role.value.upper()} PROCESS: ping {ping} LLM call started...",
                    kind="llm_start",
                    data={"role": role.value, "ping": ping},
                )

                message = agent.build_turn(ping, opponent_text)
                child_to_parent.put(message.model_dump(mode="json"))

                emit_event(
                    event_queue,
                    f"{role.value.upper()} PROCESS: ping {ping} answer ready",
                    kind="llm_done",
                    data={"role": role.value, "ping": ping},
                )
                continue

        except Exception as exc:
            log.exception("%s process failed", role.value.upper())
            child_to_parent.put(worker_error(role.value, str(exc)))
            emit_event(
                event_queue,
                f"{role.value.upper()} PROCESS ERROR: {exc}",
                kind="error",
                data={"role": role.value, "error": str(exc)},
            )
