from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from debate.config import load_config, with_custom_debate
from debate.env_loader import ensure_env_loaded
from debate.orchestrator import ProcessDebateOrchestrator

OnDone = Callable[[Path | None, Exception | None], None]


def run_debate(
    pro: str,
    con: str,
    topic: str,
    queue_log: Callable[[str], None],
    on_done: OnDone,
    cancel_event: threading.Event | None = None,
) -> None:
    """Run one debate to completion, reporting via ``on_done``.

    Kept as a plain function (no thread) so it is unit-testable synchronously;
    ``start_debate_thread`` runs it on a daemon thread for the GUI.
    """
    try:
        ensure_env_loaded()
        base = load_config()
        config = with_custom_debate(base, pro_side=pro, con_side=con, topic=topic)

        orch = ProcessDebateOrchestrator(
            config, progress_callback=queue_log, cancel_event=cancel_event
        )
        orch.start_watchdogs()
        try:
            on_done(orch.run(), None)
        finally:
            orch.stop_watchdogs()
    except Exception as exc:
        on_done(None, exc)


def start_debate_thread(
    *,
    pro: str,
    con: str,
    topic: str,
    queue_log: Callable[[str], None],
    on_done: OnDone,
    cancel_event: threading.Event | None = None,
) -> threading.Thread:
    """Run a debate on a daemon thread; returns the thread for clean shutdown."""
    thread = threading.Thread(
        target=run_debate,
        args=(pro, con, topic, queue_log, on_done, cancel_event),
        daemon=True,
    )
    thread.start()
    return thread
