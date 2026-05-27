# Architectural Decision Records

Per Guidelines V3 §2.2, every meaningful architectural decision is
captured here as a short, dated record using the
[Michael Nygard template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
Each record states the **context** (what problem are we addressing),
the **decision** we took, the **consequences** that follow, and the
**alternatives considered** with the reason each one was rejected.

The same records also live inside `docs/PLAN.md` for readers who want
the whole plan in one place; the per-file split here is the canonical
form and is what we update first.

## Index

| ID | Title | Status |
| ---: | --- | --- |
| [001](0001-mediated-parent-only-routing.md) | Mediated parent-only routing | Accepted |
| [002](0002-multiprocessing-with-spawn.md) | Multiprocessing with `spawn` | Accepted |
| [003](0003-sdk-facade-for-llm-providers.md) | SDK facade for all LLM providers | Accepted |
| [004](0004-config-externalization-json.md) | Configuration externalisation (JSON in `config/`) | Accepted |
| [005](0005-gatekeeper-pre-call-budget-check.md) | Gatekeeper as pre-call budget check | Accepted |
| [006](0006-150-line-cap-per-source-file.md) | 150-line cap per source file | Accepted |
| [007](0007-runtime-side-assignment.md) | Runtime side assignment by the host | Accepted |
| [008](0008-multi-skill-debaters.md) | Multi-skill debaters + lore-only side skills | Accepted |
| [009](0009-research-backed-judging-rubric.md) | Research-backed judging rubric | Accepted |
| [010](0010-config-version-validated-at-load.md) | Config version key validated at load | Accepted |

## When to add a new ADR

Add one whenever you make a decision that:

- Has more than one defensible answer.
- Will be hard or expensive to reverse later.
- A new contributor would otherwise have to dig out from `git log`.

Smaller decisions belong in `docs/PLAN.md`'s ADR section; standalone
files are reserved for the load-bearing ones.
