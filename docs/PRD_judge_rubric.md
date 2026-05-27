# PRD — Judge Rubric & Skill Architecture

**Owner:** Renat Karimov, Alon Engel
**Status:** Implemented as `.claude/skills/debate-judge-rubric` and
`.claude/skills/debate-parent-judge`.

## 1. Purpose

The exercise spec requires that the Parent agent decide the winner on
**persuasion**, not factual truth, and that the decision rest on a
defensible methodology rather than gut feeling. This PRD documents the
research we used to build the judge skill and the per-category rubric the
Parent applies when issuing the final verdict.

## 2. Research basis

We surveyed publicly documented judging methods used in competitive debate
to identify principles that translate into an LLM judge prompt:

1. **WUDC Adjudication Manual** (World Universities Debating
   Championship, British Parliamentary format). Source of the
   **Matter / Manner / Method** triad. See
   <https://worlddebating.org>.
2. **IDEA Judging Guide** (International Debate Education Association,
   Karl Popper format). Source of the **Clash** principle — a constructive
   argument that is never engaged with survives the round; a rebuttal
   without engagement is worthless. See <https://idebate.net>.
3. **NSDA Speaker Points Guide** (National Speech & Debate Association).
   Source of the **Burden of proof** category and the **dropped-argument**
   bookkeeping. See <https://www.speechanddebate.org>.
4. **Alfred C. "Tuna" Snider — *Code of the Debater*** (University of
   Vermont). Source of the **reasonable judge** standard: the judge is an
   informed but non-specialist citizen and should *not* substitute personal
   topic expertise for what the debaters establish in-round.
5. **Tabula rasa paradigm** (cross-format consensus). The judge enters
   each round with no prior view on the topic and accepts only what the
   debaters establish.

## 3. Rubric (operationalised in `debate-judge-rubric` skill)

| Category | Weight | Source |
|----------|-------:|--------|
| Matter   | 30 | WUDC |
| Manner   | 15 | WUDC |
| Method   | 15 | WUDC |
| Clash    | 25 | IDEA (Karl Popper) |
| Burden   | 15 | NSDA |
| **Total**| **100** | — |

Per-category band tables, dropped-claim handling, the "refute a lie with a
citation" rule, and tie-breaking order are specified in the
`debate-judge-rubric` skill file. They are not repeated here to keep the
PRD as a living-decisions document rather than a duplicate spec.

## 4. Skill architecture for the Parent

The Parent uses three project-local skills:

- **`debate-parent-judge`** — top-level identity and the five judging
  principles (persuasion-not-truth, clash, refutation-needs-evidence,
  dropped-arguments-stand, no-tie).
- **`debate-host-protocol`** — opening address protocol: assigns side at
  runtime, sends each child a personalised JSON briefing, performs ready
  check before ping 1.
- **`debate-judge-rubric`** — per-category scoring, dropped-claim
  bookkeeping, tie-break order.

The Parent agent is instructed (via system prompt and skill descriptions)
to consult `debate-host-protocol` at session start and
`debate-judge-rubric` at session end, and to reference the five
principles from `debate-parent-judge` throughout.

## 5. Skill architecture for each debater

Each debater uses up to three project-local skills:

- **`debate-argument-builder`** — side-agnostic constructive case
  (claim → warrant → impact → source).
- **`debate-rebuttal-strategist`** — side-agnostic refutation, including
  the hard rule that alleging a falsehood requires a cited source in the
  same turn.
- **`debate-pro-godfather`** / **`debate-con-shawshank`** — topic-knowledge
  layer with curated facts and counter-moves, used only when the topic is
  the Godfather-vs-Shawshank question.

The first two are independent of which side the debater defends — the
side is assigned by the Parent at runtime via `debate-host-protocol`.

## 6. Why this satisfies the course requirements

| Course requirement | Mechanism |
|--------------------|-----------|
| Judge skill must be research-based, not generic | `debate-parent-judge` cites WUDC, IDEA, NSDA, and Snider; `PRD_judge_rubric.md` documents sources. |
| Multiple skills per agent | Parent uses 3 skills; each debater uses 2–3 skills. |
| Project-local skills only | All skills live under `.claude/skills/` inside this repository. |
| Side not hardcoded | `debate-host-protocol` assigns sides at runtime, seeded by `session_id` for replayability. |
| Refute lies with citations | Enforced in `debate-rebuttal-strategist` and rewarded/penalised in `debate-judge-rubric`. |
| Verdict on persuasion, not truth | Principle #1 in `debate-parent-judge`; explicit in the rubric. |
| No ties | Tie-break order specified in `debate-judge-rubric`. |

## 7. Open items

- Wire `debate-host-protocol` into the Parent's runtime so the side is
  decided at session start rather than read from `config/setup.json`.
  Tracked in `docs/TODO.md`.
- Add a per-session log of dropped-claim bookkeeping to the JSONL
  transcript so the verdict can cite which claims were dropped. Tracked
  in `docs/TODO.md`.
