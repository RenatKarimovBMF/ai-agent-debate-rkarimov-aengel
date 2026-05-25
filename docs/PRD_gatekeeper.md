# Mechanism PRD — Gatekeeper

**Component:** `Gatekeeper`  
**Module:** `debate.gatekeeper`  
**Version:** 1.00  
**Authors:** Renat Karimov, Alon Engel  
**Last updated:** 2026-05-21

---

## 1. Summary

The gatekeeper protects the project from **runaway LLM/API usage** during development and grading. It enforces configurable **global** and **per-agent** request limits immediately **before** each LLM call and records successful calls after approval.

Exercise 02 §8.6 and Guidelines V3 require a gatekeeper with config-driven limits. Stage 7 will extend this MVP with a request queue and structured denial logging.

---

## 2. Problem statement

Without budget control:

- A bug in the ping loop could trigger hundreds of API calls.
- Free-tier Gemini quotas exhaust quickly (429 errors).
- Graders cannot verify responsible API usage.

The gatekeeper provides a **fail-fast** guard at the SDK boundary inside each agent.

---

## 3. Scope

### In scope

- Count LLM requests per agent role (`pro`, `con`, `parent`).
- Count total requests across all roles in a session.
- Configurable enable/disable switch.
- Raise `BudgetExceededError` when a limit would be exceeded.
- Expose `total_requests` for logging and tests.

### Out of scope (Stage 7+)

- Token-based billing limits (future enhancement).
- Persistent cross-session counters.
- Distributed rate limiting across machines.

---

## 4. Public API

### `BudgetExceededError`

Subclass of `RuntimeError`. Raised when `check()` would allow a call that exceeds limits.

### `Gatekeeper`

```python
class Gatekeeper:
    def __init__(self, config: GatekeeperConfig) -> None: ...

    def check(self, role: AgentRole) -> None:
        """Raise BudgetExceededError if this call is not allowed."""

    def record(self, role: AgentRole) -> None:
        """Increment counters after a successful LLM call."""

    @property
    def total_requests(self) -> int: ...
```

### Usage pattern (agents)

```python
self._gatekeeper.check(self._role)
response = self._client.prompt(system, user)
self._gatekeeper.record(self._role)
```

**Invariant:** Every successful LLM call must pair exactly one `check` + one `record` for the same role. `check` without `record` is allowed only if the call fails before record.

---

## 5. Configuration

Current source: `config/rate_limits.json` (paired with `config/setup.json`).

Demo runs use `config/demo_rate_limits.json` with `config/demo_setup.json`.

| Field | Type | Default (full config) | Description |
|-------|------|------------------------|-------------|
| `enabled` | bool | `true` | Master switch |
| `max_total_requests` | int | `200` | Cap for entire session |
| `max_requests_per_agent` | int | `80` | Cap per `AgentRole` |

Demo config (`config/demo_setup.json` + `config/demo_rate_limits.json`) uses tighter limits for cheap runs.

### Future (Stage 6–7): `config/rate_limits.json`

```json
{
  "enabled": true,
  "max_total_requests": 200,
  "max_requests_per_agent": 80,
  "min_interval_ms": 0,
  "log_denials": true
}
```

---

## 6. Limit arithmetic

For default debate settings:

- **10 pings/side** → 20 Pro + 20 Con turns = 40 child LLM calls.
- **Parent** calls: opening guidance + verdict (+ optional interim) ≈ 2–5 calls.
- **Expected total:** ~45–50 requests per full session.

Limits of 200 global / 80 per agent provide headroom for retries and development misruns while still bounding disasters.

---

## 7. Behavior specification

### `check(role)` when `enabled=true`

1. If `total_requests >= max_total_requests` → raise `BudgetExceededError("Global request budget exceeded")`.
2. If `per_agent[role] >= max_requests_per_agent` → raise `BudgetExceededError("Budget exceeded for {role}")`.
3. Otherwise return silently.

### `check(role)` when `enabled=false`

No-op; counters may still be updated if `record` is called (implementation choice: current code skips both).

### `record(role)` when `enabled=true`

- Increment `total_requests` by 1.
- Increment `per_agent[role]` by 1.

### Thread / process safety

Each worker process instantiates **its own** `Gatekeeper`. Counters are **not shared** across processes in the MVP.

**Implication:** Global limit is per-process, not cluster-wide. For this assignment, Parent and children maintain separate instances — Stage 7 should document or unify via shared manager if true global cap is required.

**Current design (Stage 7):** Pro, Con, and Parent workers each instantiate their own `Gatekeeper`. Global caps in JSON apply **per process**, not across the whole session. This is documented in the module docstring and is acceptable for the assignment; a shared `multiprocessing.Manager` counter is out of scope.

---

## 8. Integration points

| Caller | When |
|--------|------|
| `ProAgent.invoke_llm` | Before/after Gemini/Claude call |
| `ConAgent.invoke_llm` | Same |
| `ParentAgent.invoke_llm` | Verdict and host messages |
| Tests | Direct unit tests with low limits |

Gatekeeper does **not** wrap transport IPC — only LLM/API calls count.

---

## 9. Logging (current vs planned)

### Current

- Exception propagates to worker → ERROR event → session log.

### Stage 7 (implemented)

- Log structured denial: `{event: "gatekeeper_denied", role, reason, totals}` when `log_denials` is true.
- Thread lock + `min_interval_ms` sleep serializes LLM calls within a process.
- Limits read from `config/rate_limits.json` via `GatekeeperConfig`.

---

## 10. Error handling

| Scenario | Expected outcome |
|----------|------------------|
| Budget exceeded on Pro ping 8 | Pro worker ERROR; session abort; partial logs retained |
| `enabled=false` | Unlimited calls (development only — document in README) |
| Misconfigured limits (0) | Immediate failure on first `check` — valid for testing |

---

## 11. Test requirements

| Test case | File |
|-----------|------|
| Disabled gatekeeper allows unlimited records | `test_gatekeeper.py` |
| Global cap triggers on N+1 | `test_gatekeeper.py` |
| Per-agent cap independent of other roles | `test_gatekeeper.py` |
| `total_requests` property accuracy | `test_gatekeeper.py` |
| Denial logging (Stage 7) | `tests/unit/test_gatekeeper.py` |

---

## 12. Acceptance criteria

- [x] MVP counter-based gatekeeper implemented.
- [x] Config-driven limits from `config/rate_limits.json`.
- [x] Unit tests for check/record/budget error, denials, and interval queue.
- [x] Per-process semantics documented (each worker has its own gatekeeper).
- [x] Request serialization via `min_interval_ms` + thread lock.
- [x] Structured denial logging when `log_denials` is true.
- [x] Limits loaded from `config/rate_limits.json`.

---

## 13. Related documents

- `PRD.md` — FR-19, FR-20
- `PLAN.md` — ADR-005
- `TODO.md` — Stage 7 tasks
