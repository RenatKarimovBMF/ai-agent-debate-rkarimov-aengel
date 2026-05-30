# Worked example — custom topic (abortion)

A complete, unedited 10-ping session on a **custom motion** supplied at
runtime, included to demonstrate that the engine is **topic-agnostic**:
the same orchestrator, skills, and research-backed rubric handle an
arbitrary real-world debate, not just the default film comparison — and
do so respectfully, with cited sources on every turn.

## Files in this folder

| File | What it is |
|------|------------|
| [`transcript.md`](transcript.md) | The **verbatim, untruncated** transcript auto-saved by the run (all 20 turns in full + citations) |
| [`verdict.json`](verdict.json) | The machine-readable verdict the judge produced |

## How it was run

```powershell
uv run python -m debate.main --config config/setup.json `
  --topic "Should abortion be legal and accessible?" `
  --pro "Supporting legal abortion access" `
  --con "Opposing legal abortion"
```

| Field | Value |
|-------|-------|
| Session id | `d5b184b0` |
| LLM provider | `claude_cli` (Claude via the CLI, Claude Pro login) |
| Topic | Should abortion be legal and accessible? (custom, via `--topic`) |
| Pings per side | 10 (20 debater turns + 1 verdict = 21 LLM calls) |
| Wall-clock | ~9 minutes (ended 15:34:34) |
| Side assignment | Parent assigned PRO → *Opposing*, CON → *Supporting* (session-seeded; varies per run) |
| Winner | **CON — Supporting legal abortion access**, 83 to 79 |

## What this example demonstrates

- **Topic-agnostic engine** — the motion, sides, and the entire debate were
  supplied with `--topic`/`--pro`/`--con`; nothing about the default film
  debate leaked in. Same code path as the default run.
- **Runtime side assignment** — the Parent put PRO on *Opposing* and CON on
  *Supporting* this session (it varies by `session_id`), so the winning side
  here is defended by CON.
- **Substantive, cited clash** — both sides argued real jurisprudence and
  data (*McFall v. Shimp*, the Unborn Victims of Violence Act, WHO, the
  Turnaway Study, Guttmacher, the Commonwealth Fund, Safe Haven laws). Every
  turn carried at least one real source.
- **Refute-with-citation, decisively** — at ping 4 PRO cited the Unborn
  Victims of Violence Act to argue the law already deems the fetus a victim;
  CON quoted the same statute's §1841(c) consent-exclusion clause to show it
  draws the line at the woman's consent — turning PRO's own evidence against
  him. At ping 5 CON anchored the round on *McFall v. Shimp* (no person may
  be conscripted to sustain another's body), which PRO never overcame.
- **Research-backed, no-tie verdict** — distinct scores (83 vs 79) with a
  rationale tied to the five judging principles (clash, refute-with-citation,
  dropped arguments).
- **Respectful handling of a sensitive motion** — the debater prompt's
  "respectful, politically appropriate, no insults" rule held throughout.

## Verdict (excerpt)

```
FINAL VERDICT: CON wins
PRO score: 79.0
CON score: 83.0
```

> "CON's central argument — grant fetal personhood arguendo, and forced
> gestation still fails because no person, living or dead, may be conscripted
> to sustain another's body (*McFall v. Shimp*, the corpse-harvesting and
> kidney-donation lines) — was the hardest claim in the round to defeat, and
> CON defended it intact across every PRO counter. CON consistently turned
> PRO's own evidence: the §1841(c) consent carve-out and the safe-haven
> transferability point were repurposed to show the law already encodes
> consent/autonomy as the distinguishing factor. The deciding margin is
> Clash discipline."

The full rationale and persuasion notes are in [`verdict.json`](verdict.json).
