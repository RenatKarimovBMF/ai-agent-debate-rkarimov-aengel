from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from debate.agents import ConAgent, ParentAgent, ProAgent
from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.logging_setup import setup_logging
from debate.models import AgentRole, DebateMessage, MessageType
from debate.transport import build_channels
from debate.watchdog import Watchdog
from sdk.llm_client import LlmClient

logger = logging.getLogger("debate.orchestrator")

ProgressCallback = Callable[[str], None]


class DebateOrchestrator:
    """
    Python orchestrator for three logical agents.

    The child agents never exchange data directly.
    Every turn goes:

        child -> parent -> other child

    The optional progress_callback is used by the GUI to show live debate flow.
    Terminal users still see the same flow through normal logging.
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

        self.gatekeeper = Gatekeeper(config.gatekeeper)
        self.client = LlmClient(
            cli_command=config.agents.cli_command,
            workdir=config.project_root / config.agents.workdir,
            timeout_seconds=config.debate.request_timeout_seconds,
            gemini_model=config.llm.gemini_model,
            gemini_fallback_models=config.llm.gemini_model_fallbacks,
            use_google_search=config.llm.use_google_search,
        )

        logger.info(
            "LLM provider: %s",
            self.client.active_provider(),
            extra={"extra_data": {"provider": self.client.active_provider()}},
        )

        root = config.project_root
        self._pro_channels = build_channels(config.ipc, "pro", root)
        self._con_channels = build_channels(config.ipc, "con", root)

        self.parent = ParentAgent(
            config,
            self.gatekeeper,
            self.client,
            self.session_id,
            self._pro_channels,
            self._con_channels,
        )

        self.pro = ProAgent(
            AgentRole.PRO,
            config,
            self._pro_channels,
            self.gatekeeper,
            self.client,
            self.session_id,
        )

        self.con = ConAgent(
            AgentRole.CON,
            config,
            self._con_channels,
            self.gatekeeper,
            self.client,
            self.session_id,
        )

        self._last_heartbeat = time.monotonic()
        self._watchdogs: list[Watchdog] = []

    def _progress(self, message: str) -> None:
        logger.info(message)
        if self._progress_callback is not None:
            self._progress_callback(message)

    def _short_text(self, text: str, limit: int = 700) -> str:
        clean = " ".join(text.split())
        if len(clean) <= limit:
            return clean
        return clean[:limit].rstrip() + "..."

    def _clear_queues(self) -> None:
        fifo_dir = self.config.project_root / self.config.ipc.fifo_dir
        fifo_dir.mkdir(parents=True, exist_ok=True)

        for path in fifo_dir.glob("*"):
            if path.is_file() and path.name != ".gitkeep":
                path.unlink(missing_ok=True)

    def _heartbeat(self) -> None:
        self._last_heartbeat = time.monotonic()

    def _is_alive(self) -> bool:
        max_gap = max(10, self.config.debate.request_timeout_seconds * 2)
        return (time.monotonic() - self._last_heartbeat) < max_gap

    def _watchdog_restart(self) -> None:
        message = "WATCHDOG: Debate seems stalled. Check LLM/API/network."
        logger.error(message, extra={"extra_data": {"session": self.session_id}})
        if self._progress_callback is not None:
            self._progress_callback(message)

    def run(self) -> Path:
        self._clear_queues()

        pings = self.config.debate.pings_per_side
        timeout = float(self.config.debate.request_timeout_seconds)

        self._progress("=" * 72)
        self._progress(f"SESSION: {self.session_id}")
        self._progress(f"TOPIC: {self.config.debate.topic}")
        self._progress(f"PRO: {self.config.debate.pro_side}")
        self._progress(f"CON: {self.config.debate.con_side}")
        self._progress(f"PINGS PER SIDE: {pings}")
        self._progress(f"TIMEOUT PER LLM CALL: {timeout:.0f} seconds")
        self._progress("=" * 72)

        last_pro: str | None = None
        last_con: str | None = None

        for ping in range(1, pings + 1):
            self._heartbeat()

            self._progress("")
            self._progress(f"PING {ping}/{pings} — PRO is thinking...")
            pro_msg = self.pro.build_turn(ping, last_con)
            self.pro.send(pro_msg)

            received_pro = self.parent.receive_from_child(AgentRole.PRO, timeout=timeout)
            received_pro = self._require_message(received_pro, AgentRole.PRO, ping)

            self.parent.record_turn(received_pro)

            pro_text = received_pro.payload.text
            pro_sources = [citation.url for citation in received_pro.payload.citations]

            self._progress(f"PRO says: {self._short_text(pro_text)}")
            if pro_sources:
                self._progress(f"PRO sources: {', '.join(pro_sources)}")

            self._progress("PARENT: received PRO argument and relays it to CON.")
            self.parent.relay_to_child(received_pro, AgentRole.CON)

            relayed_to_con = self.con.receive(timeout=timeout)
            last_pro = self._require_message(relayed_to_con, AgentRole.PRO, ping).payload.text

            self._heartbeat()

            self._progress("")
            self._progress(f"PING {ping}/{pings} — CON is thinking...")
            con_msg = self.con.build_turn(ping, last_pro)
            self.con.send(con_msg)

            received_con = self.parent.receive_from_child(AgentRole.CON, timeout=timeout)
            received_con = self._require_message(received_con, AgentRole.CON, ping)

            self.parent.record_turn(received_con)

            con_text = received_con.payload.text
            con_sources = [citation.url for citation in received_con.payload.citations]

            self._progress(f"CON says: {self._short_text(con_text)}")
            if con_sources:
                self._progress(f"CON sources: {', '.join(con_sources)}")

            self._progress("PARENT: received CON counterargument and relays it to PRO.")
            self.parent.relay_to_child(received_con, AgentRole.PRO)

            relayed_to_pro = self.pro.receive(timeout=timeout)
            last_con = self._require_message(relayed_to_pro, AgentRole.CON, ping).payload.text

            logger.info(
                "Ping complete",
                extra={
                    "extra_data": {
                        "ping": ping,
                        "pro_words": len(last_pro.split()),
                        "con_words": len(last_con.split()),
                    }
                },
            )

        self._heartbeat()

        self._progress("")
        self._progress("PARENT/JUDGE: Debate finished. Judge is choosing a winner...")
        verdict = self.parent.render_verdict()

        out = self.config.project_root / "logs" / f"verdict_{self.session_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(verdict.to_json_line(), encoding="utf-8")

        winner = verdict.payload.winner.value.upper()
        self._progress("")
        self._progress("=" * 72)
        self._progress(f"FINAL VERDICT: {winner} wins")
        self._progress(f"PRO score: {verdict.payload.pro_score}")
        self._progress(f"CON score: {verdict.payload.con_score}")
        self._progress(f"Judge rationale: {verdict.payload.rationale}")
        self._progress(f"Persuasion notes: {verdict.payload.persuasion_notes}")
        self._progress(f"Verdict saved to: {out}")
        self._progress("=" * 72)

        logger.info("Verdict", extra={"extra_data": verdict.model_dump()})
        return out

    def _require_message(
        self,
        message: DebateMessage | None,
        expected_original_sender: AgentRole,
        ping: int,
    ) -> DebateMessage:
        if message is None:
            raise TimeoutError(
                f"No message received for {expected_original_sender.value} ping {ping}"
            )

        if message.session_id != self.session_id:
            raise ValueError(f"Wrong session id in message: {message.session_id}")

        if message.payload.ping_number != ping:
            raise ValueError(
                f"Wrong ping number: expected {ping}, got {message.payload.ping_number}"
            )

        if message.type not in {MessageType.TURN, MessageType.RELAY}:
            raise ValueError(f"Unexpected message type: {message.type}")

        if message.type == MessageType.TURN and message.from_role != expected_original_sender:
            raise ValueError(f"Unexpected sender: {message.from_role}")

        if message.type == MessageType.RELAY and message.to_role not in {
            AgentRole.PRO,
            AgentRole.CON,
        }:
            raise ValueError(f"Bad relay target: {message.to_role}")

        return message

    def start_watchdogs(self) -> None:
        interval = self.config.debate.keepalive_interval_seconds
        self._watchdogs = [
            Watchdog(interval, self._is_alive, self._watchdog_restart),
        ]

        for watchdog in self._watchdogs:
            watchdog.start()

    def stop_watchdogs(self) -> None:
        for watchdog in self._watchdogs:
            watchdog.stop()

        self._pro_channels.close()
        self._con_channels.close()