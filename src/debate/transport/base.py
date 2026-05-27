from __future__ import annotations

from abc import ABC, abstractmethod

from debate.models import DebateMessage


class MessageTransport(ABC):
    """Abstract IPC channel that carries one `DebateMessage` at a time."""

    @abstractmethod
    def write(self, message: DebateMessage) -> None: ...

    @abstractmethod
    def read(self, timeout: float | None = None) -> DebateMessage | None: ...

    @abstractmethod
    def close(self) -> None: ...


class ChannelPair:
    """Bidirectional channels between parent and one child."""

    def __init__(
        self,
        child_to_parent: MessageTransport,
        parent_to_child: MessageTransport,
    ) -> None:
        self.child_to_parent = child_to_parent
        self.parent_to_child = parent_to_child

    def close(self) -> None:
        self.child_to_parent.close()
        self.parent_to_child.close()
