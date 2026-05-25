from __future__ import annotations

from pathlib import Path

import pytest

from debate.config import load_config
from debate.models import AgentRole, DebateMessage, DebatePayload, MessageType
from debate.transport import (
    ChannelPair,
    FileQueueTransport,
    build_channels,
    create_transport,
)


def _sample_message(session: str = "s1") -> DebateMessage:
    return DebateMessage(
        type=MessageType.TURN,
        from_role=AgentRole.PRO,
        to_role=AgentRole.PARENT,
        session_id=session,
        turn_id=1,
        payload=DebatePayload(text="hi", ping_number=1),
    )


def test_file_queue_transport_roundtrip(tmp_path: Path):
    path = tmp_path / "q.queue"
    transport = FileQueueTransport(path)
    transport.write(_sample_message())
    read = transport.read(timeout=1.0)
    assert read is not None
    assert read.payload.text == "hi"
    transport.close()


def test_file_queue_read_timeout(tmp_path: Path):
    transport = FileQueueTransport(tmp_path / "empty.queue")
    assert transport.read(timeout=0.2) is None


def test_build_channels_for_pro_and_con(tmp_path: Path):
    from dataclasses import replace

    config = replace(load_config(), project_root=tmp_path)

    pro = build_channels(config.ipc, "pro", tmp_path)
    con = build_channels(config.ipc, "con", tmp_path)
    assert isinstance(pro, ChannelPair)
    assert isinstance(con, ChannelPair)
    pro.close()
    con.close()


def test_create_transport_unknown_type():
    from dataclasses import replace

    config = load_config()
    bad = replace(config.ipc, transport_type="unknown")
    with pytest.raises(ValueError, match="Unknown ipc.transport_type"):
        create_transport(bad, "x.queue", Path("."))
