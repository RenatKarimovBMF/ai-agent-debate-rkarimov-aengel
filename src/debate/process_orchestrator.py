from __future__ import annotations

import logging
import multiprocessing as mp
import queue
import threading
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from debate.agents import ConAgent, ParentAgent, ProAgent
from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.logging_setup import setup_logging
from debate.models import AgentRole, DebateMessage, MessageType
from debate.transport import ChannelPair, MessageTransport
from sdk.llm_client import LlmClient

logger = logging.getLogger("debate.process_orchestrator")

ProgressCallback = Callable[[str], None]


class _NoopTransport(MessageTransport):
    """Used only so ParentAgent can be constructed inside the parent process.

    In multiprocessing mode, real IPC is done with multiprocessing.Queue.
    """

    def write(self, message: DebateMessage) -> None:
        return None

    def read(self, timeout: float | None = None) -> DebateMessage | None:
        return None

    def close(self) -> None:
        return None


def _make_client(config: AppConfig) -> LlmClient:
    return LlmClient(
        cli_command=config.agents.cli_command,
        workdir=config.project_root / config.agents.workdir,
        timeout_seconds=config.debate.request_timeout_seconds,
        gemini_model=config.llm.gemini_model,
        gemini_fallback_models=config.llm.gemini_model_fallbacks,
        use_google_search=config.llm.use_google_search,
    )


def _short_text(text: str, limit: int = 700) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + "..."


def _event(
    event_queue: mp.Queue,
    message: str,
    *,
    kind: str = "progress",
    data: dict[str, Any] | None = None,
) -> None:
    payload = {
        "kind": kind,
        "message": message,
        "data": data or {},
        "time": time.time(),
    }
    event_queue.put(payload)


def _queue_get_or_timeout(q: mp.Queue, timeout: float, label: str) -> Any:
    try:
        return q.get(timeout=timeout)
    except queue.Empty as exc:
        raise TimeoutError(f"Timeout while waiting for {label}") from exc


def _create_child_agent(
    role: AgentRole,
    config: AppConfig,
    session_id: str,
) -> ProAgent | ConAgent:
    gatekeeper = Gatekeeper(config.gatekeeper)
    client = _make_client(config)

    if role == AgentRole.PRO:
        return ProAgent(role, config, None, gatekeeper, client, session_id)

    if role == AgentRole.CON:
        return ConAgent(role, config, None, gatekeeper, client, session_id)

    raise ValueError(f"Child worker cannot use role: {role}")


