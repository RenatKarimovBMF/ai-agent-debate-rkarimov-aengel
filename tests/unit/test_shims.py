"""Cover the thin backward-compatible re-export shims."""

from __future__ import annotations


def test_process_orchestrator_shim_reexports():
    import debate.process_orchestrator as shim
    from debate.orchestrator import (
        ProcessDebateOrchestrator,
        make_relay,
        validate_child_message,
    )

    assert shim.ProcessDebateOrchestrator is ProcessDebateOrchestrator
    assert shim.make_relay is make_relay
    assert shim.validate_child_message is validate_child_message
    assert shim._make_relay is make_relay
    assert shim._validate_child_message is validate_child_message
    assert set(shim.__all__) == {
        "ProcessDebateOrchestrator",
        "make_relay",
        "validate_child_message",
    }


def test_single_orchestrator_shim_reexports():
    import debate.single_orchestrator as shim
    from debate.legacy import DebateOrchestrator

    assert shim.DebateOrchestrator is DebateOrchestrator
    assert shim.__all__ == ["DebateOrchestrator"]
