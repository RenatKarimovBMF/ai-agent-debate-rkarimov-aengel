---
name: debate-judge-rubric
description: Score a completed debate transcript against a research-backed rubric (Matter, Manner, Method, Clash, Burden) inspired by WUDC, IDEA Karl Popper, and NSDA judge training. Produce per-category scores and a defensible total. Use after all pings are exchanged; the parent-judge skill calls this for the final verdict.
---

# Judge Rubric — per-category scoring

This skill turns a debate transcript into numerical scores. The rubric is
adapted from three published judging frameworks so that the final verdict
is defensible:

- **WUDC Adjudication Manual** — Matter / Manner / Method.
- **IDEA Karl Popper Format Judging Guide** — Clash weighting.
- **NSDA Speaker Points Guide** — Burden of proof and dropped arguments.

## Categories and weights

| Category | Weight | Score range | What it measures |
|----------|-------:|------------:|------------------|
| **Matter** | 30 | 0–30 | Substance, evidence, logical chain, source quality. |
| **Manner** | 15 | 0–15 | Clarity, tone, respect, word economy. |
| **Method** | 15 | 0–15 | Structure, signposting, adherence to format and word cap. |
| **Clash** | 25 | 0–25 | Direct engagement with opponent's last point. Penalise speaking past the opponent. |
| **Burden** | 15 | 0–15 | Did the side carry its burden of proof? Were dropped opponent claims addressed? |
| **Total** | **100** | 0–100 | Sum of the above. |

## How to score each category

### Matter (0–30)
- 27–30: Multi-warrant arguments, strong sources, no logical gaps.
- 20–26: Solid arguments with at least one cited source per turn.
- 13–19: Mostly assertion; sources thin or weak.
- 0–12: Empty claims, no sources, or hallucinated facts caught by opponent.

### Manner (0–15)
- 13–15: Clear, respectful, economical.
- 9–12: Mostly clear; occasional filler or mild rudeness.
- 4–8: Hard to follow, or disrespectful.
- 0–3: Insults, profanity, or unintelligible.

### Method (0–15)
- 13–15: Every turn signposts claim → warrant → impact; word cap respected.
- 9–12: Generally structured; one or two turns wander.
- 4–8: Disorganised; frequent over-runs.
- 0–3: No structure; format violations.

### Clash (0–25)
- 22–25: Every rebuttal names the opponent's claim, attacks the warrant, and
  weighs it against the side's own framework.
- 16–21: Engages most points; a few drops.
- 9–15: Often speaks past opponent; reruns own talking points.
- 0–8: No engagement; parallel monologues.

### Burden (0–15)
- 13–15: All burdens met; opponent's main claims addressed before extending.
- 9–12: Most burdens met; one significant drop.
- 4–8: Two or more dropped claims that the opponent capitalised on.
- 0–3: Burden of proof not even attempted.

## The "refute a lie" deduction

If a debater **alleges** the opponent lied, the rubric requires a cited
source in the same turn:
- **Citation provided** that contradicts the opponent's claim: opponent
  loses up to 5 Matter points and 3 Clash points for the fabricated claim.
- **No citation provided**: the alleging debater loses 3 Clash points
  (bare contradiction is not refutation).

## Tie-breaking (no ties allowed)

If raw totals tie:
1. Higher **Clash** score wins.
2. If still tied, lower **dropped-claim count** wins.
3. If still tied, the side that opened more new lines of argument wins.
4. As a last resort, add +1 to the side judged stronger on the opening
   ping — but document this clearly in `persuasion_notes`.

## Output format (consumed by `debate-parent-judge`)

```json
{
  "pro": {
    "matter": 24,
    "manner": 13,
    "method": 11,
    "clash": 19,
    "burden": 12,
    "total": 79,
    "dropped_claims": ["opponent's IMDb ranking point"]
  },
  "con": {
    "matter": 21,
    "manner": 13,
    "method": 12,
    "clash": 14,
    "burden": 10,
    "total": 70,
    "dropped_claims": ["AFI ranking", "Oscar count"]
  },
  "winner": "pro",
  "tie_break_used": null
}
```

The parent-judge skill then maps this to the final `VerdictMessage`
(`pro_score`, `con_score`, `winner`, `rationale`, `persuasion_notes`).
