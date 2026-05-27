# ADR-005: Gatekeeper as pre-call budget check

**Status:** Accepted
**Date:** 2026-05-21

## Context

Exercise §8.6 and the submission guidelines both require rate
limiting / cost control. Students develop on free-tier Gemini, which
caps requests per minute and per day.

## Decision

`debate.gatekeeper.Gatekeeper` is consulted synchronously before
every LLM call. It enforces:

- A global cap (`max_total_requests`).
- A per-agent cap (`max_requests_per_agent`).
- A minimum interval between requests (`min_interval_ms`) via an
  internal serialisation queue.
- A denial log (`gatekeeper/denial_log.py`) so refusals are
  observable in the rotating logs.

## Consequences

**Positive:**

- One choke point for budget enforcement; no agent can bypass it
  because the SDK isn't called directly from agents.
- Easy to demo the cost story: change `rate_limits.json`, re-run,
  see the denial log.
- The denial log is JSONL, so it joins the existing rotating-log
  pipeline without ceremony.

**Negative:**

- Synchronous queue serialises all LLM calls across all agents,
  which is fine for the exercise but not for high-throughput
  production use.
- Not a full token-bucket: tokens-per-minute aren't tracked yet;
  we count requests.

## Alternatives considered

- **Token-bucket with leaky-bucket replenishment** — rejected for
  scope; the request count is the binding constraint on the free
  tier we develop against.
- **Per-provider quotas instead of per-agent** — partially included
  (the limit applies per `Gatekeeper` instance, one per worker
  process). Per-provider quotas would need provider-aware accounting
  in the SDK layer.
