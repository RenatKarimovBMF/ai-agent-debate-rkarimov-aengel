# Worked examples

Complete, unedited debate sessions captured from real runs on the
`claude_cli` provider. Each folder has a write-up (`README.md`), the
full turn-by-turn transcript (`transcript.md`), and the machine-readable
verdict the judge produced (`verdict.json`).

| Debate | Provider | Pings | Result | Folder |
|--------|----------|-------|--------|--------|
| The Godfather vs The Shawshank Redemption (default topic) | `claude_cli` | 10 | CON (The Godfather) wins 83–78 | [godfather-vs-shawshank/](godfather-vs-shawshank/) |
| Should abortion be legal and accessible? (custom `--topic`) | `claude_cli` | 10 | PRO (Supporting) wins 84–80 | [abortion-legality/](abortion-legality/) |

The second example was run with `--topic`/`--pro`/`--con` overrides to
demonstrate that the engine is **topic-agnostic** — the same orchestrator,
skills, and judging rubric handle an arbitrary real-world motion, not just
the default film debate.

Both show the same mechanics: mediated routing (every turn relayed by the
Parent), runtime side assignment, a cited source on every turn, the
refute-with-citation rule, and a research-backed no-tie verdict.
