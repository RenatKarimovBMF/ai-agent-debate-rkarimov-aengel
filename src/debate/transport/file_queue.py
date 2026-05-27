from __future__ import annotations

import threading
import time
from pathlib import Path

from debate.models import DebateMessage
from debate.transport.base import MessageTransport


class FileQueueTransport(MessageTransport):
    """Cross-platform JSONL queue.

    This behaves like an IPC channel for the exercise, but avoids the
    Unix FIFO blocking semantics when the grader runs everything from
    one Python orchestrator process.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()
        self._lock = threading.Lock()
        self._offset = 0

    def write(self, message: DebateMessage) -> None:
        with self._lock:
            with self._path.open("a", encoding="utf-8") as f:
                f.write(message.to_json_line())

    def read(self, timeout: float | None = None) -> DebateMessage | None:
        deadline = time.time() + timeout if timeout else None

        while True:
            with self._lock:
                lines = self._path.read_text(encoding="utf-8").splitlines()

            if self._offset < len(lines):
                line = lines[self._offset]
                self._offset += 1
                return DebateMessage.from_json_line(line)

            if deadline and time.time() >= deadline:
                return None

            if timeout is None:
                return None

            time.sleep(0.2)

    def close(self) -> None:
        pass