def _child_worker(
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

    agent = _create_child_agent(role, config, session_id)
    last_opponent_text: str | None = None

    _event(event_queue, f"{role.value.upper()} PROCESS: started", kind="process")

    while True:
        try:
            command = parent_to_child.get()

            if not isinstance(command, dict):
                continue

            command_type = command.get("type")

            if command_type == "STOP":
                _event(event_queue, f"{role.value.upper()} PROCESS: stopping", kind="process")
                break

            if command_type == "RELAY":
                relayed = DebateMessage.model_validate(command["message"])
                last_opponent_text = relayed.payload.text
                _event(
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

            if command_type == "TURN_REQUEST":
                ping = int(command["ping"])
                opponent_text = command.get("opponent_text") or last_opponent_text

                _event(
                    event_queue,
                    f"{role.value.upper()} PROCESS: ping {ping} LLM call started...",
                    kind="llm_start",
                    data={"role": role.value, "ping": ping},
                )

                if role == AgentRole.PRO:
                    assert isinstance(agent, ProAgent)
                    message = agent.build_turn(ping, opponent_text)
                else:
                    assert isinstance(agent, ConAgent)
                    message = agent.build_turn(ping, opponent_text)

                child_to_parent.put(message.model_dump(mode="json"))

                _event(
                    event_queue,
                    f"{role.value.upper()} PROCESS: ping {ping} answer ready",
                    kind="llm_done",
                    data={"role": role.value, "ping": ping},
                )
                continue

        except Exception as exc:
            log.exception("%s process failed", role.value.upper())
            child_to_parent.put(
                {
                    "type": "ERROR",
                    "role": role.value,
                    "error": str(exc),
                }
            )
            _event(
                event_queue,
                f"{role.value.upper()} PROCESS ERROR: {exc}",
                kind="error",
                data={"role": role.value, "error": str(exc)},
            )


def _make_parent_agent(config: AppConfig, session_id: str) -> ParentAgent:
    gatekeeper = Gatekeeper(config.gatekeeper)
    client = _make_client(config)

    dummy_pair = ChannelPair(_NoopTransport(), _NoopTransport())

    return ParentAgent(
        config=config,
        gatekeeper=gatekeeper,
        client=client,
        session_id=session_id,
        pro_channel=dummy_pair,
        con_channel=dummy_pair,
    )


def _validate_child_message(
    raw: Any,
    *,
    expected_sender: AgentRole,
    session_id: str,
    ping: int,
) -> DebateMessage:
    if isinstance(raw, dict) and raw.get("type") == "ERROR":
        raise RuntimeError(f"{raw.get('role')} worker failed: {raw.get('error')}")

    message = DebateMessage.model_validate(raw)

    if message.session_id != session_id:
        raise ValueError(f"Wrong session id: {message.session_id}")

    if message.type != MessageType.TURN:
        raise ValueError(f"Expected TURN message, got {message.type}")

    if message.from_role != expected_sender:
        raise ValueError(f"Expected sender {expected_sender}, got {message.from_role}")

    if message.to_role != AgentRole.PARENT:
        raise ValueError(f"Child messages must go to parent, got {message.to_role}")

    if message.payload.ping_number != ping:
        raise ValueError(
            f"Wrong ping number: expected {ping}, got {message.payload.ping_number}"
        )

    return message


def _make_relay(message: DebateMessage, target: AgentRole) -> DebateMessage:
    return message.model_copy(
        update={
            "type": MessageType.RELAY,
            "from_role": AgentRole.PARENT,
            "to_role": target,
        }
    )


def _parent_worker(
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

    parent = _make_parent_agent(config, session_id)

    _event(event_queue, "PARENT PROCESS: started", kind="process")

    try:
        command = command_queue.get()
        if command.get("type") != "START":
            raise RuntimeError("Parent expected START command")

        pings = config.debate.pings_per_side
        timeout = float(config.debate.request_timeout_seconds)

        _event(event_queue, "=" * 72)
        _event(event_queue, f"SESSION: {session_id}")
        _event(event_queue, f"TOPIC: {config.debate.topic}")
        _event(event_queue, f"PRO: {config.debate.pro_side}")
        _event(event_queue, f"CON: {config.debate.con_side}")
        _event(event_queue, f"PINGS PER SIDE: {pings}")
        _event(event_queue, f"TIMEOUT PER LLM CALL: {timeout:.0f} seconds")
        _event(event_queue, "=" * 72)

        last_pro: str | None = None
        last_con: str | None = None

        for ping in range(1, pings + 1):
            _event(event_queue, "")
            _event(event_queue, f"PING {ping}/{pings} — PARENT asks PRO to argue")

            parent_to_pro.put(
                {
                    "type": "TURN_REQUEST",
                    "ping": ping,
                    "opponent_text": last_con,
                }
            )

            raw_pro = _queue_get_or_timeout(pro_to_parent, timeout, "PRO response")
            pro_msg = _validate_child_message(
                raw_pro,
                expected_sender=AgentRole.PRO,
                session_id=session_id,
                ping=ping,
            )

            parent.record_turn(pro_msg)
            last_pro = pro_msg.payload.text

            _event(event_queue, f"PRO says: {_short_text(last_pro)}")
            if pro_msg.payload.citations:
                _event(
                    event_queue,
                    "PRO sources: "
                    + ", ".join(c.url for c in pro_msg.payload.citations),
                )

            _event(event_queue, "PARENT: received PRO argument and relays it to CON.")

            pro_relay = _make_relay(pro_msg, AgentRole.CON)
            parent_to_con.put(
                {
                    "type": "RELAY",
                    "message": pro_relay.model_dump(mode="json"),
                }
            )

            _event(event_queue, "")
            _event(event_queue, f"PING {ping}/{pings} — PARENT asks CON to respond")

            parent_to_con.put(
                {
                    "type": "TURN_REQUEST",
                    "ping": ping,
                    "opponent_text": last_pro,
                }
            )

            raw_con = _queue_get_or_timeout(con_to_parent, timeout, "CON response")
            con_msg = _validate_child_message(
                raw_con,
                expected_sender=AgentRole.CON,
                session_id=session_id,
                ping=ping,
            )

            parent.record_turn(con_msg)
            last_con = con_msg.payload.text

            _event(event_queue, f"CON says: {_short_text(last_con)}")
            if con_msg.payload.citations:
                _event(
                    event_queue,
                    "CON sources: "
                    + ", ".join(c.url for c in con_msg.payload.citations),
                )

            _event(event_queue, "PARENT: received CON counterargument and relays it to PRO.")

            con_relay = _make_relay(con_msg, AgentRole.PRO)
            parent_to_pro.put(
                {
                    "type": "RELAY",
                    "message": con_relay.model_dump(mode="json"),
                }
            )

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

        _event(event_queue, "")
        _event(event_queue, "PARENT/JUDGE: Debate finished. Judge is choosing a winner...")

        verdict = parent.render_verdict()

        out = config.project_root / "logs" / f"verdict_{session_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(verdict.to_json_line(), encoding="utf-8")

        winner = verdict.payload.winner.value.upper()

        _event(event_queue, "")
        _event(event_queue, "=" * 72)
        _event(event_queue, f"FINAL VERDICT: {winner} wins")
        _event(event_queue, f"PRO score: {verdict.payload.pro_score}")
        _event(event_queue, f"CON score: {verdict.payload.con_score}")
        _event(event_queue, f"Judge rationale: {verdict.payload.rationale}")
        _event(event_queue, f"Persuasion notes: {verdict.payload.persuasion_notes}")
        _event(event_queue, f"Verdict saved to: {out}")
        _event(event_queue, "=" * 72)

        event_queue.put(
            {
                "kind": "done",
                "message": str(out),
                "data": {"verdict_path": str(out)},
                "time": time.time(),
            }
        )

    except Exception as exc:
        log.exception("PARENT process failed")
        _event(
            event_queue,
            f"PARENT PROCESS ERROR: {exc}",
            kind="error",
            data={"error": str(exc)},
        )

    finally:
        parent_to_pro.put({"type": "STOP"})
        parent_to_con.put({"type": "STOP"})
        _event(event_queue, "PARENT PROCESS: stopped", kind="process")


class ProcessDebateOrchestrator:
    """Real three-process debate orchestrator.

    Processes:
    1. parent/judge process
    2. pro debater process
    3. con debater process

    Main process only supervises, logs progress, and serves the GUI/terminal.
    """

    def __init__(
        self,
        config: AppConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.config = config
        self.session_id = str(uuid.uuid4())[:8]
        self._progress_callback = progress_callback

        setup_logging(config.logging)

        self._ctx = mp.get_context("spawn")

        self._parent_commands: mp.Queue = self._ctx.Queue()
        self._events: mp.Queue = self._ctx.Queue()

        self._parent_to_pro: mp.Queue = self._ctx.Queue()
        self._pro_to_parent: mp.Queue = self._ctx.Queue()

        self._parent_to_con: mp.Queue = self._ctx.Queue()
        self._con_to_parent: mp.Queue = self._ctx.Queue()

        self._processes: dict[str, mp.Process] = {}
        self._watchdog_stop = threading.Event()
        self._watchdog_thread: threading.Thread | None = None

    def _progress(self, message: str) -> None:
        logger.info(message)
        if self._progress_callback is not None:
            self._progress_callback(message)

    def _start_processes(self) -> None:
        self._processes["pro"] = self._ctx.Process(
            name=f"debate-pro-{self.session_id}",
            target=_child_worker,
            args=(
                AgentRole.PRO.value,
                self.config,
                self.session_id,
                self._parent_to_pro,
                self._pro_to_parent,
                self._events,
            ),
        )

        self._processes["con"] = self._ctx.Process(
            name=f"debate-con-{self.session_id}",
            target=_child_worker,
            args=(
                AgentRole.CON.value,
                self.config,
                self.session_id,
                self._parent_to_con,
                self._con_to_parent,
                self._events,
            ),
        )

        self._processes["parent"] = self._ctx.Process(
            name=f"debate-parent-{self.session_id}",
            target=_parent_worker,
            args=(
                self.config,
                self.session_id,
                self._parent_commands,
                self._events,
                self._parent_to_pro,
                self._pro_to_parent,
                self._parent_to_con,
                self._con_to_parent,
            ),
        )

        for name, process in self._processes.items():
            process.start()
            self._progress(f"SUPERVISOR: started {name} process pid={process.pid}")

    def _restart_child(self, name: str) -> None:
        if name not in {"pro", "con"}:
            return

        self._progress(f"WATCHDOG: {name} process died. Restarting it...")

        old = self._processes.get(name)
        if old is not None and old.is_alive():
            old.terminate()
            old.join(timeout=3)

        if name == "pro":
            process = self._ctx.Process(
                name=f"debate-pro-{self.session_id}-restart",
                target=_child_worker,
                args=(
                    AgentRole.PRO.value,
                    self.config,
                    self.session_id,
                    self._parent_to_pro,
                    self._pro_to_parent,
                    self._events,
                ),
            )
        else:
            process = self._ctx.Process(
                name=f"debate-con-{self.session_id}-restart",
                target=_child_worker,
                args=(
                    AgentRole.CON.value,
                    self.config,
                    self.session_id,
                    self._parent_to_con,
                    self._con_to_parent,
                    self._events,
                ),
            )

        process.start()
        self._processes[name] = process
        self._progress(f"WATCHDOG: restarted {name} process pid={process.pid}")

    def _watchdog_loop(self) -> None:
        interval = max(2, self.config.debate.keepalive_interval_seconds)

        while not self._watchdog_stop.wait(interval):
            parent = self._processes.get("parent")
            if parent is not None and not parent.is_alive():
                self._progress("WATCHDOG: parent process died. Debate cannot continue safely.")
                return

            for name in ("pro", "con"):
                process = self._processes.get(name)
                if process is not None and not process.is_alive():
                    self._restart_child(name)

    def start_watchdogs(self) -> None:
        self._watchdog_stop.clear()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
            name=f"debate-watchdog-{self.session_id}",
        )
        self._watchdog_thread.start()
        self._progress("WATCHDOG: process watchdog started")

    def stop_watchdogs(self) -> None:
        self._watchdog_stop.set()
        if self._watchdog_thread is not None:
            self._watchdog_thread.join(timeout=3)
        self._progress("WATCHDOG: process watchdog stopped")

    def _stop_processes(self) -> None:
        for q in (self._parent_to_pro, self._parent_to_con):
            try:
                q.put({"type": "STOP"})
            except Exception:
                pass

        for name, process in self._processes.items():
            if process.is_alive():
                process.join(timeout=3)

            if process.is_alive():
                self._progress(f"SUPERVISOR: terminating {name} process")
                process.terminate()
                process.join(timeout=3)

    def run(self) -> Path:
        self._start_processes()

        self._parent_commands.put({"type": "START"})

        verdict_path: Path | None = None
        deadline = time.time() + (
            self.config.debate.request_timeout_seconds
            * max(3, self.config.debate.pings_per_side * 3)
        )

        try:
            while True:
                if time.time() > deadline:
                    raise TimeoutError("Debate global timeout reached")

                try:
                    event = self._events.get(timeout=0.5)
                except queue.Empty:
                    parent = self._processes.get("parent")
                    if parent is not None and not parent.is_alive():
                        raise RuntimeError("Parent process stopped before producing verdict")
                    continue

                kind = event.get("kind")
                message = str(event.get("message", ""))

                if kind == "error":
                    self._progress(message)
                    raise RuntimeError(message)

                if kind == "done":
                    verdict_path = Path(event["data"]["verdict_path"])
                    self._progress(f"SUPERVISOR: debate done, verdict={verdict_path}")
                    break

                self._progress(message)

            if verdict_path is None:
                raise RuntimeError("Debate finished without verdict path")

            return verdict_path

        finally:
            self._stop_processes()