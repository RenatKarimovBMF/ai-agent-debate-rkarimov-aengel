# ADR-001: Mediated parent-only routing

**Status:** Accepted
**Date:** 2026-05-21

## Context

The exercise forbids direct Pro↔Con communication. Every message
between the two debaters must go through the host/judge. This is the
single most important architectural invariant of the project — almost
every other design choice cascades from it.

## Decision

The Parent process owns all routing. Pro and Con only talk to the
Parent via `ChannelPair`-typed transport channels. There is no
direct peer-to-peer link; the orchestrator does not even create one.

## Consequences

**Positive:**

- Easy to audit: every transcript line records both `from_role` and
  `to_role`, so the grader can verify mediation by reading any log.
- The judge naturally sees the full transcript because it is the
  router.
- A single point to enforce side-assignment, the refute-with-citation
  rule, and the gatekeeper.

**Negative:**

- Higher latency than a peer mesh would have, because every turn
  takes two hops.
- The Parent is a single point of failure; the watchdog must monitor
  it explicitly.

## Alternatives considered

- **Peer-to-peer with a passive observer judge** — rejected; the
  brief explicitly forbids direct Pro↔Con messages.
- **Shared bus with role-filtered subscriptions** — rejected; adds
  infrastructure without changing the auditing story.
