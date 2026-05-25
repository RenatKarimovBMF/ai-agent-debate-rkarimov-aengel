from __future__ import annotations

import multiprocessing as mp
import queue
import time
from typing import Any


def short_text(text: str, limit: int = 700) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[:limit].rstrip() + "..."


def emit_event(
    event_queue: mp.Queue,
    message: str,
    *,
    kind: str = "progress",
    data: dict[str, Any] | None = None,
) -> None:
    event_queue.put(
        {
            "kind": kind,
            "message": message,
            "data": data or {},
            "time": time.time(),
        }
    )


def queue_get_or_timeout(q: mp.Queue, timeout: float, label: str) -> Any:
    try:
        return q.get(timeout=timeout)
    except queue.Empty as exc:
        raise TimeoutError(f"Timeout while waiting for {label}") from exc
