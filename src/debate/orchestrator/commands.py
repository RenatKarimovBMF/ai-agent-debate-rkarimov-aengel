from __future__ import annotations

STOP = "STOP"
START = "START"
RELAY = "RELAY"
TURN_REQUEST = "TURN_REQUEST"
ASSIGN = "ASSIGN"
ERROR = "ERROR"


def turn_request(ping: int, opponent_text: str | None) -> dict[str, object]:
    return {
        "type": TURN_REQUEST,
        "ping": ping,
        "opponent_text": opponent_text,
    }


def relay_message(message: dict[str, object]) -> dict[str, object]:
    return {
        "type": RELAY,
        "message": message,
    }


def assignment(
    *,
    role: str,
    topic: str,
    assigned_side: str,
    opponent_side: str,
    pings: int,
    max_words: int,
    rules: list[str],
) -> dict[str, object]:
    """Parent → child briefing delivered before the first turn request.

    Mirrors the runtime side-assignment protocol documented in
    `.claude/skills/debate-host-protocol/SKILL.md`. The Parent owns this
    decision; sides are not read from a hardcoded config field.
    """
    return {
        "type": ASSIGN,
        "role": role,
        "topic": topic,
        "assigned_side": assigned_side,
        "opponent_side": opponent_side,
        "pings": pings,
        "max_words": max_words,
        "rules": list(rules),
    }


def worker_error(role: str, error: str) -> dict[str, object]:
    return {
        "type": ERROR,
        "role": role,
        "error": error,
    }
