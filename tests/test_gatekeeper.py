import pytest

from debate.config import GatekeeperConfig
from debate.gatekeeper import BudgetExceededError, Gatekeeper
from debate.models import AgentRole


def test_gatekeeper_blocks_over_budget():
    gk = Gatekeeper(GatekeeperConfig(enabled=True, max_total_requests=2, max_requests_per_agent=2))
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)
    gk.check(AgentRole.CON)
    gk.record(AgentRole.CON)
    with pytest.raises(BudgetExceededError):
        gk.check(AgentRole.PRO)
