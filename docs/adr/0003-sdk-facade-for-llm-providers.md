# ADR-003: SDK facade for all LLM providers

**Status:** Accepted
**Date:** 2026-05-21

## Context

Guidelines V3 requires an explicit SDK layer that hides the concrete
LLM provider from business logic. We also want to fall back gracefully
between providers because students develop on free-tier Gemini.

## Decision

`sdk.llm_client.LlmClient` is the single entry point for every LLM
call. It chooses between Gemini → Anthropic API → Claude CLI in that
order based on which credentials are available, and exposes a single
`prompt(system, user)` method that returns a normalised
`LlmResponse`. Agents never import `google.genai` or `anthropic`
directly.

## Consequences

**Positive:**

- One mock point in tests (`tests/unit/test_sdk_clients.py`).
- New providers can be added by writing a new client and wiring it
  into the priority order; agents don't change.
- The active provider is observable (`--dry-run` prints it; the GUI
  shows it; logs include it).

**Negative:**

- The facade is thin — almost a passthrough — and adds one extra
  indirection. Worth it for the test ergonomics.

## Alternatives considered

- **One provider, hardcoded** — rejected; the brief calls out the
  free-tier Gemini path explicitly, and we wanted Claude as a
  fallback.
- **A LangChain-style provider abstraction** — rejected; too much
  surface for what the exercise needs, and a heavyweight dependency.
