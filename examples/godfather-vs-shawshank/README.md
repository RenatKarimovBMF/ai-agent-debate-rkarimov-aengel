# Worked example — default topic (The Godfather vs The Shawshank Redemption)

A complete, unedited 10-ping session on the project's **default** debate,
run on the `claude_cli` provider. Shows the full mediated flow: runtime
side assignment, a cited source on every turn, the refute-with-citation
rule, and a research-backed no-tie verdict.

## Files in this folder

| File | What it is |
|------|------------|
| [`transcript.md`](transcript.md) | The **verbatim, untruncated** transcript auto-saved by the run (all 20 turns in full + citations) |
| [`verdict.json`](verdict.json) | The machine-readable verdict the judge produced |

## How it was run

```powershell
uv run python -m debate.main --config config/setup.json
```

| Field | Value |
|-------|-------|
| Session id | `00baf1b0` |
| LLM provider | `claude_cli` (Claude via the CLI, Claude Pro login) |
| Topic | Which is the greater film: The Godfather (1972) or The Shawshank Redemption (1994)? |
| Pings per side | 10 (20 debater turns + 1 verdict = 21 LLM calls) |
| Wall-clock | ~9 minutes (started 15:50:42) |
| Winner | **PRO — The Godfather**, 81 to 77 |

## Runtime side assignment

The sides are **not** hardcoded; the Parent/Judge assigns them at session
start, seeded by `session_id`. For `00baf1b0` the host announced:

```
PARENT (host): assigning sides — PRO defends 'The Godfather',
CON defends 'The Shawshank Redemption' (session-seeded, not hardcoded).
```

So in this session PRO argued for *The Godfather* and CON for *Shawshank* —
the mirror of the earlier `fe14afde` run, proving the assignment really does
vary per session.

## What this example demonstrates

- **Mediated routing** — debaters never address each other; every turn is
  relayed by the Parent.
- **Runtime side assignment** — decided by the host, not the config.
- **Cited clash** — IMDb Top 250, AFI 100 Years…100 Movies, the Oscars,
  the National Film Registry, BFI Sight & Sound, all cited in-line.
- **Refute-with-citation rule** — at ping 9 PRO leaned on the National Film
  Registry as a ranking ("the archive reached for The Godfather first");
  CON refuted it by citing the Library of Congress's own statement that the
  Registry is *not* a ranking and that induction tracks eligibility windows,
  a clean cited takedown (the rule cuts both ways, not just against one side).
- **Research-backed, no-tie verdict** — distinct scores (81 vs 77) tied to
  the five judging principles; CON won the cited NFR exchange, but PRO took
  the round on Clash and uncontested expert consensus.

## Verdict (excerpt)

```
FINAL VERDICT: PRO wins
PRO score: 81.0
CON score: 77.0
```

> "PRO turned CON's IMDb anchor by noting The Godfather sits at #2 on the
> very same list — establishing rough parity among the popular crowd and
> forcing the tiebreak onto expert/critical consensus … There PRO held
> concrete, side-by-side evidence (AFI #2 vs. Shawshank #72 on the same
> 2007 ballot; the 1973 Best Picture/Actor/Screenplay sweep). CON answered
> only by impugning the AFI jury … never produced a competing expert
> ranking. Higher Clash and fewer dropped claims both break to PRO."

The full rationale and persuasion notes are in [`verdict.json`](verdict.json).
