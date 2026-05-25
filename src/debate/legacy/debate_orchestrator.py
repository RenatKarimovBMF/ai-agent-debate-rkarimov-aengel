from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from debate.config import AppConfig
from debate.gatekeeper import Gatekeeper
from debate.legacy.session_loop import run_debate_session
from debate.legacy.setup import build_legacy_agents, clear_ipc_queues
from debate.logging_setup import setup_logging
from debate.watchdog import Watchdog
from sdk.llm_client import LlmClient

logger = logging.getLogger("debate.legacy.orchestrator")

ProgressCallback = Callable[[str], None]


class DebateOrchestrator:
    """Single-process orchestrator using file-queue IPC (legacy reference path)."""

    def __init__(
        self,
        config: AppConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.config = config
        self.session_id = str(uuid.uuid4())[:8]
        self._progress_callback = progress_callback

        setup_logging(config.logging)

        gatekeeper = Gatekeeper(config.gatekeeper)
        client = LlmClient(
            cli_command=config.agents.cli_command,
            workdir=config.project_root / config.agents.workdir,
            timeout_seconds=config.debate.request_timeout_seconds,
            gemini_model=config.llm.gemini_model,
            gemini_fallback_models=config.llm.gemini_model_fallbacks,
            use_google_search=config.llm.use_google_search,
        )

        provider = client.active_provider()
        logger.info("LLM provider: %s", provider, extra={"extra_data": {"provider": provider}})

        self._agents = build_legacy_agents(config, self.session_id, gatekeeper, client)
        self._last_heartbeat = time.monotonic()
        self._watchdogs: list[Watchdog] = []

    def _progress(self, message: str) -> None:
        logger.info(message)
        if self._progress_callback is not None:
            self._progress_callback(message)

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
        clear_ipc_queues(self.config)
        return run_debate_session(
            self.config,
            self.session_id,
            self._agents,
            self._progress,
            self._heartbeat,
        )

    def start_watchdogs(self) -> None:
        interval = self.config.debate.keepalive_interval_seconds
        self._watchdogs = [Watchdog(interval, self._is_alive, self._watchdog_restart)]
        for watchdog in self._watchdogs:
            watchdog.start()

    def stop_watchdogs(self) -> None:
        for watchdog in self._watchdogs:
            watchdog.stop()

        self._agents.pro_channels.close()
        self._agents.con_channels.close()
