from __future__ import annotations

import threading
from collections.abc import Callable

from debate.orchestrator.process_pool import DebateProcessPool


class ProcessSupervisorWatchdog:
    def __init__(
        self,
        pool: DebateProcessPool,
        interval_seconds: int,
        on_message: Callable[[str], None],
    ) -> None:
        self._pool = pool
        self._interval = max(2, interval_seconds)
        self._on_message = on_message
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name="debate-process-watchdog",
        )
        self._thread.start()
        self._on_message("WATCHDOG: process watchdog started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
        self._on_message("WATCHDOG: process watchdog stopped")

    def _loop(self) -> None:
        while not self._stop.wait(self._interval):
            parent = self._pool.processes.get("parent")
            if parent is not None and not parent.is_alive():
                self._on_message("WATCHDOG: parent process died. Debate cannot continue safely.")
                return

            for name in ("pro", "con"):
                process = self._pool.processes.get(name)
                if process is not None and not process.is_alive():
                    self._on_message(f"WATCHDOG: {name} process died. Restarting it...")
                    self._pool.restart_child(
                        name,
                        on_started=lambda n, pid: self._on_message(
                            f"WATCHDOG: restarted {n} process pid={pid}"
                        ),
                    )
