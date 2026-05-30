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
| Session id | `507cd011` |
| LLM provider | `claude_cli` (Claude via the CLI, Claude Pro login) |
| Topic | Should abortion be legal and accessible? (custom, via `--topic`) |
| Pings per side | 10 (20 debater turns + 1 verdict = 21 LLM calls) |
| Wall-clock | ~8m18s (14:28:27 → 14:36:45) |
| Side assignment | Parent assigned PRO → *Opposing*, CON → *Supporting* (session-seeded; varies per run) |
| Winner | **CON — Supporting legal abortion access**, 84 to 80 |

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
- **Refute-with-citation, decisively** — at ping 2 PRO cited the Unborn
  Victims of Violence Act to allege "legal incoherence"; CON quoted the same
  statute's §1841(c) consent-exclusion clause to show it draws the line at
  the woman's consent — turning PRO's own evidence against him.
- **Research-backed, no-tie verdict** — distinct scores (84 vs 80) with a
  rationale tied to the five judging principles (clash, refute-with-citation,
  dropped arguments).
- **Respectful handling of a sensitive motion** — the debater prompt's
  "respectful, politically appropriate, no insults" rule held throughout.

## Verdict (excerpt)

```
FINAL VERDICT: CON wins
PRO score: 80.0
CON score: 84.0
```

> "CON's decisive turn came in ping 2: PRO cited the Unborn Victims of
> Violence Act for 'legal incoherence,' and CON quoted §1841(c)'s explicit
> consent exclusion to show the statute draws its line exactly at the
> woman's consent — a textbook refute-with-citation that PRO never
> recovered. CON's central asymmetry — that the law nowhere compels even a
> parent to surrender blood, marrow, or a kidney to a born child (*McFall
> v. Shimp*) — was pressed every turn and PRO never produced a precedent
> compelling bodily use."

The full rationale and persuasion notes are in [`verdict.json`](verdict.json).
