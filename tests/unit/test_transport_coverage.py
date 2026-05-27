"""Targeted branch coverage for `debate.transport.factory` and
`debate.transport.file_queue` (the supported transport variants).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from debate.config import load_config
from debate.transport import (
    FileQueueTransport,
    build_channels,
    create_transport,
)
from debate.transport.factory import create_transport as factory_create_transport

from ._coverage_helpers import MagicMock, make_message


def test_transport_factory_unknown_role(tmp_path):
    cfg = load_config()
    with pytest.raises(ValueError, match="Unknown role for channel pair"):
        build_channels(cfg.ipc, "judge", tmp_path)


def test_transport_factory_unknown_type(tmp_path):
    cfg = load_config()
    bad = replace(cfg.ipc, transport_type="space-pigeons")
    with pytest.raises(ValueError, match="Unknown ipc.transport_type"):
        factory_create_transport(bad, "x.queue", tmp_path)


def test_transport_factory_fifo_on_windows_raises(tmp_path, monkeypatch):
    cfg = load_config()
    monkeypatch.setattr("debate.transport.factory._fifo_supported", lambda: False)
    bad = replace(cfg.ipc, transport_type="fifo")
    with pytest.raises(RuntimeError, match="FIFO transport requested"):
        factory_create_transport(bad, "x.fifo", tmp_path)


def test_transport_factory_fifo_when_supported_returns_fifo_transport(tmp_path, monkeypatch):
    cfg = load_config()
    monkeypatch.setattr("debate.transport.factory._fifo_supported", lambda: True)
    fake = MagicMock()
    monkeypatch.setattr("debate.transport.factory.FifoTransport", lambda path: fake)
    cfg_fifo = replace(cfg.ipc, transport_type="fifo")

    result = factory_create_transport(cfg_fifo, "x.fifo", tmp_path)
    assert result is fake


def test_file_queue_transport_returns_none_when_timeout_is_none(tmp_path):
    transport = FileQueueTransport(tmp_path / "empty.queue")
    assert transport.read(timeout=None) is None


def test_file_queue_transport_waits_for_message(tmp_path):
    """Exercises the sleep branch in `FileQueueTransport.read`."""
    path = tmp_path / "slow.queue"
    transport = FileQueueTransport(path)
    msg = make_message()

    import threading
    import time as _time

    def writer():
        _time.sleep(0.25)
        transport.write(msg)

    t = threading.Thread(target=writer)
    t.start()
    try:
        result = transport.read(timeout=2.0)
    finally:
        t.join()

    assert result is not None
    assert result.payload.text == "hi"


def test_create_transport_via_public_re_export(tmp_path):
    cfg = load_config()
    t = create_transport(cfg.ipc, "x.queue", tmp_path)
    t.close()
