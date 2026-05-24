from __future__ import annotations

import logging
import threading
import time
from typing import Callable

logger = logging.getLogger("debate.watchdog")


class Watchdog:
    """Keep-alive monitor; restarts dead agent workers (Exercise 02 §8.6)."""

    def __init__(
        self,
        interval_seconds: float,
        is_alive: Callable[[], bool],
        restart: Callable[[], None],
    ) -> None:
        self._interval = interval_seconds
        self._is_alive = is_alive
        self._restart = restart
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        while not self._stop.wait(self._interval):
            if self._is_alive():
                continue
            logger.warning("Watchdog: agent process not alive, restarting")
            try:
                self._restart()
            except Exception:
                logger.exception("Watchdog restart failed")
