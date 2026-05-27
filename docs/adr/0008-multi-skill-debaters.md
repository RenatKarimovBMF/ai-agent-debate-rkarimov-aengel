# ADR-008: Multi-skill debaters + lore-only side skills

**Status:** Accepted
**Date:** 2026-05-27

## Context

In-class clarification: each debater should have more than one
skill — one for building arguments, one for refuting the opponent —
modelled on a legal team where each lawyer specialises. The skills
must be project-local (`.claude/skills/`), not global, so they do not
leak into other projects.

## Decision

Split each debater's behaviour into three skill files:

- `debate-argument-builder/SKILL.md` — side-agnostic positive-case
  playbook (Claim → Warrant → Impact → Source).
- `debate-rebuttal-strategist/SKILL.md` — side-agnostic refutation
  playbook (with the refute-with-citation rule).
- `debate-pro-godfather/SKILL.md` and `debate-con-shawshank/SKILL.md`
  — lore-only side knowledge consumed by the two playbook skills.

The host (`debate-host-protocol`) picks which lore skill applies per
agent at session start.

## Consequences

**Positive:**

- Side knowledge can be swapped in for new topics without touching
  the playbook (the new topic just needs new lore skills).
- Refutation discipline is shared across both sides, so the
  refute-with-citation rule cannot be forgotten by one side and
  enforced by the other.
- Smaller, focused skill files (each is well under the 150-line cap).

**Negative:**

- Five skill files per debate instead of one. Acceptable cost for
  the clarity.

## Alternatives considered

- **One monolithic skill per side** — what we started with;
  abandoned because the in-class clarification said multi-skill is
  required.
- **Global skills shared across projects** — explicitly forbidden by
  the brief.
- **Generic skills only (no lore)** — rejected; the per-side
  knowledge meaningfully improves debate quality.
