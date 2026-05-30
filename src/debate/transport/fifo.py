from __future__ import annotations

import os
from pathlib import Path

from debate.models import DebateMessage
from debate.transport.base import MessageTransport


def _fifo_supported() -> bool:
    return os.name != "nt" and hasattr(os, "mkfifo")


class FifoTransport(MessageTransport):
    """Unix FIFO transport for real separate-process experiments."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            os.mkfifo(self._path)  # type: ignore[attr-defined]  # POSIX-only

        self._read_fd: int | None = None
        self._write_fd: int | None = None

    def _ensure_write(self) -> None:
        if self._write_fd is None:
            flags = os.O_WRONLY | os.O_NONBLOCK  # type: ignore[attr-defined]  # POSIX-only
            self._write_fd = os.open(self._path, flags)

    def _ensure_read(self) -> None:
        if self._read_fd is None:
            flags = os.O_RDONLY | os.O_NONBLOCK  # type: ignore[attr-defined]  # POSIX-only
            self._read_fd = os.open(self._path, flags)

    def write(self, message: DebateMessage) -> None:
        self._ensure_write()
        data = message.to_json_line().encode("utf-8")
        os.write(self._write_fd, data)  # type: ignore[arg-type]

    def read(self, timeout: float | None = None) -> DebateMessage | None:
        self._ensure_read()

        if timeout:
            import select

            ready, _, _ = select.select([self._read_fd], [], [], timeout)
            if not ready:
                return None

        try:
            chunk = os.read(self._read_fd, 65536)  # type: ignore[arg-type]
        except BlockingIOError:
            return None

        if not chunk:
            return None

        return DebateMessage.from_json_line(chunk.decode("utf-8"))

    def close(self) -> None:
        for fd in (self._read_fd, self._write_fd):
            if fd is not None:
                os.close(fd)
