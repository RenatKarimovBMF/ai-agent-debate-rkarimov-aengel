# ADR-002: Multiprocessing with `spawn`

**Status:** Accepted
**Date:** 2026-05-21

## Context

The exercise asks for separate agent processes — not just threads.
Windows is the primary development environment, which means we must
use `multiprocessing.get_context("spawn")` (Windows does not support
`fork`).

## Decision

`ProcessDebateOrchestrator` boots three persistent workers per
session — Parent, Pro, Con — under a `spawn` context. The supervisor
process exchanges `START`, `ASSIGN`, `TURN_REQUEST`, `RELAY`, and
`STOP` commands over `multiprocessing.Queue`s. All config objects
passed between processes are pickle-safe dataclasses.

## Consequences

**Positive:**

- True process isolation; an OOM or hang in one agent cannot corrupt
  the others.
- Works identically on Linux/macOS without extra branches.
- Maps cleanly to the IPC table in `docs/PLAN.md` §6.

**Negative:**

- Higher startup cost than `fork` would have.
- All shared state must be pickle-safe; we cannot share an open file
  handle directly. The transport layer (`debate/transport/`)
  abstracts this away.

## Alternatives considered

- **Threads only** — rejected; the brief asks for real OS-level
  separation between agents.
- **`fork`-only multiprocessing** — rejected; would not run on
  Windows, which is the primary dev environment.
- **One persistent worker reused across sessions** — rejected;
  adds session-bleed risk for very little startup-time payoff.
