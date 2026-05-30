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
| Session id | `fe14afde` |
| LLM provider | `claude_cli` (Claude via the CLI, Claude Pro login) |
| Topic | Which is the greater film: The Godfather (1972) or The Shawshank Redemption (1994)? |
| Pings per side | 10 (20 debater turns + 1 verdict = 21 LLM calls) |
| Wall-clock | ~7m57s (04:29:56 → 04:37:53) |
| Winner | **CON — The Godfather**, 83 to 78 |

## Runtime side assignment

The sides are **not** hardcoded; the Parent/Judge assigns them at session
start, seeded by `session_id`. For `fe14afde` the host announced:

```
PARENT (host): assigning sides — PRO defends 'The Shawshank Redemption',
CON defends 'The Godfather' (session-seeded, not hardcoded).
```

So in this session PRO argued for *Shawshank* and CON for *The Godfather*.

## What this example demonstrates

- **Mediated routing** — debaters never address each other; every turn is
  relayed by the Parent.
- **Runtime side assignment** — decided by the host, not the config.
- **Cited clash** — IMDb Top 250, AFI 100 Years…100 Movies, the Oscars,
  the National Film Registry, BFI Sight & Sound, all cited in-line.
- **Refute-with-citation rule** — at ping 2, PRO claimed Shawshank ranks
  AFI #72 (a falsehood); CON refuted it with a cited AFI source and PRO
  conceded the point, a net loss for PRO.
- **Research-backed, no-tie verdict** — distinct scores (83 vs 78) tied to
  the five judging principles.

## Verdict (excerpt)

```
FINAL VERDICT: CON wins
PRO score: 78.0
CON score: 83.0
```

> "CON ran the tighter, better-diversified case. PRO built almost
> everything on a single warrant — IMDb's #1 user ranking … CON attacked
> that warrant repeatedly … landing the decisive observation that The
> Godfather sits at #2 on the very same IMDb list … CON's convergence
> frame (AFI #2/#3, two Best Picture wins, Sight & Sound presence,
> genre-redefining influence) gave it multiple independent lines."

The full rationale and persuasion notes are in [`verdict.json`](verdict.json).
