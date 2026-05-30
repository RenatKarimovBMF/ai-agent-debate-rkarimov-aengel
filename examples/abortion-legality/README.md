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
| Session id | `c1255aa1` |
| LLM provider | `claude_cli` (Claude via the CLI, Claude Pro login) |
| Topic | Should abortion be legal and accessible? (custom, via `--topic`) |
| Pings per side | 10 (20 debater turns + 1 verdict = 21 LLM calls) |
| Wall-clock | ~7m28s (04:17:32 → 04:25:00) |
| Winner | **PRO — Supporting legal abortion access**, 84 to 80 |

## What this example demonstrates

- **Topic-agnostic engine** — the motion, sides, and the entire debate were
  supplied with `--topic`/`--pro`/`--con`; nothing about the default film
  debate leaked in. Same code path as the default run.
- **Substantive, cited clash** — both sides argued real jurisprudence and
  data (*McFall v. Shimp*, WHO, the NBER Dobbs paper, the Turnaway Study,
  Texas statutes, Stanford/IEP philosophy entries, Guttmacher, CDC). Every
  turn carried at least one real source.
- **Refute-with-citation in action** — the judge credited PRO for turning
  CON's own JAMA fetal-pain source with a citation in the same turn.
- **Research-backed, no-tie verdict** — distinct scores (84 vs 80) with a
  rationale tied to the five judging principles (clash, refute-with-citation,
  dropped arguments).
- **Respectful handling of a sensitive motion** — the debater prompt's
  "respectful, politically appropriate, no insults" rule held throughout.

## Verdict (excerpt)

```
FINAL VERDICT: PRO wins
PRO score: 84.0
CON score: 80.0
```

> "The decisive battleground was the bodily-autonomy analogy. CON repeatedly
> tried to break it on causation, but PRO produced the load-bearing legal
> counter (*McFall v. Shimp*, plus the delegability point: every parental
> duty CON cited can be discharged by a third party, whereas gestation
> cannot…). CON never met the refute-with-citation bar on this central
> claim … so PRO's strongest line survived to the end."

The full rationale and persuasion notes are in [`verdict.json`](verdict.json).
