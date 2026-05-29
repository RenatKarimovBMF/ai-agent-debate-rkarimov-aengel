"""Coverage + validation for `debate.skills` (Gemini-only skill injection).

Verifies the loader (frontmatter stripping, missing files, role mapping)
and that an agent whose provider resolves to Gemini gets the project
skills appended to its system prompt, while other providers do not.
"""

from __future__ import annotations

from debate import skills
from debate.agents.parent_agent import ParentAgent
from debate.config import load_config
from debate.models import AgentRole
from debate.skills import (
    _strip_frontmatter,
    load_skill,
    skill_block_for_role,
    skill_suffix_for_provider,
)
from debate.transport import ChannelPair

from ._coverage_helpers import MagicMock, make_gatekeeper


def test_strip_frontmatter_removes_block():
    assert _strip_frontmatter("---\nname: x\n---\nBODY").strip() == "BODY"


def test_strip_frontmatter_no_closing_returns_text():
    text = "---\nname: x\nno closing fence"
    assert _strip_frontmatter(text) == text


def test_strip_frontmatter_plain_text_unchanged():
    assert _strip_frontmatter("# Heading\nbody") == "# Heading\nbody"


def test_load_skill_reads_real_skill():
    body = load_skill("debate-argument-builder")
    assert body
    assert not body.startswith("---")


def test_load_skill_missing_returns_empty():
    assert load_skill("no-such-skill-xyz") == ""


def test_generic_evidence_skill_loads():
    body = load_skill("debate-evidence")
    assert body
    assert "godfather" not in body.lower()  # no hardcoded topic facts


def test_skill_block_for_role_contains_skill_text():
    block = skill_block_for_role(AgentRole.PRO)
    assert "Project skills" in block


def test_skill_block_empty_when_no_bodies(monkeypatch):
    monkeypatch.setattr(skills, "load_skill", lambda name: "")
    assert skill_block_for_role(AgentRole.PARENT) == ""


def test_skill_suffix_skips_claude_cli():
    assert skill_suffix_for_provider("claude_cli", AgentRole.PRO) == ""


def test_skill_suffix_injects_for_gemini():
    assert "Project skills" in skill_suffix_for_provider("gemini", AgentRole.PRO)


def test_skill_suffix_injects_for_anthropic():
    assert "Project skills" in skill_suffix_for_provider("anthropic", AgentRole.CON)


def _parent_with_provider(provider_value) -> ParentAgent:
    cfg = load_config()
    pair = ChannelPair(MagicMock(), MagicMock())
    client = MagicMock()
    if isinstance(provider_value, Exception):
        client.active_provider.side_effect = provider_value
    else:
        client.active_provider.return_value = provider_value
    return ParentAgent(cfg, make_gatekeeper(), client, "sess", pair, pair)


def test_agent_system_prompt_injects_skills_on_gemini():
    parent = _parent_with_provider("gemini")
    prompt = parent.system_prompt()
    assert "Project skills" in prompt
    assert "PARENT/JUDGE" in prompt  # base judge prompt still present


def test_agent_system_prompt_injects_skills_on_anthropic():
    parent = _parent_with_provider("anthropic")
    assert "Project skills" in parent.system_prompt()


def test_agent_system_prompt_no_skills_on_claude_cli():
    parent = _parent_with_provider("claude_cli")
    assert "Project skills" not in parent.system_prompt()


def test_active_provider_handles_raise():
    parent = _parent_with_provider(RuntimeError("no provider"))
    assert parent._active_provider() == ""
