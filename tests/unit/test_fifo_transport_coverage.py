"""Cover ``transport/fifo.py`` on any platform by faking the os FIFO calls.

The real ``os.mkfifo`` only exists on Unix, so it is monkeypatched to
``touch`` a regular file and ``O_NONBLOCK`` is neutralised. The transport
logic (open/write/read/select/close) then runs against a real temp file
in-process, with no Unix-only syscalls actually executed.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from debate.transport.fifo import FifoTransport, _fifo_supported

from ._coverage_helpers import make_message


@pytest.fixture
def fake_fifo(monkeypatch):
    monkeypatch.setattr(os, "O_NONBLOCK", 0, raising=False)
    monkeypatch.setattr(os, "mkfifo", lambda p: Path(p).touch(), raising=False)


def test_fifo_supported_branches(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    assert _fifo_supported() is False

    monkeypatch.setattr(os, "name", "posix")
    monkeypatch.setattr(os, "mkfifo", lambda p: None, raising=False)
    assert _fifo_supported() is True

    monkeypatch.delattr(os, "mkfifo", raising=False)
    assert _fifo_supported() is False


def test_init_creates_then_reuses_path(fake_fifo, tmp_path):
    path = tmp_path / "pipe"
    FifoTransport(path)
    assert path.exists()
    FifoTransport(path)  # already exists -> skips mkfifo branch


def test_write_read_roundtrip_and_close(fake_fifo, tmp_path):
    transport = FifoTransport(tmp_path / "pipe")
    message = make_message()
    transport.write(message)

    got = transport.read(timeout=None)
    assert got is not None
    assert got.session_id == message.session_id
    transport.close()

    FifoTransport(tmp_path / "fresh").close()  # no fds opened -> None branch


def test_read_empty_returns_none(fake_fifo, tmp_path):
    transport = FifoTransport(tmp_path / "pipe")
    assert transport.read(timeout=None) is None


def test_read_select_ready_and_timeout(fake_fifo, tmp_path, monkeypatch):
    ready = FifoTransport(tmp_path / "ready")
    ready.write(make_message())
    monkeypatch.setattr("select.select", lambda r, w, x, t: (r, [], []))
    assert ready.read(timeout=0.5) is not None

    idle = FifoTransport(tmp_path / "idle")
    monkeypatch.setattr("select.select", lambda r, w, x, t: ([], [], []))
    assert idle.read(timeout=0.5) is None


def test_read_blocking_error_returns_none(fake_fifo, tmp_path, monkeypatch):
    transport = FifoTransport(tmp_path / "pipe")

    def _raise(*_a, **_k):
        raise BlockingIOError

    monkeypatch.setattr(os, "read", _raise)
    assert transport.read(timeout=None) is None
