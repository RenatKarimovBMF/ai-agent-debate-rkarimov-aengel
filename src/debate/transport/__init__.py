"""IPC transport layer for the debate orchestrator.

Re-exports the public surface so existing call sites stay valid:
`from debate.transport import ChannelPair, FileQueueTransport, ...`.
"""

from debate.transport.base import ChannelPair, MessageTransport
from debate.transport.factory import build_channels, create_transport
from debate.transport.fifo import FifoTransport
from debate.transport.file_queue import FileQueueTransport

__all__ = [
    "ChannelPair",
    "MessageTransport",
    "FileQueueTransport",
    "FifoTransport",
    "build_channels",
    "create_transport",
]
