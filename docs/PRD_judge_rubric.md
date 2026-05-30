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

## 3. The scoring system (how points are awarded)

Each side is scored **0–100** as the sum of five weighted categories. The
weights and what each measures:

| Category | Weight | Source | Measures |
|----------|-------:|--------|----------|
| Matter   | 30 | WUDC | Substance, evidence quality, logical chain. |
| Clash    | 25 | IDEA (Karl Popper) | Direct engagement with the opponent's actual claim. |
| Manner   | 15 | WUDC | Clarity, tone, respect, word economy. |
| Method   | 15 | WUDC | Structure, signposting, format/word-cap adherence. |
| Burden   | 15 | NSDA | Carrying the burden of proof; answering dropped claims. |
| **Total**| **100** | — | Sum of the above. |

### 3.1 Per-category bands

The judge places each side in a band per category (full tables in the
`debate-judge-rubric` skill); summarised:

- **Matter (0–30):** 27–30 multi-warrant + strong sources, no gaps; 20–26
  solid with ≥1 cited source/turn; 13–19 mostly assertion; 0–12 empty or
  hallucinated facts caught by the opponent.
- **Clash (0–25):** 22–25 names the opponent's claim, attacks the warrant,
  and weighs it; 16–21 engages most points; 9–15 often talks past; 0–8
  parallel monologues.
- **Manner (0–15):** 13–15 clear/respectful/economical … 0–3 insults or
  unintelligible.
- **Method (0–15):** 13–15 every turn signposts claim→warrant→impact and
  respects the cap … 0–3 no structure / format violations.
- **Burden (0–15):** 13–15 all burdens met, opponent's main claims answered
  … 0–3 burden not attempted.

### 3.2 The "refute a lie" adjustment

Lies are allowed; a *bare* contradiction is not a refutation. When a side
alleges the opponent stated a falsehood:

- **With a cited source** that contradicts the claim → the opponent loses up
  to **5 Matter + 3 Clash** points for the fabricated claim.
- **Without a citation** → the *accuser* loses **3 Clash** points (bare
  denial doesn't count).

### 3.3 Combining into the verdict

The five categories sum to each side's 0–100 total; the higher total wins.
The Parent maps the rubric output to the verdict JSON
(`pro_score`, `con_score`, `winner`, `rationale`, `persuasion_notes`), and
`persuasion_notes` must name at least one of the five judging principles.

### 3.4 No ties — tie-break order

Scores **must differ**. If raw totals tie, break in order:

1. Higher **Clash** score wins.
2. Else, fewer **dropped claims** wins.
3. Else, the side that opened more new lines wins.
4. Last resort: +1 to the side judged stronger on the opening ping
   (documented in `persuasion_notes`).

The code-side fallback (`agents/verdict_builder.py`) also bumps the stated
winner by 1 if the model ever emits equal scores, so a tie can never reach
the output (see KNOWN_LIMITATIONS L-08).

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
- **`debate-evidence`** — side-agnostic, topic-agnostic sourcing skill:
  how to find concrete, citeable evidence and weigh/turn sources for any
  assigned side and topic. It supplies no hardcoded facts.

All three are independent of which side the debater defends — the side is
assigned by the Parent at runtime via `debate-host-protocol`.

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
