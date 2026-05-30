from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from debate.config import load_config, with_custom_debate
from debate.env_loader import ensure_env_loaded
from debate.orchestrator import ProcessDebateOrchestrator


def start_debate_thread(
    *,
    pro: str,
    con: str,
    topic: str,
    queue_log: Callable[[str], None],
    on_done: Callable[[Path | None, Exception | None], None],
    cancel_event: threading.Event | None = None,
) -> threading.Thread:
    """Run a debate on a daemon thread. Returns the thread so callers/tests
    can join it for clean shutdown."""

    def worker() -> None:
        try:
            ensure_env_loaded()
            base = load_config()
            config = with_custom_debate(base, pro_side=pro, con_side=con, topic=topic)

            orch = ProcessDebateOrchestrator(
                config, progress_callback=queue_log, cancel_event=cancel_event
            )
            orch.start_watchdogs()

            try:
                path = orch.run()
                on_done(path, None)
            finally:
                orch.stop_watchdogs()

        except Exception as exc:
            on_done(None, exc)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread
