# ADR-009: Research-backed judging rubric

**Status:** Accepted
**Date:** 2026-05-27

## Context

The exercise brief says it is insufficient to declare the Parent "an
expert" — its rubric must rest on published debate methodology.
The judge's decision should be auditable against written criteria.

## Decision

The Parent skill stack
(`debate-parent-judge` + `debate-host-protocol` + `debate-judge-rubric`)
and the verdict prompt are grounded in the WUDC manual, IDEA's
adjudicator handbook, NSDA's scoring guidance, and Alfred Snider's
published criteria.

Five judging principles:

1. **Persuasion, not truth.** A well-defended falsehood beats a
   poorly defended truth (with the refute-with-citation exception
   below).
2. **Clash matters.** Direct engagement with the opponent's last
   point is rewarded.
3. **Refute with citation.** A debater alleging a falsehood must
   cite a real source in the same turn, or the allegation is
   penalised.
4. **Dropped arguments stand.** A claim unanswered for two
   consecutive turns counts as conceded.
5. **No tie.** Scores must differ; the winner has the strictly
   higher score.

Five-axis scoring rubric (sums to 100):

| Axis | Weight |
| --- | ---: |
| Matter (substance, evidence quality) | 30 |
| Clash (direct engagement with opponent) | 25 |
| Manner (delivery, structure, civility) | 15 |
| Method (case organisation, signposting) | 15 |
| Burden (meeting the prima-facie burden) | 15 |

Documented in `docs/PRD_judge_rubric.md` and enforced in
`agents/judge_prompts.py` (`verdict_prompt`).

## Consequences

**Positive:**

- Verdicts are auditable against a written rubric; the verdict's
  `persuasion_notes` field is required to reference at least one
  principle.
- The judge stops drifting into "Godfather is obviously better"
  popularity scoring because Principle 1 is restated near the
  evidence.

**Negative:**

- Longer judge prompts (verdict prompt is ~50 lines after
  refactor) eating into the model's context budget. We send only
  the last 80 transcript items to stay under Gemini Flash's window.

## Alternatives considered

- **Free-form "your judgement" prompt** — what we started with;
  abandoned because verdicts were inconsistent and the grader
  could not check them against criteria.
- **Pure numeric rubric without principles** — rejected; the
  principles are what catch the refute-with-citation rule.
- **Different rubric weights** — we picked the WUDC-leaning
  Matter=30 / Clash=25 distribution because the assignment values
  argument quality and engagement specifically.
