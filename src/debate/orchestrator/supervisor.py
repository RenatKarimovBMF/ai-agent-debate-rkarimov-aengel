from __future__ import annotations

import logging
import multiprocessing as mp
import queue
import time
import uuid
from pathlib import Path

from debate.config import AppConfig
from debate.logging_setup import setup_logging
from debate.orchestrator.process_pool import DebateProcessPool
from debate.orchestrator.supervisor_watchdog import ProcessSupervisorWatchdog
from debate.orchestrator.types import ProgressCallback

logger = logging.getLogger("debate.orchestrator.supervisor")


class ProcessDebateOrchestrator:
    """Supervisor for parent, pro, and con worker processes."""

    def __init__(
        self,
        config: AppConfig,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        self.config = config
        self.session_id = str(uuid.uuid4())[:8]
        self._progress_callback = progress_callback

        setup_logging(config.logging)

        ctx = mp.get_context("spawn")
        self._pool = DebateProcessPool(ctx, config, self.session_id)
        self._watchdog = ProcessSupervisorWatchdog(
            self._pool,
            config.debate.keepalive_interval_seconds,
            self._progress,
        )

    def _progress(self, message: str) -> None:
        logger.info(message)
        if self._progress_callback is not None:
            self._progress_callback(message)

    def start_watchdogs(self) -> None:
        self._watchdog.start()

    def stop_watchdogs(self) -> None:
        self._watchdog.stop()

    def run(self) -> Path:
        self._pool.start_all(
            on_started=lambda name, pid: self._progress(
                f"SUPERVISOR: started {name} process pid={pid}"
            )
        )

        self._pool.parent_commands.put({"type": "START"})

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
                    event = self._pool.events.get(timeout=0.5)
                except queue.Empty:
                    parent = self._pool.processes.get("parent")
                    if parent is not None and not parent.is_alive():
                        raise RuntimeError(
                            "Parent process stopped before producing verdict"
                        ) from None
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
            self._pool.stop_all(
                on_terminate=lambda name: self._progress(
                    f"SUPERVISOR: terminating {name} process"
                )
            )
