# ADR-007: Runtime side assignment by the host

**Status:** Accepted
**Date:** 2026-05-27

## Context

In-class clarification: the debater's position must not be fixed in
code. The host should hand it over in real time, so the Parent
visibly runs the debate rather than being a passive scorer.

## Decision

`ProAgent` and `ConAgent` are pure role markers with no built-in side
knowledge. `debate.orchestrator.host_protocol.decide_sides(config,
session_id)` chooses which class defends `config.debate.pro_side` and
which defends `config.debate.con_side`. The choice is deterministic
per `session_id` (replayable from logs) but varies across sessions.

The result travels to children in an `ASSIGN` command before any
turn request:

```
{"type": "ASSIGN", "own_side": "...", "opponent_side": "..."}
```

The Parent records the same mapping and uses it in its system prompt
and verdict prompt.

## Consequences

**Positive:**

- The Parent visibly assigns sides in the boxing-referee opening
  briefing (`debate-host-protocol` skill).
- Tests can no longer assume "PRO = Godfather"; the new
  `tests/unit/test_host_protocol.py` covers determinism,
  variability, and override paths.
- Side strings are decoupled from agent class names, so adding a new
  side label is a config-only change.

**Negative:**

- The IPC protocol grows one more command type.
- Determinism is per `session_id`; reproducing a specific assignment
  requires capturing the session id.

## Alternatives considered

- **Hardcode sides on the agent class** — what we used to do;
  rejected because it contradicted the brief.
- **Random assignment without a seed** — rejected; we wanted runs
  to be reproducible from the JSONL transcript.
- **Send sides inside the first `TURN_REQUEST`** — rejected; the
  host opening briefing is a separate ceremony, and conflating it
  with the first turn would make the boxing-referee analogy weaker.
