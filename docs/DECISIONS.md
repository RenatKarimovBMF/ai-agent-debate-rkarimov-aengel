# Decision Journal

> A lightweight, chronological log of notable engineering decisions and
> "what's next", kept **separate** from the PRD/PLAN (the formal specs) and
> from the system prompt. It is a continuity aid between work sessions — not
> a requirement — as suggested in the Exercise 02 brief. Architectural
> decisions with lasting weight are also captured as ADRs in
> [`PLAN.md`](PLAN.md); this file is the running narrative around them.

Format: newest entry first. Each entry lists **Decided** (what we settled)
and **Next** (the open follow-ups at that point in time).

---

## 2026-05-30 (PM) — web search, judge intervention, research layer

**Decided**

- **Web search on every provider.** Added `llm.anthropic_web_search` so the
  Anthropic API path attaches the GA `web_search_20250305` tool; Gemini
  grounding and the Claude CLI's WebSearch were already active. Code-level
  defaults stay `False` (safe, explicit opt-in); the config files set it
  `true`. See ADR-011.
- **Judge mid-debate intervention.** Implemented as a *deterministic*
  capitulation check (`orchestrator/intervention.py`) plus a single ringside
  re-ask, rather than an LLM-based critic, to keep it token-free and
  unit-testable. Minor concessions are allowed. See ADR-012.
- **Research layer (§9).** Kept the notebook thin by putting all parsing in a
  tested `debate.analysis` module; notebook only loads + plots to `results/`.
- **ISO/IEC 25010 mapping** added to PLAN §13.
- **Crash-recovery resume: declined (won't-do).** The Watchdog already
  provides keep-alive + automatic restart of dead workers *during* a session
  (Exercise §8.6), so the system recovers mid-run today. A separate
  "reload a partial session from disk and continue" feature would duplicate
  that resilience for marginal benefit and add real complexity (per-ping
  state persistence, child re-seeding). Documented as KNOWN_LIMITATIONS L-11
  and ADR-013.

**Next**

- **(must-fix)** Screenshots + poster images; fix the broken README image
  links (`assets/posters/*.jpg`, `assets/screenshots/*.png`). GUI screenshot
  to be added by the author.
- Optional: expand examples with more runs to strengthen the §9 statistics.

---

## 2026-05-30 (AM) — validation baseline

**Decided**

- Confirmed the submission baseline is green: 270 tests, 100% coverage, Ruff
  + mypy clean, every file ≤150 lines, CLI `--dry-run` wired correctly.

**Next**

- Tackle web search, judge intervention, and the research notebook (done same
  day — see the PM entry).
