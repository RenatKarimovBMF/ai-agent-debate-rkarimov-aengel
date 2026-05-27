"""Targeted branch coverage for `debate.orchestrator.events`.

Covers the `short_text` truncation helper, the kind/data defaults in
`emit_event`, and both branches of `queue_get_or_timeout`.
"""

from __future__ import annotations

import pytest

from debate.orchestrator.events import (
    emit_event,
    queue_get_or_timeout,
)
from debate.orchestrator.events import (
    short_text as events_short_text,
)

from ._coverage_helpers import MagicMock


def test_events_short_text_keeps_short_input():
    assert events_short_text("ok") == "ok"


def test_events_short_text_truncates_long_input():
    truncated = events_short_text("a " * 1000, limit=10)
    assert truncated.endswith("...")


def test_emit_event_records_kind_and_data():
    fake_queue = MagicMock()
    emit_event(fake_queue, "hello", kind="ipc", data={"k": 1})
    payload = fake_queue.put.call_args[0][0]
    assert payload["kind"] == "ipc"
    assert payload["data"] == {"k": 1}
    assert payload["message"] == "hello"


def test_emit_event_default_kind_and_data():
    fake_queue = MagicMock()
    emit_event(fake_queue, "go")
    payload = fake_queue.put.call_args[0][0]
    assert payload["kind"] == "progress"
    assert payload["data"] == {}


def test_queue_get_or_timeout_raises_on_empty():
    import queue as std_queue

    real_queue = MagicMock()
    real_queue.get.side_effect = std_queue.Empty()
    with pytest.raises(TimeoutError, match="Timeout while waiting for label"):
        queue_get_or_timeout(real_queue, timeout=0.01, label="label")


def test_queue_get_or_timeout_returns_value():
    real_queue = MagicMock()
    real_queue.get.return_value = "value"
    assert queue_get_or_timeout(real_queue, timeout=0.01, label="l") == "value"
