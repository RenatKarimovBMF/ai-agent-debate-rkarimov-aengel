from __future__ import annotations

import multiprocessing as mp

from debate.models import AgentRole, DebateMessage
from debate.orchestrator.commands import turn_request
from debate.orchestrator.events import emit_event, queue_get_or_timeout
from debate.orchestrator.messages import validate_child_message

# Whole-position capitulation markers. Minor concessions ("I concede that
# X, but…") are legitimate and intentionally NOT listed here — only signals
# that a debater abandoned its side or was swept by the opponent.
_CAPITULATION_MARKERS = (
    "i agree with you",
    "i agree with my opponent",
    "you are right",
    "you're right",
    "you have convinced me",
    "you've convinced me",
    "i concede the debate",
    "i concede defeat",
    "i change my position",
    "i now agree",
    "i switch sides",
    "i withdraw my argument",
    "i abandon my position",
    "i support the opposing",
)

_CORRECTION = (
    "RINGSIDE WARNING from the JUDGE: your last turn drifted toward agreeing "
    "with your opponent. You were assigned to DEFEND your side and to "
    "CONTRADICT the opponent — not to concede the debate. Redo this turn: "
    "open with a direct rebuttal of the opponent's strongest point, hold your "
    "assigned position, and back any factual refutation with a cited source."
)


def capitulation_warning(text: str) -> str | None:
    """Return a corrective instruction when a turn over-agrees / switches side.

    This is the judge's mid-debate intervention required by the exercise
    brief: the host must stop an agent that is being swept into agreement
    and remind it of its role.
    """
    lowered = text.lower()
    if any(marker in lowered for marker in _CAPITULATION_MARKERS):
        return _CORRECTION
    return None


def solicit_turn(
    *,
    role: AgentRole,
    ping: int,
    opponent_text: str | None,
    request_queue: mp.Queue,
    response_queue: mp.Queue,
    session_id: str,
    event_queue: mp.Queue,
    timeout: float,
) -> DebateMessage:
    """Ask a child for its turn and enforce on-side debating.

    If the first answer capitulates, the Parent issues one ringside warning
    and re-requests the turn with a correction note, mirroring the
    boxing-referee role in `.claude/skills/debate-host-protocol`.
    """
    label = role.value.upper()
    request_queue.put(turn_request(ping, opponent_text))
    raw = queue_get_or_timeout(response_queue, timeout, f"{label} response")
    message = validate_child_message(
        raw, expected_sender=role, session_id=session_id, ping=ping
    )

    warning = capitulation_warning(message.payload.text)
    if warning is None:
        return message

    emit_event(
        event_queue,
        f"PARENT WARNING to {label}: turn drifted off-side; re-requesting.",
        kind="host",
        data={"role": role.value, "ping": ping},
    )
    request_queue.put(turn_request(ping, opponent_text, correction=warning))
    raw = queue_get_or_timeout(response_queue, timeout, f"{label} corrected response")
    return validate_child_message(
        raw, expected_sender=role, session_id=session_id, ping=ping
    )
