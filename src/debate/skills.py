"""Inject project-local skills into the system prompt for API providers.

The skills under `.claude/skills/` (required by PRD FR-03) are loaded
natively by the **Claude CLI**. The **Gemini** and **Anthropic API**
paths do not read `.claude/`, so for those providers we read the same
skill files here and append their content to the system prompt. This
keeps `.claude/skills/` the single source of truth (no duplication)
while giving every provider the same skills. The Claude CLI is excluded
because it already loads them natively.
"""

from __future__ import annotations

from debate.env_loader import project_root
from debate.models import AgentRole

# Role -> skills the agent should follow. Mirrors the native Claude
# activation: debaters share three generic, topic-agnostic skills; the
# parent uses its host/judge/rubric stack.
_DEBATER_SKILLS = (
    "debate-argument-builder",
    "debate-rebuttal-strategist",
    "debate-evidence",
)
_ROLE_SKILLS: dict[AgentRole, tuple[str, ...]] = {
    AgentRole.PRO: _DEBATER_SKILLS,
    AgentRole.CON: _DEBATER_SKILLS,
    AgentRole.PARENT: (
        "debate-parent-judge",
        "debate-host-protocol",
        "debate-judge-rubric",
    ),
}


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block (``--- ... ---``)."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3 :].lstrip()
    return text


def load_skill(name: str) -> str:
    """Return a skill's markdown body (frontmatter stripped), or ``""``."""
    path = project_root() / ".claude" / "skills" / name / "SKILL.md"
    if not path.is_file():
        return ""
    return _strip_frontmatter(path.read_text(encoding="utf-8")).strip()


def skill_block_for_role(role: AgentRole) -> str:
    """Concatenate the role's skill bodies into one prompt block."""
    bodies = [body for name in _ROLE_SKILLS.get(role, ()) if (body := load_skill(name))]
    if not bodies:
        return ""
    joined = "\n\n---\n\n".join(bodies)
    return "\n\nProject skills (follow these as part of your instructions):\n\n" + joined


# Providers that do NOT load .claude/skills/ natively, so we inject the
# skill content into their system prompt. The Claude CLI is excluded
# because it already loads the skills itself.
_INJECTED_PROVIDERS = ("gemini", "anthropic")


def skill_suffix_for_provider(provider: str, role: AgentRole) -> str:
    """Return the role's skill block for providers that need injection
    (Gemini, Anthropic API); empty for the Claude CLI (native skills)."""
    if provider not in _INJECTED_PROVIDERS:
        return ""
    return skill_block_for_role(role)
