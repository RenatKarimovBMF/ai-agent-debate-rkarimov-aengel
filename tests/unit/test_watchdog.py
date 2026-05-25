from __future__ import annotations

import threading

from debate.watchdog import Watchdog


def test_watchdog_calls_restart_when_not_alive():
    restarted = threading.Event()

    def restart() -> None:
        restarted.set()

    wd = Watchdog(0.05, is_alive=lambda: False, restart=restart)
    wd.start()
    restarted.wait(timeout=1)
    wd.stop()
    assert restarted.is_set()


def test_watchdog_stop_without_restart():
    wd = Watchdog(0.05, is_alive=lambda: True, restart=lambda: None)
    wd.start()
    wd.stop()
