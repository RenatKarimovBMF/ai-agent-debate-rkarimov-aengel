from __future__ import annotations

from pathlib import Path

from debate.config import IpcConfig
from debate.transport.base import ChannelPair, MessageTransport
from debate.transport.fifo import FifoTransport, _fifo_supported
from debate.transport.file_queue import FileQueueTransport


def create_transport(
    ipc: IpcConfig,
    channel_name: str,
    project_root: Path,
) -> MessageTransport:
    path = project_root / ipc.fifo_dir / channel_name
    transport_type = ipc.transport_type.lower().strip()

    if transport_type == "fifo":
        if not _fifo_supported():
            raise RuntimeError("FIFO transport requested, but this OS does not support os.mkfifo")
        return FifoTransport(path)

    if transport_type == "file_queue":
        return FileQueueTransport(path.with_suffix(".queue"))

    raise ValueError(f"Unknown ipc.transport_type: {ipc.transport_type!r}")


def build_channels(ipc: IpcConfig, role: str, project_root: Path) -> ChannelPair:
    if role == "pro":
        return ChannelPair(
            create_transport(ipc, ipc.pro_to_parent, project_root),
            create_transport(ipc, ipc.parent_to_pro, project_root),
        )

    if role == "con":
        return ChannelPair(
            create_transport(ipc, ipc.con_to_parent, project_root),
            create_transport(ipc, ipc.parent_to_con, project_root),
        )

    raise ValueError(f"Unknown role for channel pair: {role}")
