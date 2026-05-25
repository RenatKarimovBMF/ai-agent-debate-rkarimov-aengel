import time

import pytest

from debate.config import GatekeeperConfig
from debate.gatekeeper import BudgetExceededError, Gatekeeper
from debate.models import AgentRole


def _config(**overrides) -> GatekeeperConfig:
    base = {
        "enabled": True,
        "max_total_requests": 200,
        "max_requests_per_agent": 80,
        "min_interval_ms": 0,
        "log_denials": False,
    }
    base.update(overrides)
    return GatekeeperConfig(**base)


def test_gatekeeper_blocks_over_budget():
    gk = Gatekeeper(_config(max_total_requests=2, max_requests_per_agent=2))
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)
    gk.check(AgentRole.CON)
    gk.record(AgentRole.CON)
    with pytest.raises(BudgetExceededError):
        gk.check(AgentRole.PRO)


def test_disabled_gatekeeper_skips_limits():
    gk = Gatekeeper(_config(enabled=False, max_total_requests=1, max_requests_per_agent=1))
    for _ in range(5):
        gk.check(AgentRole.PRO)
        gk.record(AgentRole.PRO)

    assert gk.total_requests == 0


def test_global_cap_triggers_on_next_check():
    gk = Gatekeeper(_config(max_total_requests=2, max_requests_per_agent=10))
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)

    with pytest.raises(BudgetExceededError, match="Global request budget"):
        gk.check(AgentRole.CON)


def test_per_agent_cap_is_independent():
    gk = Gatekeeper(_config(max_total_requests=10, max_requests_per_agent=1))
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)

    with pytest.raises(BudgetExceededError, match="Budget exceeded for pro"):
        gk.check(AgentRole.PRO)

    gk.check(AgentRole.CON)
    gk.record(AgentRole.CON)
    assert gk.requests_for(AgentRole.CON) == 1


def test_total_requests_property():
    gk = Gatekeeper(_config(max_total_requests=10, max_requests_per_agent=10))
    gk.check(AgentRole.PARENT)
    gk.record(AgentRole.PARENT)
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)

    assert gk.total_requests == 2
    assert gk.requests_for(AgentRole.PARENT) == 1
    assert gk.requests_for(AgentRole.PRO) == 1


def test_denial_is_logged_when_enabled():
    from unittest.mock import patch

    gk = Gatekeeper(
        _config(max_total_requests=1, max_requests_per_agent=1, log_denials=True)
    )
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)

    with patch("debate.gatekeeper.core.log_denial") as mock_log:
        with pytest.raises(BudgetExceededError):
            gk.check(AgentRole.PRO)

    assert gk.denial_count == 1
    mock_log.assert_called_once()


def test_min_interval_ms_serializes_requests():
    gk = Gatekeeper(_config(max_total_requests=10, max_requests_per_agent=10, min_interval_ms=80))

    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)

    start = time.monotonic()
    gk.check(AgentRole.PRO)
    gk.record(AgentRole.PRO)
    elapsed_ms = (time.monotonic() - start) * 1000

    assert elapsed_ms >= 60


def test_rate_limits_loaded_from_json():
    from debate.config import load_config

    cfg = load_config()
    assert cfg.gatekeeper.enabled is True
    assert cfg.gatekeeper.max_total_requests == 200
    assert cfg.gatekeeper.log_denials is True

    from debate.config.loader import project_root

    demo = load_config(project_root() / "config" / "demo_setup.json")
    assert demo.gatekeeper.max_total_requests == 80
    assert demo.gatekeeper.max_requests_per_agent == 30
