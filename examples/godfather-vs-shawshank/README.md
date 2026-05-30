# Worked example — a full 10-ping debate

A complete, unedited run of the system, captured for reference. It shows
the mediated flow, runtime side assignment, web-cited turns, the
refute-with-citation rule deciding the round, and a no-tie verdict.

## Files in this folder

| File | What it is |
|------|------------|
| [`transcript.md`](transcript.md) | The full turn-by-turn transcript (all 20 turns + verdict) |
| [`verdict.json`](verdict.json) | The machine-readable verdict the judge produced |

## How it was run

```powershell
uv run python -m debate.main --config config/setup.json
```

| Field | Value |
|-------|-------|
| Session id | `57cf02c2` |
| LLM provider | `claude_cli` (Claude via the local CLI, Claude Pro login) |
| Topic | Which is the greater film: The Godfather (1972) or The Shawshank Redemption (1994)? |
| Pings per side | 10 (20 debater turns + 1 verdict = 21 LLM calls) |
| Wall-clock | ~7m45s (22:55:48 → 23:03:34) |
| Winner | **CON — The Godfather**, 84 to 76 |

## Runtime side assignment

The sides are **not** hardcoded; the Parent/Judge assigns them at session
start, seeded by `session_id`. For `57cf02c2` the host announced:

```
PARENT (host): assigning sides - PRO defends 'The Shawshank Redemption',
CON defends 'The Godfather' (session-seeded, not hardcoded).
```

So in this session PRO argued for *Shawshank* and CON argued for *The
Godfather* — the opposite of the config defaults, proving the assignment
is dynamic.

## The clash, ping by ping

Every turn went PRO → Parent → CON → Parent, and each turn carried at
least one real citation (see the transcript for the sources). Condensed:

| Ping | PRO (Shawshank) | CON (The Godfather) |
|------|-----------------|---------------------|
| 1 | Frames greatness as durable mass devotion; IMDb Top 250 #1 for years. | Popularity ≠ greatness; AFI ranks Godfather #2, Shawshank absent. |
| 2 | AFI is a closed US panel; Shawshank is #23 on AFI "100 Years…100 Cheers". | IMDb is an unweighted popularity poll; concedes the Cheers sub-list is minor. |
| 3 | Turns the National Film Registry into an "equalizer" (both inducted). | Expert verdict (AFI, Ebert's Great Movies) inverts the crowd verdict. |
| 4 | AFI 2007 froze out a young film; Ebert inducted Shawshank to his pantheon. | AFI *revised* in 2007 and Godfather rose to #2; age is no excuse. |
| 5 | IMDb is a rolling 20-year worldwide referendum beating one-off juries. | BFI Sight & Sound (critics, once a decade) ranks Godfather, not Shawshank. |
| 6 | Sight & Sound 2022 upended its own canon (Jeanne Dielman #1) — not durable. | PRO swaps arbiters; Godfather is #2 even on PRO's own IMDb yardstick. |
| 7 | Registry credential is shared; concedes nothing; Shawshank sits above on IMDb. | The Academy crowned Godfather (3 Oscars); Shawshank went 0-for-7. |
| **8** | **Alleges CON erred: claims Shawshank is "#72 on AFI 2007".** | **Refutes in the same turn with a cited source: that ranking does not exist.** |
| 9 | Reframes greatness as on-screen experience (hope, friendship). | IMDb measures reach, not merit; Registry induction is shared, not decisive. |
| 10 | Oscars are a poor proxy — Citizen Kane lost too. | Kane *endures via critics* (Sight & Sound), exactly where Godfather lives. |

## The decisive moment (ping 8)

PRO tried to discredit CON's central evidence with a fabricated fact:

> PRO: "In AFI's 100 Years…100 Movies, 10th Anniversary Edition (2007),
> The Shawshank Redemption is ranked #72 by the very 1,500 industry
> leaders he invokes."

CON applied the **refute-with-citation rule** — contradicting a factual
claim *and* citing a source in the same turn:

> CON: "That number does not exist. Shawshank appears on neither the 1998
> nor the 2007 AFI 100 Years…100 Movies list. The 2007 revision added
> films like Toy Story, The Sixth Sense, and Titanic — not Shawshank."

Because PRO advanced an uncited falsehood and CON refuted it with a
source, the allegation rebounded against PRO. The judge called this the
turning point.

## Final verdict

```
FINAL VERDICT: CON wins
PRO score: 76.0
CON score: 84.0
```

**Judge rationale (excerpt):** "CON won the framing war by repeatedly
attacking the warrant behind IMDb's #1 ranking … while stacking
convergent professional-consensus evidence: AFI #2, the 1972 Oscar
sweep, first-class National Film Registry induction, Sight & Sound, and
Ebert's Great Movies essay. … The round turned on ping 8 … CON refuted
this in the same turn with a cited source … Under the
refute-with-citation rule this both rehabilitated CON and penalized PRO
for advancing an uncited falsehood."

**Persuasion notes (excerpt):** "Principle 3 (refute-a-lie-with-citation)
was decisive … Principle 1 (persuasion not truth): judged on defense
quality, not on which film is 'really' greater … Principle 5 invoked
only as confirmation, not needed to break a tie since scores differ."

The full rationale and persuasion notes are in
[`verdict.json`](verdict.json).

## What this example demonstrates

- **Mediated routing** — debaters never address each other; every turn
  is relayed by the Parent.
- **Runtime side assignment** — PRO defended Shawshank here, the reverse
  of the config defaults.
- **Web citations every turn** — IMDb, AFI, the Library of Congress,
  BFI Sight & Sound, Oscars.org, RogerEbert.com.
- **Refute-with-citation rule** — a bare contradiction is not a
  refutation; the cited correction at ping 8 decided the debate.
- **Research-backed, no-tie judging** — distinct scores (84 vs 76) with
  a rationale tied to the five judging principles.
