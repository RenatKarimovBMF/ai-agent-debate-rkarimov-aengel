from __future__ import annotations

from debate.config import GatekeeperConfig
from debate.models import AgentRole


class BudgetExceededError(RuntimeError):
    pass


class Gatekeeper:
    """Limits API/CLI calls per agent and globally (Exercise 02 §8.6)."""

    def __init__(self, config: GatekeeperConfig) -> None:
        self._config = config
        self._total = 0
        self._per_agent: dict[AgentRole, int] = {}

    def check(self, role: AgentRole) -> None:
        if not self._config.enabled:
            return
        if self._total >= self._config.max_total_requests:
            raise BudgetExceededError("Global request budget exceeded")
        count = self._per_agent.get(role, 0)
        if count >= self._config.max_requests_per_agent:
            raise BudgetExceededError(f"Budget exceeded for {role.value}")

    def record(self, role: AgentRole) -> None:
        if not self._config.enabled:
            return
        self._total += 1
        self._per_agent[role] = self._per_agent.get(role, 0) + 1

    @property
    def total_requests(self) -> int:
        return self._total
