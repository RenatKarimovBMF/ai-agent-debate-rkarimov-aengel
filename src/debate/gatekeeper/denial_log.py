from __future__ import annotations

import logging

from debate.models import AgentRole

logger = logging.getLogger("debate.gatekeeper")


def log_denial(
    *,
    role: AgentRole,
    reason: str,
    total_requests: int,
    per_agent: dict[str, int],
) -> None:
    logger.warning(
        "gatekeeper_denied",
        extra={
            "extra_data": {
                "event": "gatekeeper_denied",
                "role": role.value,
                "reason": reason,
                "total_requests": total_requests,
                "per_agent": per_agent,
            }
        },
    )
