"""Backward-compatible imports. Prefer debate.orchestrator."""

from debate.orchestrator import (
    ProcessDebateOrchestrator,
    make_relay,
    validate_child_message,
)

__all__ = ["ProcessDebateOrchestrator", "make_relay", "validate_child_message"]

# Legacy private names used by older tests.
_make_relay = make_relay
_validate_child_message = validate_child_message
