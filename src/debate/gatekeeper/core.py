from __future__ import annotations

import threading
import time

from debate.config import GatekeeperConfig
from debate.gatekeeper.denial_log import log_denial
from debate.gatekeeper.errors import BudgetExceededError
from debate.models import AgentRole


class Gatekeeper:
    """Limits LLM/API calls per agent and globally (Exercise 02 §8.6).

    Each worker process owns its own Gatekeeper instance. Limits in
    config/rate_limits.json apply per process (pro, con, parent separately).
    """

    def __init__(self, config: GatekeeperConfig) -> None:
        self._config = config
        self._lock = threading.Lock()
        self._total = 0
        self._per_agent: dict[AgentRole, int] = {}
        self._last_request_at: float | None = None
        self._denial_count = 0

    @property
    def total_requests(self) -> int:
        return self._total

    @property
    def denial_count(self) -> int:
        return self._denial_count

    def check(self, role: AgentRole) -> None:
        with self._lock:
            reason = self._denial_reason(role)
            if reason is not None:
                self._denial_count += 1
                if self._config.log_denials:
                    log_denial(
                        role=role,
                        reason=reason,
                        total_requests=self._total,
                        per_agent={r.value: c for r, c in self._per_agent.items()},
                    )
                raise BudgetExceededError(reason)

            self._enforce_min_interval_unlocked()

    def record(self, role: AgentRole) -> None:
        if not self._config.enabled:
            return

        with self._lock:
            self._total += 1
            self._per_agent[role] = self._per_agent.get(role, 0) + 1
            self._last_request_at = time.monotonic()

    def requests_for(self, role: AgentRole) -> int:
        return self._per_agent.get(role, 0)

    def _denial_reason(self, role: AgentRole) -> str | None:
        if not self._config.enabled:
            return None

        if self._total >= self._config.max_total_requests:
            return "Global request budget exceeded"

        count = self._per_agent.get(role, 0)
        if count >= self._config.max_requests_per_agent:
            return f"Budget exceeded for {role.value}"

        return None

    def _enforce_min_interval_unlocked(self) -> None:
        interval_ms = self._config.min_interval_ms
        if interval_ms <= 0 or self._last_request_at is None:
            return

        elapsed_ms = (time.monotonic() - self._last_request_at) * 1000
        wait_ms = interval_ms - elapsed_ms
        if wait_ms > 0:
            time.sleep(wait_ms / 1000)
