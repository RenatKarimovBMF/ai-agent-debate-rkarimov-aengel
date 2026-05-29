# ADR-008: Multi-skill debaters

**Status:** Accepted
**Date:** 2026-05-27 (updated 2026-05-30)

## Context

In-class clarification: each debater should have more than one
skill — one for building arguments, one for refuting the opponent —
modelled on a legal team where each lawyer specialises. The skills
must be project-local (`.claude/skills/`), not global, so they do not
leak into other projects.

## Decision

Split each debater's behaviour into three **generic, topic-agnostic**
skill files:

- `debate-argument-builder/SKILL.md` — side-agnostic positive-case
  playbook (Claim → Warrant → Impact → Source).
- `debate-rebuttal-strategist/SKILL.md` — side-agnostic refutation
  playbook (with the refute-with-citation rule).
- `debate-evidence/SKILL.md` — side-agnostic, topic-agnostic sourcing
  guidance: the debater finds its own concrete, citeable evidence for
  whatever side and topic it is assigned. No facts are hardcoded.

## Update (2026-05-30)

This ADR originally shipped two **lore** skills
(`debate-pro-godfather`, `debate-con-shawshank`) that carried curated
facts about the two default films. Once the engine became fully
generic (any `--topic`), hardcoded film lore conflicted with that goal:
on the injected providers (Gemini / Anthropic API, see ADR-003) the
lore would be appended even for unrelated topics. We removed the two
lore skills and replaced them with the single generic `debate-evidence`
skill, which teaches *how* to find and deploy evidence rather than
supplying any. Debaters now source their own evidence at runtime, which
keeps the skill layer topic-agnostic.

## Consequences

**Positive:**

- The skill layer is fully topic-agnostic — any `--topic` works without
  authoring new skills.
- Refutation and sourcing discipline are shared across both sides, so
  the refute-with-citation rule and citation quality cannot be forgotten
  by one side and enforced by the other.
- Smaller, focused skill files (each well under the 150-line cap).

**Negative:**

- No pre-loaded topic facts: for the default film debate the agents must
  source evidence themselves (web search on Gemini, model knowledge on
  Claude) instead of reading curated lore. Acceptable for genericity.

## Alternatives considered

- **One monolithic skill per side** — abandoned; the in-class
  clarification requires multi-skill debaters.
- **Global skills shared across projects** — explicitly forbidden by
  the brief.
- **Per-side lore skills** — the original approach; replaced (see Update
  above) because hardcoded facts broke topic-genericity.
