from __future__ import annotations

STOP = "STOP"
START = "START"
RELAY = "RELAY"
TURN_REQUEST = "TURN_REQUEST"
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


def worker_error(role: str, error: str) -> dict[str, object]:
    return {
        "type": ERROR,
        "role": role,
        "error": error,
    }
