from __future__ import annotations

from collections.abc import Callable

ProgressCallback = Callable[[str], None]


class DebateCancelled(Exception):
    """Raised when a debate is stopped by the user before a verdict is produced."""
