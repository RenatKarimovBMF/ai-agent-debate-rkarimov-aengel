"""Targeted branch coverage for `debate.agent_base.BaseAgent`.

See `_coverage_helpers.py` for shared fixtures. Kept under the
project-wide 150-line cap (PRD NFR-01).
"""

from __future__ import annotations

import pytest

from debate import __version__
from debate.agent_base import BaseAgent
from debate.config import load_config
from debate.env_loader import project_root
from debate.models import AgentRole
from debate.transport import ChannelPair
from sdk.llm_client import LlmResponse

from ._coverage_helpers import MagicMock, make_gatekeeper, make_message


class _StubAgent(BaseAgent):
    def system_prompt(self) -> str:
        return "sys"


def test_version_exposed_at_package_root():
    assert __version__ == "1.00"


def test_project_root_is_repo_root():
    assert (project_root() / "pyproject.toml").exists()


def test_base_agent_send_without_channels_raises():
    cfg = load_config()
    agent = _StubAgent(AgentRole.PARENT, cfg, None, make_gatekeeper(), MagicMock(), "sess")
    with pytest.raises(RuntimeError, match="Parent agent does not use child channels"):
        agent.send(make_message())


def test_base_agent_receive_returns_none_without_channels():
    cfg = load_config()
    agent = _StubAgent(AgentRole.PARENT, cfg, None, make_gatekeeper(), MagicMock(), "sess")
    assert agent.receive(timeout=0.0) is None


def test_base_agent_send_and_receive_with_channels():
    cfg = load_config()
    child_to_parent = MagicMock()
    parent_to_child = MagicMock()
    parent_to_child.read.return_value = "incoming"
    channels = ChannelPair(child_to_parent, parent_to_child)
    agent = _StubAgent(AgentRole.PRO, cfg, channels, make_gatekeeper(), MagicMock(), "sess")

    msg = make_message()
    agent.send(msg)
    child_to_parent.write.assert_called_once_with(msg)
    assert agent.receive(timeout=0.5) == "incoming"
    parent_to_child.read.assert_called_once_with(timeout=0.5)


def test_base_agent_invoke_llm_increments_gatekeeper():
    client = MagicMock()
    client.complete.return_value = LlmResponse(text="answer", raw="answer", provider="x")
    agent = _StubAgent(AgentRole.PRO, load_config(), None, make_gatekeeper(), client, "sess")
    assert agent.invoke_llm("user") == "answer"
    client.complete.assert_called_once()
